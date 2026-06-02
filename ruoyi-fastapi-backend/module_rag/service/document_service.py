# module_rag/service/document_service.py
"""文档处理 Pipeline
参考 ragflow/rag/svr/task_executor.py 的 TaskManager 状态机设计
上传 → 解析 → 分块 → 向量化 → 完成
"""
import os
import tempfile
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from module_rag.dao.document_dao import DocumentDao
from module_rag.dao.chunk_dao import ChunkDao
from module_rag.dao.knowledge_base_dao import KnowledgeBaseDao
from module_rag.service.parser import get_parser
from module_rag.service.chunker.fixed_chunker import FixedChunker
from module_rag.service.embedding_service import EmbeddingService
from module_rag.utils.minio_client import MinioClient

logger = logging.getLogger(__name__)


class DocumentService:

    @classmethod
    async def process_document(cls, db: AsyncSession, doc_id: int):
        """
        文档处理主流程
        状态机设计参考 ragflow/rag/svr/task_executor.py 的 do_handle_task

        状态流转：
        parse_status: 0(待处理) → 1(解析中) → 2(完成) / 9(失败)
        embed_status: 0(待处理) → 1(向量化中) → 2(完成) / 9(失败)

        文件存储在 MinIO，解析时先下载到临时文件
        """
        doc = await DocumentDao.get_by_id(db, doc_id)
        if not doc:
            raise ValueError(f"文档不存在: {doc_id}")

        temp_file_path = None
        try:
            # ===== Step 0: 从 MinIO 下载文件到临时目录 =====
            minio = MinioClient.get_instance()
            file_data = minio.get(doc.file_path)
            if file_data is None:
                raise RuntimeError(f"MinIO 文件不存在: {doc.file_path}")

            # 写入临时文件（解析器需要文件路径）
            suffix = doc.file_type if doc.file_type.startswith('.') else f'.{doc.file_type}'
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(file_data)
                temp_file_path = tmp.name

            logger.info(f"文档 {doc_id}: 从 MinIO 下载到临时文件 {temp_file_path}")

            # ===== Step 1: 解析文档 =====
            await DocumentDao.update_status(db, doc_id, parse_status="1")
            parser = get_parser(doc.file_type)
            blocks = parser.parse(temp_file_path)

            # ===== Step 2: 文本分块 =====
            kb = await KnowledgeBaseDao.get_by_id(db, doc.kb_id)
            chunker = FixedChunker(
                chunk_size=kb.chunk_size if kb else 500,
                overlap=kb.chunk_overlap if kb else 50,
            )
            all_chunks = []
            for block in blocks:
                chunks = chunker.chunk(
                    text=block["text"],
                    metadata={"page": block.get("page"), "type": block.get("type")}
                )
                all_chunks.extend(chunks)

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
            await DocumentDao.update_status(
                db, doc_id,
                embed_status="9",
                error_msg=str(e)[:500]
            )
            raise
        finally:
            # 清理临时文件
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                logger.info(f"文档 {doc_id}: 清理临时文件 {temp_file_path}")
