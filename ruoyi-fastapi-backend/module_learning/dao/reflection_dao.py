from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module_learning.entity.do.reflection_do import EduReflectionData, EduReflectionDialogue, EduReflectionDepthHistory


class ReflectionDao:

    @classmethod
    async def create(cls, db: AsyncSession, reflection: EduReflectionData) -> EduReflectionData:
        db.add(reflection)
        await db.flush()
        return reflection

    @classmethod
    async def get_by_id(cls, db: AsyncSession, reflection_id: int) -> EduReflectionData | None:
        result = await db.execute(
            select(EduReflectionData).where(EduReflectionData.reflection_id == reflection_id)
        )
        return result.scalars().first()

    @classmethod
    async def get_by_record_id(cls, db: AsyncSession, record_id: int) -> EduReflectionData | None:
        result = await db.execute(
            select(EduReflectionData).where(EduReflectionData.record_id == record_id)
        )
        return result.scalars().first()

    @classmethod
    async def update(cls, db: AsyncSession, reflection: EduReflectionData) -> EduReflectionData:
        await db.flush()
        return reflection

    @classmethod
    async def add_dialogue(cls, db: AsyncSession, dialogue: EduReflectionDialogue) -> EduReflectionDialogue:
        db.add(dialogue)
        await db.flush()
        return dialogue

    @classmethod
    async def get_dialogues(cls, db: AsyncSession, reflection_id: int) -> list:
        result = await db.execute(
            select(EduReflectionDialogue)
            .where(EduReflectionDialogue.reflection_id == reflection_id)
            .order_by(EduReflectionDialogue.create_time)
        )
        return list(result.scalars().all())

    @classmethod
    async def add_depth_history(cls, db: AsyncSession, history: EduReflectionDepthHistory) -> EduReflectionDepthHistory:
        db.add(history)
        await db.flush()
        return history

    @classmethod
    async def get_depth_history(cls, db: AsyncSession, reflection_id: int) -> list:
        result = await db.execute(
            select(EduReflectionDepthHistory)
            .where(EduReflectionDepthHistory.reflection_id == reflection_id)
            .order_by(EduReflectionDepthHistory.create_time)
        )
        return list(result.scalars().all())

    @classmethod
    async def get_latest_depth(cls, db: AsyncSession, reflection_id: int) -> EduReflectionDepthHistory | None:
        result = await db.execute(
            select(EduReflectionDepthHistory)
            .where(EduReflectionDepthHistory.reflection_id == reflection_id)
            .order_by(EduReflectionDepthHistory.create_time.desc())
            .limit(1)
        )
        return result.scalars().first()
