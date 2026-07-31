# module_rag/service/document_service.py
"""文档处理 Pipeline
参考 ragflow/rag/svr/task_executor.py 的 TaskManager 状态机设计
上传 → 解析 → 分块 → 向量化 → 完成
"""
import os
import tempfile
import uuid

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from exceptions.exception import ServiceException
from module_rag.dao.document_dao import DocumentDao
from module_rag.dao.chunk_dao import ChunkDao
from module_rag.dao.knowledge_base_dao import KnowledgeBaseDao
from module_rag.entity.do.document_do import RagDocument
from module_rag.service.parser import get_parser
from module_rag.service.chunker.fixed_chunker import FixedChunker
from module_rag.service.embedding_service import EmbeddingService
from module_rag.utils.text_cleaner import clean_block_text, content_fingerprint, is_valid_chunk
from config.get_minio import MinioUtil
from utils.log_util import logger


class DocumentService:
    """文档业务服务 —— MinIO 调用与 DB 操作全部收口在此，controller 只做参数接收与响应封装"""

    @classmethod
    async def upload_document(cls, db: AsyncSession, kb_id: int, file: UploadFile, user_id: int) -> RagDocument:
        """
        上传文档 → 保存到 MinIO → 创建数据库记录 + 知识库 doc_count+1 → 触发解析Pipeline

        一致性策略：
        - MinIO 上传失败 → 抛 ServiceException（前端友好提示），无 DB 脏数据。
        - MinIO 上传成功但 DB 写入失败 → 补偿删除 MinIO 文件，避免孤儿，再抛 ServiceException。
        - 解析/向量化失败 → 不回滚，保留记录并标记状态（embed_status='9'），上传接口仍返回成功。
        """
        content = await file.read()
        file_type = os.path.splitext(file.filename)[1].lower()

        # 对象路径: rag/{kb_id}/{uuid}.{ext}
        object_name = f"rag/{kb_id}/{uuid.uuid4().hex}{file_type}"

        minio = MinioUtil.get_instance()

        # ===== 入库前：上传 MinIO =====
        try:
            minio.put(object_name, content)
        except Exception as e:
            logger.error(f"MinIO 上传失败 kb_id={kb_id} filename={file.filename}: {e}")
            raise ServiceException(message="文件存储失败，请稍后重试")

        # ===== 入库（同一事务）：建记录 + doc_count+1 =====
        doc = RagDocument(
            kb_id=kb_id,
            doc_name=file.filename,
            file_path=object_name,
            file_type=file_type,
            file_size=len(content),
            user_id=user_id,
        )
        try:
            doc = await DocumentDao.create(db, doc)
            await KnowledgeBaseDao.increment_doc_count(db, kb_id, 1)
        except Exception as e:
            # 补偿：删除已上传的 MinIO 文件，避免孤儿
            logger.error(f"文档记录保存失败，回滚 MinIO 文件 {object_name}: {e}")
            minio.remove(object_name)
            raise ServiceException(message="文档保存失败，请稍后重试")

        # ===== 处理（尽力而为，失败不抛出，仅记录状态）=====
        await cls.process_document(db, doc.doc_id)

        return doc

    @classmethod
    async def get_doc_list(cls, db: AsyncSession, kb_id: int | None = None) -> list[RagDocument]:
        """获取文档列表，kb_id=None 返回全部，否则返回指定知识库下的文档"""
        if kb_id is not None:
            return await DocumentDao.get_by_kb_id(db, kb_id)
        return await DocumentDao.get_all(db)

    @classmethod
    async def get_file(cls, db: AsyncSession, doc_id: int) -> tuple[RagDocument, bytes] | None:
        """供下载使用：返回 (doc, file_bytes)，文档不存在或文件损坏返回 None"""
        doc = await DocumentDao.get_by_id(db, doc_id)
        if not doc:
            return None
        data = MinioUtil.get_instance().get(doc.file_path)
        if data is None:
            return None
        return doc, data

    @classmethod
    async def get_presigned_url(cls, db: AsyncSession, doc_id: int) -> tuple[str, RagDocument] | None:
        """供预览使用：返回 (url, doc)，文档不存在或取地址失败返回 None"""
        doc = await DocumentDao.get_by_id(db, doc_id)
        if not doc:
            return None
        url = MinioUtil.get_instance().get_presigned_url(doc.file_path)
        if url is None:
            return None
        return url, doc

    @classmethod
    async def delete_documents(cls, db: AsyncSession, doc_ids: list[int]) -> None:
        """删除文档（MinIO 文件 + 逻辑删除记录 + 知识库 doc_count-1）"""
        minio = MinioUtil.get_instance()
        for doc_id in doc_ids:
            doc = await DocumentDao.get_by_id(db, doc_id)
            if not doc:
                continue
            # 删除 MinIO 文件
            minio.remove(doc.file_path)
            # 逻辑删除数据库记录
            await DocumentDao.update_status(db, doc_id, del_flag='2')
            # 同步失效分块，避免已删除文档继续参与检索
            await ChunkDao.delete_by_doc_id(db, doc_id)
            # 知识库文档数 -1
            await KnowledgeBaseDao.increment_doc_count(db, doc.kb_id, -1)

    @classmethod
    async def process_document(cls, db: AsyncSession, doc_id: int):
        """
        文档处理主流程
        状态机设计参考 ragflow/rag/svr/task_executor.py 的 do_handle_task

        状态流转：
        parse_status: 0(待处理) → 1(解析中) → 2(完成) / 9(失败)
        embed_status: 0(待处理) → 1(向量化中) → 2(完成) / 9(失败)

        失败处理：记录状态后正常返回（不抛出），调用方据状态字段判断是否需重试。
        文件存储在 MinIO，解析时先下载到临时文件。
        """
        doc = await DocumentDao.get_by_id(db, doc_id)
        if not doc:
            raise ValueError(f"文档不存在: {doc_id}")

        temp_file_path = None
        try:
            # ===== Step 0: 从 MinIO 下载文件到临时目录 =====
            minio = MinioUtil.get_instance()
            file_data = minio.get(doc.file_path)
            if file_data is None:
                raise RuntimeError(f"MinIO 文件不存在: {doc.file_path}")

            # 写入临时文件（解析器需要文件路径）
            suffix = doc.file_type if doc.file_type.startswith('.') else f'.{doc.file_type}'
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(file_data)
                temp_file_path = tmp.name

            logger.info(f"文档 {doc_id}: 从 MinIO 下载到临时文件 {temp_file_path}")

            # ===== 清理旧分块（重试场景保证幂等，避免重复分块累积）=====
            await ChunkDao.delete_by_doc_id(db, doc_id)

            # ===== Step 1: 解析文档 =====
            await DocumentDao.update_status(db, doc_id, parse_status="1")
            parser = get_parser(doc.file_type)
            blocks = cls._enrich_heading_paths(parser.parse(temp_file_path))

            # ===== Step 2: 文本分块 =====
            kb = await KnowledgeBaseDao.get_by_id(db, doc.kb_id)
            chunker = FixedChunker(
                chunk_size=kb.chunk_size if kb else 500,
                overlap=kb.chunk_overlap if kb else 50,
            )
            all_chunks = []
            seen_fingerprints: set[str] = set()
            for block in blocks:
                block_text = clean_block_text(block["text"])
                if block.get("type") == "title" or not block_text:
                    continue
                heading_path = block.get("heading_path") or []
                retrieval_text = cls._with_heading_context(block_text, heading_path)
                chunks = chunker.chunk(
                    text=retrieval_text,
                    metadata={
                        "doc_id": doc.doc_id,
                        "doc_name": doc.doc_name,
                        "file_type": doc.file_type,
                        "page": block.get("page"),
                        "heading_path": heading_path,
                        "block_type": block.get("type", "text"),
                    },
                )
                for chunk in chunks:
                    if not is_valid_chunk(chunk["content"]):
                        continue
                    fingerprint = content_fingerprint(chunk["content"])
                    if fingerprint in seen_fingerprints:
                        continue
                    seen_fingerprints.add(fingerprint)
                    all_chunks.append(chunk)

            if not all_chunks:
                raise ValueError("文档解析后没有可用文本分块")

            # ===== Step 3: 保存分块记录 =====
            await DocumentDao.update_status(db, doc_id, parse_status="2", embed_status="1")
            chunk_ids = await ChunkDao.bulk_insert(db, doc_id, doc.kb_id, all_chunks)

            # ===== Step 4: 批量向量化 =====
            texts = [c["content"] for c in all_chunks]
            embeddings = await EmbeddingService.embed_texts(texts)

            # ===== Step 5: 更新向量 =====
            await ChunkDao.bulk_update_embeddings(db, chunk_ids, embeddings)
            await DocumentDao.update_status(
                db, doc_id,
                embed_status="2",
                chunk_count=len(all_chunks)
            )

            logger.info(f"文档 {doc_id}: 处理完成，共 {len(all_chunks)} 个分块")

        except Exception as e:
            logger.error(f"文档 {doc_id}: 处理失败 - {e}")
            # 失败状态落库后正常返回，不抛出 —— 保留文档记录供用户重试
            await DocumentDao.update_status(
                db, doc_id,
                parse_status="9",
                embed_status="9",
                error_msg=str(e)[:500]
            )
        finally:
            # 清理临时文件
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                logger.info(f"文档 {doc_id}: 清理临时文件 {temp_file_path}")

    @staticmethod
    def _enrich_heading_paths(blocks: list[dict]) -> list[dict]:
        """为不原生提供章节路径的解析器补齐 heading_path。"""
        heading_stack: list[tuple[int, str]] = []
        enriched: list[dict] = []
        for raw_block in blocks:
            block = dict(raw_block)
            if block.get("type") == "title":
                level = int(block.get("heading_level") or 1)
                while heading_stack and heading_stack[-1][0] >= level:
                    heading_stack.pop()
                title = clean_block_text(block.get("text") or "")
                if title:
                    heading_stack.append((level, title))
                block.setdefault("heading_path", [item[1] for item in heading_stack])
            else:
                block.setdefault("heading_path", [item[1] for item in heading_stack])
            enriched.append(block)
        return enriched

    @staticmethod
    def _with_heading_context(content: str, heading_path: list[str]) -> str:
        """将章节面包屑加入向量化文本，提升孤立段落的语义完整度。"""
        heading = " > ".join(item.strip() for item in heading_path if item and item.strip())
        return f"{heading}\n{content}" if heading else content
