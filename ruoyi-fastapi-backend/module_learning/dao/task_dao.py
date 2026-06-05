from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from module_learning.entity.do.task_do import EduTask, EduTaskClass


class TaskDao:

    @classmethod
    async def create_task(cls, db: AsyncSession, task: EduTask) -> EduTask:
        db.add(task)
        await db.flush()
        return task

    @classmethod
    async def get_by_id(cls, db: AsyncSession, task_id: int) -> EduTask | None:
        result = await db.execute(
            select(EduTask).where(EduTask.task_id == task_id, EduTask.del_flag == '0')
        )
        return result.scalars().first()

    @classmethod
    async def get_task_list_by_teacher(cls, db: AsyncSession, teacher_id: int) -> list:
        result = await db.execute(
            select(EduTask)
            .where(EduTask.teacher_id == teacher_id, EduTask.del_flag == '0')
            .order_by(desc(EduTask.create_time))
        )
        return list(result.scalars().all())

    @classmethod
    async def get_published_tasks_by_dept_ids(cls, db: AsyncSession, dept_ids: list[int]) -> list:
        """获取指定班级的已发布任务"""
        result = await db.execute(
            select(EduTask)
            .join(EduTaskClass, EduTask.task_id == EduTaskClass.task_id)
            .where(
                EduTaskClass.dept_id.in_(dept_ids),
                EduTask.status == '1',
                EduTask.del_flag == '0',
            )
            .order_by(desc(EduTask.create_time))
        )
        return list(result.scalars().all())

    @classmethod
    async def update_task(cls, db: AsyncSession, task: EduTask) -> EduTask:
        await db.flush()
        return task

    @classmethod
    async def delete_task(cls, db: AsyncSession, task_id: int) -> None:
        from sqlalchemy import update
        await db.execute(
            update(EduTask).where(EduTask.task_id == task_id).values(del_flag='2')
        )

    @classmethod
    async def assign_classes(cls, db: AsyncSession, task_id: int, dept_ids: list[int]) -> None:
        # 先清除旧分配
        await db.execute(delete(EduTaskClass).where(EduTaskClass.task_id == task_id))
        # 批量新增
        for dept_id in dept_ids:
            db.add(EduTaskClass(task_id=task_id, dept_id=dept_id))
        await db.flush()

    @classmethod
    async def get_assigned_classes(cls, db: AsyncSession, task_id: int) -> list[int]:
        result = await db.execute(
            select(EduTaskClass.dept_id).where(EduTaskClass.task_id == task_id)
        )
        return [r[0] for r in result.all()]

    @classmethod
    async def get_all_published_tasks(cls, db: AsyncSession) -> list:
        """获取所有已发布任务"""
        result = await db.execute(
            select(EduTask)
            .where(EduTask.status == '1', EduTask.del_flag == '0')
            .order_by(desc(EduTask.create_time))
        )
        return list(result.scalars().all())
