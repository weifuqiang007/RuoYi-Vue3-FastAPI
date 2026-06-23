# module_rag/service/chunk_service.py
"""分块管理服务 —— 查看与修改分块内容

修改分块内容时必须重新向量化，否则检索会命中旧向量。
"""
from sqlalchemy.ext.asyncio import AsyncSession
from exceptions.exception import ServiceException
from module_rag.dao.chunk_dao import ChunkDao
from module_rag.entity.do.chunk_do import RagChunk
from module_rag.entity.vo.chunk_vo import ChunkUpdateModel
from module_rag.service.embedding_service import EmbeddingService
from utils.log_util import logger


class ChunkService:

    @classmethod
    async def get_page_by_doc(
        cls, db: AsyncSession, doc_id: int, page_num: int = 1, page_size: int = 20
    ) -> tuple[int, list[RagChunk]]:
        """分页获取某文档的分块（DAO 层已排除 embedding 列，避免大文档超时）"""
        return await ChunkDao.get_page_by_doc_id(db, doc_id, page_num, page_size)

    @classmethod
    async def update_chunk(cls, db: AsyncSession, data: ChunkUpdateModel) -> RagChunk:
        """
        修改分块内容并重新向量化。

        :raises ServiceException: 分块不存在
        """
        chunk = await ChunkDao.get_by_id(db, data.chunk_id)
        if not chunk:
            raise ServiceException(message='分块不存在')

        # 内容无变化则直接返回，避免无谓的向量化调用
        if chunk.content == data.content:
            return chunk

        # 重新向量化（保证检索命中新内容）
        try:
            embedding = await EmbeddingService.embed_single(data.content)
        except Exception as e:
            logger.error(f"分块 {data.chunk_id} 重新向量化失败: {e}")
            raise ServiceException(message='内容更新失败：向量化服务异常，请稍后重试')

        # token_count 与入库时保持一致（取字符数作为回退口径）
        await ChunkDao.update_content(
            db,
            chunk_id=data.chunk_id,
            content=data.content,
            token_count=len(data.content),
            embedding=embedding,
        )
        chunk.content = data.content
        chunk.token_count = len(data.content)
        return chunk
