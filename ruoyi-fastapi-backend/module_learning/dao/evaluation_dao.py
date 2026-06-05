from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from module_learning.entity.do.evaluation_do import EduEvaluation, EduExcellentCase


class EvaluationDao:

    @classmethod
    async def create(cls, db: AsyncSession, evaluation: EduEvaluation) -> EduEvaluation:
        db.add(evaluation)
        await db.flush()
        return evaluation

    @classmethod
    async def get_by_id(cls, db: AsyncSession, evaluation_id: int) -> EduEvaluation | None:
        result = await db.execute(
            select(EduEvaluation).where(EduEvaluation.evaluation_id == evaluation_id)
        )
        return result.scalars().first()

    @classmethod
    async def get_by_record_id(cls, db: AsyncSession, record_id: int) -> EduEvaluation | None:
        result = await db.execute(
            select(EduEvaluation).where(EduEvaluation.record_id == record_id)
        )
        return result.scalars().first()

    @classmethod
    async def update(cls, db: AsyncSession, evaluation: EduEvaluation) -> EduEvaluation:
        await db.flush()
        return evaluation

    @classmethod
    async def get_excellent_cases(cls, db: AsyncSession) -> list:
        result = await db.execute(
            select(EduExcellentCase)
            .where(EduExcellentCase.status == '1')
            .order_by(desc(EduExcellentCase.create_time))
        )
        return list(result.scalars().all())

    @classmethod
    async def get_case_by_id(cls, db: AsyncSession, case_id: int) -> EduExcellentCase | None:
        result = await db.execute(
            select(EduExcellentCase).where(EduExcellentCase.case_id == case_id)
        )
        return result.scalars().first()

    @classmethod
    async def create_case(cls, db: AsyncSession, case: EduExcellentCase) -> EduExcellentCase:
        db.add(case)
        await db.flush()
        return case
