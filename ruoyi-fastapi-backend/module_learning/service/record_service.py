from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from module_learning.dao.record_dao import RecordDao
from module_learning.entity.do.record_do import EduLearningRecord


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
    async def start_task(cls, db: AsyncSession, task_id: int, student_id: int) -> dict:
        """学生开始任务，创建学习记录"""
        # 检查是否已有记录
        existing = await RecordDao.get_by_task_and_student(db, task_id, student_id)
        if existing:
            return {'record_id': existing.record_id, 'current_stage': existing.current_stage}
        record = EduLearningRecord(
            task_id=task_id,
            student_id=student_id,
            create_by=str(student_id),
        )
        record = await RecordDao.create(db, record)
        return {'record_id': record.record_id, 'current_stage': record.current_stage}

    @classmethod
    async def create_self_study(cls, db: AsyncSession, student_id: int) -> dict:
        """创建自研课题"""
        record = EduLearningRecord(
            task_id=None,
            student_id=student_id,
            create_by=str(student_id),
        )
        record = await RecordDao.create(db, record)
        return {'record_id': record.record_id, 'current_stage': record.current_stage}

    @classmethod
    async def get_my_records(cls, db: AsyncSession, student_id: int, page_num: int = 1, page_size: int = 10) -> dict:
        """我的学习记录列表（分页）"""
        from utils.page_util import PageUtil
        records = await RecordDao.get_my_records(db, student_id)
        rows = [cls._record_to_dict(r) for r in records]
        return PageUtil.get_page_obj(rows, page_num, page_size).model_dump()

    @classmethod
    async def get_detail(cls, db: AsyncSession, record_id: int, student_id: int | None = None) -> dict | None:
        """记录详情"""
        record = await RecordDao.get_by_id(db, record_id)
        if not record:
            return None
        if student_id and record.student_id != student_id:
            return None
        return cls._record_to_dict(record)

    @classmethod
    async def advance_stage(cls, db: AsyncSession, record_id: int, student_id: int) -> dict:
        """推进到下一区"""
        record = await RecordDao.get_by_id(db, record_id)
        if not record:
            raise ValueError('学习记录不存在')
        if record.student_id != student_id:
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
    def _record_to_dict(cls, record: EduLearningRecord) -> dict:
        return {
            'record_id': record.record_id,
            'task_id': record.task_id,
            'student_id': record.student_id,
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
