from sqlalchemy import delete, desc, or_, select
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
        """获取教师自己创建的任务列表"""
        result = await db.execute(
            select(EduTask)
            .where(EduTask.teacher_id == teacher_id, EduTask.del_flag == '0')
            .order_by(desc(EduTask.create_time))
        )
        return list(result.scalars().all())

    @classmethod
    async def get_teacher_all_tasks(cls, db: AsyncSession, teacher_id: int, class_ids: list[int]) -> list:
        """
        教师视角：获取自己创建的任务 + 所管班级学生的自研课题。
        teacher_id: 当前教师用户ID
        class_ids: 教师所管理的班级ID列表
        """
        from module_admin.entity.do.edu_do import EduStudentProfile
        # 子查询：所管班级内所有学生的 user_id
        student_subq = (
            select(EduStudentProfile.user_id)
            .where(EduStudentProfile.class_id.in_(class_ids))
        )
        # 主查询：教师自己的任务 OR 所管班级学生的自研课题
        result = await db.execute(
            select(EduTask)
            .where(
                EduTask.del_flag == '0',
                or_(
                    EduTask.teacher_id == teacher_id,  # 教师自己创建的
                    EduTask.student_id.in_(student_subq),  # 所管班级学生的自研课题
                )
            )
            .order_by(desc(EduTask.create_time))
        )
        return list(result.scalars().all())

    @classmethod
    async def get_student_self_tasks(cls, db: AsyncSession, student_id: int) -> list:
        """获取学生自己创建的自研课题列表"""
        result = await db.execute(
            select(EduTask)
            .where(
                EduTask.creator_type == '1',
                EduTask.student_id == student_id,
                EduTask.del_flag == '0',
            )
            .order_by(desc(EduTask.create_time))
        )
        return list(result.scalars().all())

    @classmethod
    async def get_published_tasks_by_dept_ids(cls, db: AsyncSession, dept_ids: list[int]) -> list:
        """获取指定班级的已发布任务（仅教师指派的，creator_type='0'）"""
        result = await db.execute(
            select(EduTask)
            .join(EduTaskClass, EduTask.task_id == EduTaskClass.task_id)
            .where(
                EduTaskClass.dept_id.in_(dept_ids),
                EduTask.creator_type == '0',
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
