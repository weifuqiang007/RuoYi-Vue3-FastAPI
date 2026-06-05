from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from module_learning.dao.task_dao import TaskDao
from module_learning.entity.do.task_do import EduTask
from module_learning.entity.vo.task_vo import TaskCreateModel, TaskUpdateModel
from common.vo import CrudResponseModel


class TaskService:

    @classmethod
    async def create_task(cls, db: AsyncSession, data: TaskCreateModel, teacher_id: int, create_by: str = '') -> dict:
        task = EduTask(
            task_name=data.task_name,
            task_description=data.task_description,
            teacher_id=teacher_id,
            preset_scenario=data.preset_scenario,
            scenario_kb_ids=data.scenario_kb_ids,
            decision_kb_ids=data.decision_kb_ids,
            reflection_kb_ids=data.reflection_kb_ids,
            research_kb_ids=data.research_kb_ids,
            scenario_config=data.scenario_config,
            reflection_config=data.reflection_config,
            deadline=data.deadline,
            create_by=create_by,
        )
        task = await TaskDao.create_task(db, task)
        return {'task_id': task.task_id}

    @classmethod
    async def update_task(cls, db: AsyncSession, data: TaskUpdateModel, teacher_id: int, update_by: str = '') -> dict:
        task = await TaskDao.get_by_id(db, data.task_id)
        if not task:
            raise ValueError('任务不存在')
        if task.teacher_id != teacher_id:
            raise PermissionError('无权修改他人任务')
        update_fields = data.model_dump(exclude_unset=True, exclude={'task_id'})
        for k, v in update_fields.items():
            setattr(task, k, v)
        task.update_by = update_by
        task.update_time = datetime.now()
        await TaskDao.update_task(db, task)
        return {'task_id': task.task_id}

    @classmethod
    async def delete_task(cls, db: AsyncSession, task_id: int, teacher_id: int) -> dict:
        task = await TaskDao.get_by_id(db, task_id)
        if not task:
            raise ValueError('任务不存在')
        if task.teacher_id != teacher_id:
            raise PermissionError('无权删除他人任务')
        await TaskDao.delete_task(db, task_id)
        return {'task_id': task_id}

    @classmethod
    async def get_task_detail(cls, db: AsyncSession, task_id: int) -> dict | None:
        task = await TaskDao.get_by_id(db, task_id)
        if not task:
            return None
        assigned_classes = await TaskDao.get_assigned_classes(db, task_id)
        return {
            'task_id': task.task_id,
            'task_name': task.task_name,
            'task_description': task.task_description,
            'teacher_id': task.teacher_id,
            'preset_scenario': task.preset_scenario,
            'scenario_kb_ids': task.scenario_kb_ids,
            'decision_kb_ids': task.decision_kb_ids,
            'reflection_kb_ids': task.reflection_kb_ids,
            'research_kb_ids': task.research_kb_ids,
            'scenario_config': task.scenario_config,
            'reflection_config': task.reflection_config,
            'deadline': str(task.deadline) if task.deadline else None,
            'status': task.status,
            'assigned_classes': assigned_classes,
            'create_time': str(task.create_time) if task.create_time else None,
            'update_time': str(task.update_time) if task.update_time else None,
        }

    @classmethod
    async def get_teacher_tasks(cls, db: AsyncSession, teacher_id: int, page_num: int = 1, page_size: int = 10) -> dict:
        from utils.page_util import PageUtil
        tasks = await TaskDao.get_task_list_by_teacher(db, teacher_id)
        rows = [cls._task_to_dict(t) for t in tasks]
        return PageUtil.get_page_obj(rows, page_num, page_size).model_dump()

    @classmethod
    async def get_student_tasks(cls, db: AsyncSession, student_id: int, class_id: int | None, page_num: int = 1, page_size: int = 10) -> dict:
        """学生查看任务列表：教师指派的 + 自己的自研课题"""
        from utils.page_util import PageUtil
        from module_learning.dao.record_dao import RecordDao
        tasks = []
        # 教师指派的任务
        if class_id:
            published = await TaskDao.get_published_tasks_by_dept_ids(db, [class_id])
            for t in published:
                tasks.append(cls._task_to_dict(t, source='assigned'))
        # 自研课题（无 task_id 的学习记录）
        self_records = await RecordDao.get_self_study_records(db, student_id)
        for r in self_records:
            tasks.append({
                'task_id': None,
                'task_name': '自研课题',
                'task_description': '',
                'status': '1',
                'source': 'self_study',
                'record_id': r.record_id,
                'current_stage': r.current_stage,
                'create_time': str(r.create_time) if r.create_time else None,
            })
        return PageUtil.get_page_obj(tasks, page_num, page_size).model_dump()

    @classmethod
    async def publish_task(cls, db: AsyncSession, task_id: int, dept_ids: list[int], teacher_id: int) -> dict:
        task = await TaskDao.get_by_id(db, task_id)
        if not task:
            raise ValueError('任务不存在')
        if task.teacher_id != teacher_id:
            raise PermissionError('无权发布他人任务')
        if not dept_ids:
            raise ValueError('至少选择一个班级')
        await TaskDao.assign_classes(db, task_id, dept_ids)
        task.status = '1'
        task.update_time = datetime.now()
        await db.flush()
        return {'task_id': task_id, 'dept_ids': dept_ids}

    @classmethod
    async def copy_task(cls, db: AsyncSession, task_id: int, teacher_id: int, create_by: str = '') -> dict:
        task = await TaskDao.get_by_id(db, task_id)
        if not task:
            raise ValueError('任务不存在')
        new_task = EduTask(
            task_name=task.task_name + '(副本)',
            task_description=task.task_description,
            teacher_id=teacher_id,
            preset_scenario=task.preset_scenario,
            scenario_kb_ids=task.scenario_kb_ids,
            decision_kb_ids=task.decision_kb_ids,
            reflection_kb_ids=task.reflection_kb_ids,
            research_kb_ids=task.research_kb_ids,
            scenario_config=task.scenario_config,
            reflection_config=task.reflection_config,
            deadline=task.deadline,
            create_by=create_by,
        )
        new_task = await TaskDao.create_task(db, new_task)
        return {'task_id': new_task.task_id}

    @classmethod
    def _task_to_dict(cls, task: EduTask, source: str = 'teacher') -> dict:
        return {
            'task_id': task.task_id,
            'task_name': task.task_name,
            'task_description': task.task_description,
            'teacher_id': task.teacher_id,
            'preset_scenario': task.preset_scenario,
            'deadline': str(task.deadline) if task.deadline else None,
            'status': task.status,
            'source': source,
            'create_time': str(task.create_time) if task.create_time else None,
        }
