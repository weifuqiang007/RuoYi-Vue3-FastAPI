from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from module_learning.dao.record_dao import RecordDao
from module_learning.entity.do.record_do import EduLearningRecord
from module_learning.entity.do.task_do import EduTask
from utils.page_util import PageUtil

# 状态流转映射
STAGE_FLOW = {
    'scenario': 'decision',
    'decision': 'reflection',
    'reflection': 'research',
    'research': 'submitted',
}

STAGE_STATUS_FIELD = {
    'scenario': 'scenario_status',
    'decision': 'decision_status',
    'reflection': 'reflection_status',
    'research': 'research_status',
}


class RecordService:

    @classmethod
    async def start_task(cls, db: AsyncSession, task_id: int, user_id: int,
                         roles: list | None = None) -> dict:
        """用户开始任务，创建学习记录（支持 student/teacher/admin 所有角色）"""
        # 检查是否已有记录（UNIQUE(task_id, user_id) 保证幂等）
        existing = await RecordDao.get_by_task_and_user(db, task_id, user_id)
        if existing:
            return {'record_id': existing.record_id, 'current_stage': existing.current_stage}
        record = EduLearningRecord(
            task_id=task_id,
            user_id=user_id,
            create_by=str(user_id),
        )
        record = await RecordDao.create(db, record)
        return {'record_id': record.record_id, 'current_stage': record.current_stage}

    @classmethod
    async def get_my_records(cls, db: AsyncSession, user_id: int,
                             filters: dict | None = None,
                             page_num: int = 1, page_size: int = 10) -> dict:
        """
        我的学习记录列表（分页）。
        DAO 返回 [(EduLearningRecord, EduTask, teacher_nick_name, student_nick_name), ...]
        根据 task.creator_type 决定 creator_name 取 teacher_name 还是 student_name。
        """
        rows_data = await RecordDao.get_my_records(db, user_id, filters)
        rows = [
            cls._record_to_dict(
                row[0], task=row[1],
                teacher_name=row[2], student_name=row[3],
            )
            for row in rows_data
        ]
        return PageUtil.get_page_obj(rows, page_num, page_size).model_dump()

    @classmethod
    async def get_detail(cls, db: AsyncSession, record_id: int, user_id: int | None = None) -> dict | None:
        """记录详情（JOIN task 以返回 preset_scenario 等任务信息）"""
        record = await RecordDao.get_by_id(db, record_id)
        if not record:
            return None
        if user_id and record.user_id != user_id:
            return None
        # 查询关联的任务，获取 preset_scenario 等字段
        task = None
        if record.task_id:
            from module_learning.dao.task_dao import TaskDao
            task = await TaskDao.get_by_id(db, record.task_id)
        return cls._record_to_dict(record, task=task)

    @classmethod
    async def advance_stage(cls, db: AsyncSession, record_id: int, user_id: int) -> dict:
        """推进到下一区"""
        record = await RecordDao.get_by_id(db, record_id)
        if not record:
            raise ValueError('学习记录不存在')
        if record.user_id != user_id:
            raise PermissionError('无权操作他人记录')

        current_stage = record.current_stage
        cls._validate_advance(record, current_stage)

        # 当前区标记完成
        status_field = STAGE_STATUS_FIELD.get(current_stage)
        if status_field:
            setattr(record, status_field, '2')

        # 推进到下一区
        next_stage = STAGE_FLOW.get(current_stage)
        if not next_stage:
            raise ValueError(f'已是最后阶段: {current_stage}')

        record.current_stage = next_stage
        next_status_field = STAGE_STATUS_FIELD.get(next_stage)
        if next_status_field:
            setattr(record, next_status_field, '1')

        # 提交状态
        if next_stage == 'submitted':
            record.status = 'submitted'
            record.submit_time = datetime.now()

        record.update_time = datetime.now()
        await RecordDao.update(db, record)
        return {'record_id': record.record_id, 'current_stage': next_stage}

    @classmethod
    def _validate_advance(cls, record: EduLearningRecord, current_stage: str):
        """前置校验：当前区必须有数据"""
        if current_stage == 'scenario':
            if not record.scenario_id:
                raise ValueError('情境区尚未保存数据，无法进入决策区')
        elif current_stage == 'decision':
            if record.decision_id is None:
                raise ValueError('决策区尚未保存数据，无法进入反思区')
        elif current_stage == 'reflection':
            if not record.reflection_id:
                raise ValueError('反思区尚未保存数据，无法进入研究生成区')
        elif current_stage == 'research':
            if not record.research_id:
                raise ValueError('研究区尚未保存数据，无法提交')

    @classmethod
    def _record_to_dict(cls, record: EduLearningRecord,
                        task: EduTask | None = None,
                        teacher_name: str | None = None,
                        student_name: str | None = None,) -> dict:
        """
        将学习记录转为前端可读的字典。
        - task: 关联的任务对象（来自JOIN查询），列表查询时传入，详情查询时不传
        - teacher_name: 任务创建者（教师）昵称，由DAO的JOIN查询传入
        - student_name: 任务创建者（学生）昵称，由DAO的JOIN查询传入
        """
        # 根据 creator_type 确定创建者姓名
        creator_name = None
        if task:
            creator_name = teacher_name if task.creator_type == '0' else student_name

        return {
            'record_id': record.record_id,
            'task_id': record.task_id,
            'task_name': task.task_name if task else None,
            'creator_type': task.creator_type if task else None,
            'creator_name': creator_name,
            'preset_scenario': task.preset_scenario if task else None,
            'task_description': task.task_description if task else None,
            'deadline': str(task.deadline) if task and task.deadline else None,
            'user_id': record.user_id,
            'current_stage': record.current_stage,
            'scenario_status': record.scenario_status,
            'decision_status': record.decision_status,
            'reflection_status': record.reflection_status,
            'research_status': record.research_status,
            'scenario_id': record.scenario_id,
            'decision_id': record.decision_id,
            'reflection_id': record.reflection_id,
            'research_id': record.research_id,
            'status': record.status,
            'score': float(record.score) if record.score else None,
            'teacher_feedback': record.teacher_feedback,
            'start_time': str(record.start_time) if record.start_time else None,
            'submit_time': str(record.submit_time) if record.submit_time else None,
            'complete_time': str(record.complete_time) if record.complete_time else None,
            'create_time': str(record.create_time) if record.create_time else None,
        }
