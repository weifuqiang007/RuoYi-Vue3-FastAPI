from sqlalchemy import delete, desc, or_, select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from module_admin.entity.do.dept_do import SysDept
from module_admin.entity.do.user_do import SysUser
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
        返回 [(EduTask, teacher_nick_name, student_nick_name), ...]
        """
        from module_admin.entity.do.edu_do import EduStudentProfile
        TeacherUser = aliased(SysUser)
        StudentUser = aliased(SysUser)
        student_subq = (
            select(EduStudentProfile.user_id)
            .where(EduStudentProfile.class_id.in_(class_ids))
        )
        result = await db.execute(
            select(EduTask, TeacherUser.nick_name, StudentUser.nick_name)
            .outerjoin(TeacherUser, EduTask.teacher_id == TeacherUser.user_id)
            .outerjoin(StudentUser, EduTask.student_id == StudentUser.user_id)
            .where(
                EduTask.del_flag == '0',
                or_(
                    EduTask.teacher_id == teacher_id,
                    EduTask.student_id.in_(student_subq),
                )
            )
            .order_by(desc(EduTask.create_time))
        )
        return list(result.all())

    @classmethod
    async def get_assigned_classes_batch(cls, db: AsyncSession, task_ids: list[int]) -> dict:
        """
        批量获取多个任务分配的班级信息。
        返回 { task_id: [{'dept_id': x, 'dept_name': 'xx'}, ...], ... }
        """
        if not task_ids:
            return {}
        result = await db.execute(
            select(EduTaskClass.task_id, SysDept.dept_id, SysDept.dept_name)
            .select_from(EduTaskClass)
            .outerjoin(SysDept, EduTaskClass.dept_id == SysDept.dept_id)
            .where(EduTaskClass.task_id.in_(task_ids))
        )
        mapping: dict[int, list] = {}
        for row in result.all():
            tid = row[0]
            if tid not in mapping:
                mapping[tid] = []
            mapping[tid].append({'dept_id': row[1], 'dept_name': row[2]})
        return mapping

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
    async def get_assigned_classes(cls, db: AsyncSession, task_id: int) -> list[dict]:
        """获取单个任务分配的班级信息，返回 [{'dept_id': x, 'dept_name': 'xx'}, ...]"""
        result = await db.execute(
            select(EduTaskClass.dept_id, SysDept.dept_name)
            .select_from(EduTaskClass)
            .outerjoin(SysDept, EduTaskClass.dept_id == SysDept.dept_id)
            .where(EduTaskClass.task_id == task_id)
        )
        return [{'dept_id': r[0], 'dept_name': r[1]} for r in result.all()]

    @classmethod
    async def get_all_tasks_for_admin(cls, db: AsyncSession, filters: dict | None = None) -> list:
        """管理员视角：获取所有任务（含教师任务和学生自研课题），附带创建者姓名，支持动态过滤"""
        TeacherUser = aliased(SysUser)
        StudentUser = aliased(SysUser)

        conditions = [EduTask.del_flag == '0']
        f = filters or {}

        # 任务类型
        if f.get('creator_type'):
            conditions.append(EduTask.creator_type == f['creator_type'])
        # 任务名称模糊匹配
        if f.get('task_name'):
            conditions.append(EduTask.task_name.ilike(f"%{f['task_name']}%"))
        # 任务简述模糊匹配
        if f.get('task_description'):
            conditions.append(EduTask.task_description.ilike(f"%{f['task_description']}%"))
        # 发布状态
        if f.get('status'):
            conditions.append(EduTask.status == f['status'])
        # 教师姓名模糊匹配（JOIN TeacherUser 后过滤）
        if f.get('teacher_name'):
            conditions.append(TeacherUser.nick_name.ilike(f"%{f['teacher_name']}%"))
        # 截止时间范围
        if f.get('deadline_begin'):
            conditions.append(EduTask.deadline >= f['deadline_begin'])
        if f.get('deadline_end'):
            conditions.append(EduTask.deadline <= f['deadline_end'])
        # 创建时间范围
        if f.get('create_time_begin'):
            conditions.append(EduTask.create_time >= f['create_time_begin'])
        if f.get('create_time_end'):
            conditions.append(EduTask.create_time <= f['create_time_end'])
        # 归属班级（子查询 edu_task_class）
        if f.get('dept_id'):
            dept_subq = (
                select(EduTaskClass.task_id)
                .where(EduTaskClass.dept_id == f['dept_id'])
            )
            conditions.append(EduTask.task_id.in_(dept_subq))

        result = await db.execute(
            select(EduTask, TeacherUser.nick_name, StudentUser.nick_name)
            .outerjoin(TeacherUser, EduTask.teacher_id == TeacherUser.user_id)
            .outerjoin(StudentUser, EduTask.student_id == StudentUser.user_id)
            .where(*conditions)
            .order_by(desc(EduTask.create_time))
        )
        return list(result.all())

    @classmethod
    async def get_all_published_tasks(cls, db: AsyncSession) -> list:
        """获取所有已发布任务"""
        result = await db.execute(
            select(EduTask)
            .where(EduTask.status == '1', EduTask.del_flag == '0')
            .order_by(desc(EduTask.create_time))
        )
        return list(result.scalars().all())
