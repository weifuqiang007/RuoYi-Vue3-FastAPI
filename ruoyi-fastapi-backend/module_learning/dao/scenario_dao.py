from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from module_learning.entity.do.scenario_do import EduScenarioData, EduScenarioDialogue


class ScenarioDao:

    @classmethod
    async def create(cls, db: AsyncSession, scenario: EduScenarioData) -> EduScenarioData:
        db.add(scenario)
        await db.flush()
        return scenario

    @classmethod
    async def get_by_id(cls, db: AsyncSession, scenario_id: int) -> EduScenarioData | None:
        result = await db.execute(
            select(EduScenarioData).where(EduScenarioData.scenario_id == scenario_id)
        )
        return result.scalars().first()

    @classmethod
    async def get_by_record_id(cls, db: AsyncSession, record_id: int) -> EduScenarioData | None:
        result = await db.execute(
            select(EduScenarioData).where(EduScenarioData.record_id == record_id)
        )
        return result.scalars().first()

    @classmethod
    async def update(cls, db: AsyncSession, scenario: EduScenarioData) -> EduScenarioData:
        await db.flush()
        return scenario

    @classmethod
    async def add_dialogue(cls, db: AsyncSession, dialogue: EduScenarioDialogue) -> EduScenarioDialogue:
        db.add(dialogue)
        await db.flush()
        return dialogue

    @classmethod
    async def get_dialogues(cls, db: AsyncSession, scenario_id: int) -> list:
        result = await db.execute(
            select(EduScenarioDialogue)
            .where(EduScenarioDialogue.scenario_id == scenario_id)
            .order_by(EduScenarioDialogue.create_time)
        )
        return list(result.scalars().all())
