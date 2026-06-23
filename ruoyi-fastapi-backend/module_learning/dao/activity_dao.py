from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from module_admin.entity.do.dept_do import SysDept
from module_admin.entity.do.edu_do import EduStudentProfile, EduTeacherProfile
from module_admin.entity.do.role_do import SysRole
from module_admin.entity.do.user_do import SysUser, SysUserRole
from module_learning.entity.do.record_do import EduLearningRecord
from module_learning.entity.do.review_do import EduReview
from module_learning.entity.do.task_do import EduTask


class ActivityDao:
    """
    首页动态墙聚合查询 + 用户名片。

    基于现有状态字段 + 时间戳「推断」最近动态，不引入事件日志表。
    每条动态返回统一结构：{actor_id, actor_name, actor_role, task_id, task_name, record_id, action, occurred_at}。
    actor_role 由 action 推断（publish/review→teacher，ongoing/submit→student），用于前端名片图标着色。
    """

    @classmethod
    async def get_recent_published(cls, db: AsyncSession, limit: int = 8) -> list[dict]:
        """教师/学生发布任务：edu_task status='1'，按 update_time 倒序。actor=创建者(teacher 或 student)"""
        TeacherUser = aliased(SysUser)
        StudentUser = aliased(SysUser)
        result = await db.execute(
            select(
                EduTask.task_id, EduTask.task_name,
                EduTask.teacher_id, EduTask.student_id,
                TeacherUser.nick_name, StudentUser.nick_name,
                EduTask.update_time,
            )
            .outerjoin(TeacherUser, EduTask.teacher_id == TeacherUser.user_id)
            .outerjoin(StudentUser, EduTask.student_id == StudentUser.user_id)
            .where(EduTask.status == '1', EduTask.del_flag == '0')
            .order_by(desc(EduTask.update_time))
            .limit(limit)
        )
        items = []
        for r in result.all():
            actor_id = r[2] or r[3]
            actor_role = 'student' if r[3] else ('teacher' if r[2] else 'admin')
            items.append({
                'actor_id': actor_id, 'actor_name': r[4] or r[5] or '某用户', 'actor_role': actor_role,
                'task_id': r[0], 'task_name': r[1] or '未命名课题', 'record_id': None,
                'action': 'publish', 'occurred_at': r[6],
            })
        return items

    @classmethod
    async def get_recent_ongoing(cls, db: AsyncSession, limit: int = 8) -> list[dict]:
        """学生正在处理：record status='ongoing'，按 update_time 倒序。actor=学生"""
        StudentUser = aliased(SysUser)
        result = await db.execute(
            select(
                EduTask.task_id, EduTask.task_name,
                EduLearningRecord.record_id, EduLearningRecord.user_id,
                StudentUser.nick_name, EduLearningRecord.update_time,
            )
            .select_from(EduLearningRecord)
            .outerjoin(EduTask, EduLearningRecord.task_id == EduTask.task_id)
            .outerjoin(StudentUser, EduLearningRecord.user_id == StudentUser.user_id)
            .where(EduLearningRecord.status == 'ongoing', EduLearningRecord.del_flag == '0')
            .order_by(desc(EduLearningRecord.update_time))
            .limit(limit)
        )
        return [
            {
                'actor_id': r[3],
                'actor_name': r[4],
                'actor_role': 'student',
                'task_id': r[0],
                'task_name': r[1],
                'record_id': r[2],
                'action': 'ongoing',
                'occurred_at': r[5],
            }
            for r in result.all()
        ]

    @classmethod
    async def get_recent_submitted(cls, db: AsyncSession, limit: int = 8) -> list[dict]:
        """学生已提交：record status='submitted' 且 submit_time 非空，按 submit_time 倒序。"""
        StudentUser = aliased(SysUser)
        result = await db.execute(
            select(
                EduTask.task_id, EduTask.task_name,
                EduLearningRecord.record_id, EduLearningRecord.user_id,
                StudentUser.nick_name, EduLearningRecord.submit_time,
            )
            .select_from(EduLearningRecord)
            .outerjoin(EduTask, EduLearningRecord.task_id == EduTask.task_id)
            .outerjoin(StudentUser, EduLearningRecord.user_id == StudentUser.user_id)
            .where(
                EduLearningRecord.status == 'submitted',
                EduLearningRecord.submit_time.is_not(None),
                EduLearningRecord.del_flag == '0',
            )
            .order_by(desc(EduLearningRecord.submit_time))
            .limit(limit)
        )
        return [
            {
                'actor_id': r[3], 'actor_name': r[4] or '某同学', 'actor_role': 'student',
                'task_id': r[0], 'task_name': r[1] or '未命名课题', 'record_id': r[2],
                'action': 'submit', 'occurred_at': r[5],
            }
            for r in result.all()
        ]

    @classmethod
    async def get_recent_reviewed(cls, db: AsyncSession, limit: int = 8) -> list[dict]:
        """教师做了点评：review review_status='1' 且 teacher_comment 非空，按 review_time 倒序。"""
        TeacherUser = aliased(SysUser)
        result = await db.execute(
            select(
                EduTask.task_id, EduTask.task_name,
                EduReview.record_id, EduReview.teacher_id,
                TeacherUser.nick_name, EduReview.review_time,
            )
            .select_from(EduReview)
            .outerjoin(EduTask, EduReview.task_id == EduTask.task_id)
            .outerjoin(TeacherUser, EduReview.teacher_id == TeacherUser.user_id)
            .where(
                EduReview.review_status == '1',
                EduReview.teacher_comment.is_not(None),
                EduReview.teacher_comment != '',
                EduReview.review_time.is_not(None),
                EduReview.del_flag == '0',
            )
            .order_by(desc(EduReview.review_time))
            .limit(limit)
        )
        return [
            {
                'actor_id': r[3], 'actor_name': r[4] or '某老师', 'actor_role': 'teacher',
                'task_id': r[0], 'task_name': r[1] or '未命名课题', 'record_id': r[2],
                'action': 'review', 'occurred_at': r[5],
            }
            for r in result.all()
        ]

    @classmethod
    async def get_user_card(cls, db: AsyncSession, user_id: int) -> dict | None:
        """
        用户名片：JOIN 角色/学生班级/教师职称，一次查询取齐。
        返回 {nick_name, role_key, role_name, class_name, major, title, create_time}。
        """
        result = await db.execute(
            select(
                SysUser.nick_name, SysUser.create_time,
                SysRole.role_key, SysRole.role_name,
                SysDept.dept_name, EduStudentProfile.major, EduTeacherProfile.title,
            )
            .select_from(SysUser)
            .outerjoin(SysUserRole, SysUser.user_id == SysUserRole.user_id)
            .outerjoin(SysRole, (SysUserRole.role_id == SysRole.role_id) & (SysRole.del_flag == '0'))
            .outerjoin(EduStudentProfile, (SysUser.user_id == EduStudentProfile.user_id) & (EduStudentProfile.del_flag == '0'))
            .outerjoin(SysDept, EduStudentProfile.class_id == SysDept.dept_id)
            .outerjoin(EduTeacherProfile, (SysUser.user_id == EduTeacherProfile.user_id) & (EduTeacherProfile.del_flag == '0'))
            .where(SysUser.user_id == user_id, SysUser.del_flag == '0')
            .limit(1)
        )
        row = result.first()
        if not row:
            return None
        return {
            'user_id': user_id,
            'nick_name': row[0] or '',
            'create_time': row[1].strftime('%Y-%m-%d') if row[1] else '',
            'role_key': row[2] or '',
            'role_name': row[3] or '',
            'class_name': row[4] or '',   # 学生所属班级
            'major': row[5] or '',        # 学生专业
            'title': row[6] or '',        # 教师职称
        }
