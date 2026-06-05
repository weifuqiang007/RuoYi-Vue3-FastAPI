from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module_learning.entity.do.research_do import EduResearchData, EduResearchChapter


class ResearchDao:

    @classmethod
    async def create(cls, db: AsyncSession, research: EduResearchData) -> EduResearchData:
        db.add(research)
        await db.flush()
        return research

    @classmethod
    async def get_by_id(cls, db: AsyncSession, research_id: int) -> EduResearchData | None:
        result = await db.execute(
            select(EduResearchData).where(EduResearchData.research_id == research_id)
        )
        return result.scalars().first()

    @classmethod
    async def get_by_record_id(cls, db: AsyncSession, record_id: int) -> EduResearchData | None:
        result = await db.execute(
            select(EduResearchData).where(EduResearchData.record_id == record_id)
        )
        return result.scalars().first()

    @classmethod
    async def update(cls, db: AsyncSession, research: EduResearchData) -> EduResearchData:
        await db.flush()
        return research

    @classmethod
    async def get_chapters(cls, db: AsyncSession, research_id: int) -> list:
        result = await db.execute(
            select(EduResearchChapter)
            .where(EduResearchChapter.research_id == research_id)
            .order_by(EduResearchChapter.chapter_index)
        )
        return list(result.scalars().all())

    @classmethod
    async def get_chapter_by_index(cls, db: AsyncSession, research_id: int, chapter_index: int) -> EduResearchChapter | None:
        result = await db.execute(
            select(EduResearchChapter).where(
                EduResearchChapter.research_id == research_id,
                EduResearchChapter.chapter_index == chapter_index,
            )
        )
        return result.scalars().first()

    @classmethod
    async def create_chapter(cls, db: AsyncSession, chapter: EduResearchChapter) -> EduResearchChapter:
        db.add(chapter)
        await db.flush()
        return chapter

    @classmethod
    async def update_chapter(cls, db: AsyncSession, chapter: EduResearchChapter) -> EduResearchChapter:
        await db.flush()
        return chapter
