from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from module_learning.entity.do.decision_do import EduDecisionData, EduDecisionDialogue


class DecisionDao:

    @classmethod
    async def create(cls, db: AsyncSession, decision: EduDecisionData) -> EduDecisionData:
        db.add(decision)
        await db.flush()
        return decision

    @classmethod
    async def get_by_id(cls, db: AsyncSession, decision_id: int) -> EduDecisionData | None:
        result = await db.execute(
            select(EduDecisionData).where(EduDecisionData.decision_id == decision_id)
        )
        return result.scalars().first()

    @classmethod
    async def get_by_record_id(cls, db: AsyncSession, record_id: int) -> list:
        result = await db.execute(
            select(EduDecisionData)
            .where(EduDecisionData.record_id == record_id)
            .order_by(EduDecisionData.key_event_index)
        )
        return list(result.scalars().all())

    @classmethod
    async def update(cls, db: AsyncSession, decision: EduDecisionData) -> EduDecisionData:
        await db.flush()
        return decision

    @classmethod
    async def add_dialogue(cls, db: AsyncSession, dialogue: EduDecisionDialogue) -> EduDecisionDialogue:
        db.add(dialogue)
        await db.flush()
        return dialogue

    @classmethod
    async def get_dialogues(cls, db: AsyncSession, decision_id: int) -> list:
        result = await db.execute(
            select(EduDecisionDialogue)
            .where(EduDecisionDialogue.decision_id == decision_id)
            .order_by(EduDecisionDialogue.create_time)
        )
        return list(result.scalars().all())
