from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from module_learning.entity.do.record_do import EduLearningRecord


class RecordDao:

    @classmethod
    async def create(cls, db: AsyncSession, record: EduLearningRecord) -> EduLearningRecord:
        db.add(record)
        await db.flush()
        return record

    @classmethod
    async def get_by_id(cls, db: AsyncSession, record_id: int) -> EduLearningRecord | None:
        result = await db.execute(
            select(EduLearningRecord).where(
                EduLearningRecord.record_id == record_id,
                EduLearningRecord.del_flag == '0',
            )
        )
        return result.scalars().first()

    @classmethod
    async def get_by_task_and_student(cls, db: AsyncSession, task_id: int | None, student_id: int) -> EduLearningRecord | None:
        query = select(EduLearningRecord).where(
            EduLearningRecord.student_id == student_id,
            EduLearningRecord.del_flag == '0',
        )
        if task_id is not None:
            query = query.where(EduLearningRecord.task_id == task_id)
        else:
            query = query.where(EduLearningRecord.task_id.is_(None))
        result = await db.execute(query)
        return result.scalars().first()

    @classmethod
    async def get_my_records(cls, db: AsyncSession, student_id: int) -> list:
        result = await db.execute(
            select(EduLearningRecord)
            .where(EduLearningRecord.student_id == student_id, EduLearningRecord.del_flag == '0')
            .order_by(desc(EduLearningRecord.create_time))
        )
        return list(result.scalars().all())

    @classmethod
    async def get_self_study_records(cls, db: AsyncSession, student_id: int) -> list:
        result = await db.execute(
            select(EduLearningRecord)
            .where(
                EduLearningRecord.student_id == student_id,
                EduLearningRecord.task_id.is_(None),
                EduLearningRecord.del_flag == '0',
            )
            .order_by(desc(EduLearningRecord.create_time))
        )
        return list(result.scalars().all())

    @classmethod
    async def get_by_task_id(cls, db: AsyncSession, task_id: int) -> list:
        result = await db.execute(
            select(EduLearningRecord)
            .where(EduLearningRecord.task_id == task_id, EduLearningRecord.del_flag == '0')
            .order_by(desc(EduLearningRecord.create_time))
        )
        return list(result.scalars().all())

    @classmethod
    async def update(cls, db: AsyncSession, record: EduLearningRecord) -> EduLearningRecord:
        await db.flush()
        return record
