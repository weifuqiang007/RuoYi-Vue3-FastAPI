from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from module_admin.entity.do.dept_do import SysDept
from module_learning.entity.do.edu_do import EduStudentProfile
from module_admin.entity.do.user_do import SysUser
from module_learning.entity.do.record_do import EduLearningRecord
from module_learning.entity.do.review_do import EduReview, EduReviewDialogue
from module_learning.entity.do.task_do import EduTask
from utils.time_format_util import TimeFormatUtil


class ReviewDao:
    """反思批阅数据访问层"""

    @classmethod
    async def get_review_list(cls, db: AsyncSession, student_ids: list[int] | None,
                              filters: dict | None = None) -> list:
        """
        教师批阅列表查询。
        JOIN edu_task（课题名/类型）+ sys_user（学生姓名）+ edu_student_profile/sys_dept（班级）+ edu_review（批阅状态）。
        - student_ids=None：管理员视角，不过滤学生范围；
        - student_ids 非空：教师视角，仅查所管学生范围内的学习记录。
        返回 [(EduLearningRecord, EduTask, student_nick_name, class_name, EduReview), ...]
        """
        StudentUser = aliased(SysUser)
        conditions = [EduLearningRecord.del_flag == '0']
        if student_ids is not None:
            conditions.append(EduLearningRecord.user_id.in_(student_ids))

        f = filters or {}
        if f.get('task_id'):
            conditions.append(EduLearningRecord.task_id == f['task_id'])
        if f.get('creator_type'):
            conditions.append(EduTask.creator_type == f['creator_type'])
        if f.get('student_name'):
            conditions.append(StudentUser.nick_name.ilike(f"%{f['student_name']}%"))
        if f.get('class_id'):
            conditions.append(EduStudentProfile.class_id == f['class_id'])
        if f.get('submit_time_begin'):
            # 字符串必须先解析为 datetime，否则 asyncpg 绑定为 VARCHAR 与 TIMESTAMP 比较会类型不匹配
            conditions.append(EduLearningRecord.submit_time >= TimeFormatUtil.parse_datetime(f['submit_time_begin']))
        if f.get('submit_time_end'):
            conditions.append(EduLearningRecord.submit_time <= TimeFormatUtil.parse_datetime(f['submit_time_end']))
        # 批阅状态筛选
        rs = f.get('review_status')
        if rs == 'commented':
            conditions.append(EduReview.review_status == '1')
        elif rs == 'pending':
            # 待批阅：无点评或点评未提交
            conditions.append(EduReview.review_status.is_(None) | (EduReview.review_status != '1'))
        elif rs == 'no_ai':
            # 未生成AI评论
            conditions.append(EduReview.ai_comment_version.is_(None) | (EduReview.ai_comment_version == 0))

        result = await db.execute(
            select(EduLearningRecord, EduTask, StudentUser.nick_name, SysDept.dept_name, EduReview)
            .select_from(EduLearningRecord)
            .outerjoin(EduTask, EduLearningRecord.task_id == EduTask.task_id)
            .outerjoin(StudentUser, EduLearningRecord.user_id == StudentUser.user_id)
            .outerjoin(EduStudentProfile, EduLearningRecord.user_id == EduStudentProfile.user_id)
            .outerjoin(SysDept, EduStudentProfile.class_id == SysDept.dept_id)
            .outerjoin(EduReview, EduLearningRecord.record_id == EduReview.record_id)
            .where(*conditions)
            .order_by(desc(EduLearningRecord.submit_time))
        )
        return list(result.all())

    @classmethod
    async def get_by_record_id(cls, db: AsyncSession, record_id: int) -> EduReview | None:
        result = await db.execute(
            select(EduReview).where(EduReview.record_id == record_id, EduReview.del_flag == '0')
        )
        return result.scalars().first()

    @classmethod
    async def create(cls, db: AsyncSession, review: EduReview) -> EduReview:
        db.add(review)
        await db.flush()
        return review

    @classmethod
    async def update(cls, db: AsyncSession, review: EduReview) -> EduReview:
        await db.flush()
        return review

    @classmethod
    async def create_dialogue(cls, db: AsyncSession, dialogue: EduReviewDialogue) -> EduReviewDialogue:
        db.add(dialogue)
        await db.flush()
        return dialogue

    @classmethod
    async def get_dialogue_history(cls, db: AsyncSession, record_id: int) -> list[EduReviewDialogue]:
        result = await db.execute(
            select(EduReviewDialogue)
            .where(EduReviewDialogue.record_id == record_id)
            .order_by(desc(EduReviewDialogue.version))
        )
        return list(result.scalars().all())
