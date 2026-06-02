# module_rag/service/knowledge_base_service.py
"""知识库管理服务"""
from sqlalchemy.ext.asyncio import AsyncSession
from module_rag.dao.knowledge_base_dao import KnowledgeBaseDao
from module_rag.entity.do.knowledge_base_do import RagKnowledgeBase
from module_rag.entity.vo.knowledge_base_vo import KnowledgeBaseCreateModel, KnowledgeBaseUpdateModel


class KnowledgeBaseService:

    @classmethod
    async def create(cls, db: AsyncSession, data: KnowledgeBaseCreateModel, user_id: int) -> RagKnowledgeBase:
        kb = RagKnowledgeBase(
            kb_name=data.kb_name,
            kb_desc=data.kb_desc,
            embedding_model=data.embedding_model,
            chunk_size=data.chunk_size,
            chunk_overlap=data.chunk_overlap,
            user_id=user_id,
        )
        return await KnowledgeBaseDao.create(db, kb)

    @classmethod
    async def get_list(cls, db: AsyncSession) -> list[RagKnowledgeBase]:
        return await KnowledgeBaseDao.get_list(db)

    @classmethod
    async def get_by_id(cls, db: AsyncSession, kb_id: int) -> RagKnowledgeBase | None:
        return await KnowledgeBaseDao.get_by_id(db, kb_id)

    @classmethod
    async def update(cls, db: AsyncSession, data: KnowledgeBaseUpdateModel):
        update_data = {k: v for k, v in data.model_dump().items() if v is not None and k != 'kb_id'}
        await KnowledgeBaseDao.update_by_id(db, data.kb_id, **update_data)

    @classmethod
    async def delete(cls, db: AsyncSession, kb_id: int):
        await KnowledgeBaseDao.delete_by_id(db, kb_id)