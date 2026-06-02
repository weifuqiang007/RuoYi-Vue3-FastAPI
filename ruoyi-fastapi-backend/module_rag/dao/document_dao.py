# module_rag/dao/document_dao.py
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from module_rag.entity.do.document_do import RagDocument


class DocumentDao:

    @classmethod
    async def get_by_id(cls, db: AsyncSession, doc_id: int) -> RagDocument | None:
        result =  await db.execute(
            select(RagDocument).where(RagDocument.doc_id == doc_id, RagDocument.del_flag == '0')
        )
        return result.scalars().first()


    @classmethod
    async def get_by_kb_id(cls, db: AsyncSession, kb_id: int) -> list[RagDocument]:
        result = await db.execute(
            select(RagDocument).where(RagDocument.kb_id == kb_id, RagDocument.del_flag == '0')
        )
        return list(result.scalars().all())

    @classmethod
    async def create(cls, db: AsyncSession, doc: RagDocument) -> RagDocument:
        db.add(doc)
        await db.flush()
        return doc

    @classmethod
    async def update_status(cls, db: AsyncSession, doc_id: int, **kwargs):
        await db.execute(
            update(RagDocument).where(RagDocument.doc_id == doc_id).values(**kwargs)
        )