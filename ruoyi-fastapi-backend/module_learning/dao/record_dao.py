from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from module_admin.entity.do.user_do import SysUser
from module_learning.entity.do.record_do import EduLearningRecord
from module_learning.entity.do.task_do import EduTask
from utils.time_format_util import TimeFormatUtil


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
    async def get_my_records(cls, db: AsyncSession, user_id: int,
                             filters: dict | None = None) -> list:
        """
        获取指定用户的学习记录，JOIN edu_task + sys_user（双LEFT JOIN）返回关联信息。
        返回 [(EduLearningRecord, EduTask, teacher_nick_name, student_nick_name), ...]

        - EduLearningRecord: 学习记录主表数据
        - EduTask: 关联的任务/课题信息（可能为 None，理论上不会）
        - teacher_nick_name: 任务创建者（教师）昵称，教师创建时非空
        - student_nick_name: 任务创建者（学生）昵称，学生自研时非空
        """
        TeacherUser = aliased(SysUser)
        StudentUser = aliased(SysUser)

        conditions = [
            EduLearningRecord.user_id == user_id,
            EduLearningRecord.del_flag == '0',
        ]
        f = filters or {}

        # 课题名称模糊匹配
        if f.get('task_name'):
            conditions.append(EduTask.task_name.ilike(f"%{f['task_name']}%"))
        # 创建者类型筛选
        if f.get('creator_type'):
            conditions.append(EduTask.creator_type == f['creator_type'])
        # 创建时间范围（字符串必须先解析为 datetime，否则 asyncpg 绑定为 VARCHAR 与 TIMESTAMP 比较会类型不匹配）
        if f.get('create_time_begin'):
            conditions.append(EduLearningRecord.create_time >= TimeFormatUtil.parse_datetime(f['create_time_begin']))
        if f.get('create_time_end'):
            conditions.append(EduLearningRecord.create_time <= TimeFormatUtil.parse_datetime(f['create_time_end']))
        # 截止时间范围
        if f.get('deadline_begin'):
            conditions.append(EduTask.deadline >= TimeFormatUtil.parse_datetime(f['deadline_begin']))
        if f.get('deadline_end'):
            conditions.append(EduTask.deadline <= TimeFormatUtil.parse_datetime(f['deadline_end']))

        result = await db.execute(
            select(EduLearningRecord, EduTask, TeacherUser.nick_name, StudentUser.nick_name)
            .outerjoin(EduTask, EduLearningRecord.task_id == EduTask.task_id)
            .outerjoin(TeacherUser, EduTask.teacher_id == TeacherUser.user_id)
            .outerjoin(StudentUser, EduTask.student_id == StudentUser.user_id)
            .where(*conditions)
            .order_by(desc(EduLearningRecord.create_time))
        )
        return list(result.all())

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
