# module_rag/dao/knowledge_base_dao.py
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession
from module_rag.entity.do.knowledge_base_do import RagKnowledgeBase


class KnowledgeBaseDao:

    @classmethod
    async def get_by_id(cls, db: AsyncSession, kb_id: int) -> RagKnowledgeBase | None:
        result = await db.execute(select(RagKnowledgeBase).where(RagKnowledgeBase.kb_id == kb_id,
                                                                 RagKnowledgeBase.del_flag == '0'))
        return result.scalars().first()
