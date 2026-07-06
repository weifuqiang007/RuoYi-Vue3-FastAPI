# module_rag/dao/knowledge_base_dao.py
from sqlalchemy import ColumnElement, select, update, delete
from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession
from module_rag.entity.do.knowledge_base_do import RagKnowledgeBase


class KnowledgeBaseDao:

    @classmethod
    async def get_by_id(cls, db: AsyncSession, kb_id: int) -> RagKnowledgeBase | None:
        result = await db.execute(select(RagKnowledgeBase).where(RagKnowledgeBase.kb_id == kb_id,
                                                                 RagKnowledgeBase.del_flag == '0'))
        return result.scalars().first()

    @classmethod
    async def get_by_ids(cls, db: AsyncSession, kb_ids: list[int]) -> list[RagKnowledgeBase]:
        """按 id 批量取未删除的知识库（检索鉴权前置取数用）。"""
        if not kb_ids:
            return []
        result = await db.execute(
            select(RagKnowledgeBase).where(
                RagKnowledgeBase.kb_id.in_(kb_ids),
                RagKnowledgeBase.del_flag == '0',
            )
        )
        return list(result.scalars().all())

    @classmethod
    async def get_list(cls, db: AsyncSession) -> list[RagKnowledgeBase]:
        result = await db.execute(
            select(RagKnowledgeBase).where(RagKnowledgeBase.del_flag == '0').order_by(RagKnowledgeBase.create_time.desc())
        )
        """
        把 Result 转换成 可迭代的 ORM 对象序列。
        相当于：只取查询结果里的 “实体行”，不要元组。
        """
        return list(result.scalars().all())

    @classmethod
    async def get_visible_list(cls, db: AsyncSession, cond: ColumnElement) -> list[RagKnowledgeBase]:
        """按可见性条件 cond 过滤的知识库列表（cond 由 ScopePolicy.visible_filter 生成）。"""
        result = await db.execute(
            select(RagKnowledgeBase)
            .where(RagKnowledgeBase.del_flag == '0', cond)
            .order_by(RagKnowledgeBase.create_time.desc())
        )
        return list(result.scalars().all())


    @classmethod
    async def create(cls, db:AsyncSession, kb: RagKnowledgeBase) -> RagKnowledgeBase:
        db.add(kb)
        await db.flush()
        return kb


    @classmethod
    async def update_by_id(cls, db: AsyncSession, kb_id: int, **kwargs):
        await db.execute(
            update(RagKnowledgeBase).where(RagKnowledgeBase.kb_id == kb_id).values(**kwargs)
        )

    @classmethod
    async def increment_doc_count(cls, db: AsyncSession, kb_id: int, delta: int = 1):
        """原子地增减知识库文档数量（用 SQL 表达式自增，避免读-改-写并发问题）"""
        await db.execute(
            update(RagKnowledgeBase)
            .where(RagKnowledgeBase.kb_id == kb_id)
            .values(doc_count=RagKnowledgeBase.doc_count + delta)
        )


    @classmethod
    async def delete_by_id(cls, db:AsyncSession, kb_id: int):
        await db.execute(
            update(RagKnowledgeBase).where(RagKnowledgeBase.kb_id == kb_id).values(del_flag='2')
        )

    
