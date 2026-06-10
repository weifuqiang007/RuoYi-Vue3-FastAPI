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
    async def get_by_task_and_user(cls, db: AsyncSession, task_id: int, user_id: int) -> EduLearningRecord | None:
        """根据 task_id + user_id 查找唯一记录"""
        result = await db.execute(
            select(EduLearningRecord).where(
                EduLearningRecord.task_id == task_id,
                EduLearningRecord.user_id == user_id,
                EduLearningRecord.del_flag == '0',
            )
        )
        return result.scalars().first()

    @classmethod
    async def get_my_records(cls, db: AsyncSession, user_id: int) -> list:
        """获取指定用户的所有学习记录"""
        result = await db.execute(
            select(EduLearningRecord)
            .where(EduLearningRecord.user_id == user_id, EduLearningRecord.del_flag == '0')
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
