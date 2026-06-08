from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from module_learning.dao.task_dao import TaskDao
from module_learning.entity.do.task_do import EduTask
from module_learning.entity.vo.task_vo import TaskCreateModel, TaskUpdateModel, StudentTaskCreateModel
from common.vo import CrudResponseModel


class TaskService:

    @classmethod
    async def create_task(cls, db: AsyncSession, data: TaskCreateModel, teacher_id: int, create_by: str = '') -> dict:
        """教师创建教学任务（creator_type='0'）"""
        task = EduTask(
            task_name=data.task_name,
            task_description=data.task_description,
            teacher_id=teacher_id,
            creator_type='0',
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
    async def create_student_task(cls, db: AsyncSession, data: StudentTaskCreateModel, student_id: int, create_by: str = '') -> dict:
        """学生自建自研课题（creator_type='1'）"""
        task = EduTask(
            task_name=data.task_name,
            task_description=data.task_description,
            teacher_id=None,
            creator_type='1',
            student_id=student_id,
            status='1',  # 学生自建课题直接为已发布状态
            create_by=create_by,
        )
        task = await TaskDao.create_task(db, task)
        return {'task_id': task.task_id}

    @classmethod
    async def update_task(cls, db: AsyncSession, data: TaskUpdateModel, user_id: int, update_by: str = '') -> dict:
        task = await TaskDao.get_by_id(db, data.task_id)
        if not task:
            raise ValueError('任务不存在')
        # 权限校验：教师只能改自己的任务，学生只能改自己的自研课题
        if task.creator_type == '0' and task.teacher_id != user_id:
            raise PermissionError('无权修改他人任务')
        if task.creator_type == '1' and task.student_id != user_id:
            raise PermissionError('无权修改他人课题')
        update_fields = data.model_dump(exclude_unset=True, exclude={'task_id'})
        for k, v in update_fields.items():
            setattr(task, k, v)
        task.update_by = update_by
        task.update_time = datetime.now()
        await TaskDao.update_task(db, task)
        return {'task_id': task.task_id}

    @classmethod
    async def delete_task(cls, db: AsyncSession, task_id: int, user_id: int) -> dict:
        task = await TaskDao.get_by_id(db, task_id)
        if not task:
            raise ValueError('任务不存在')
        # 权限校验：教师只能删自己的任务，学生只能删自己的自研课题
        if task.creator_type == '0' and task.teacher_id != user_id:
            raise PermissionError('无权删除他人任务')
        if task.creator_type == '1' and task.student_id != user_id:
            raise PermissionError('无权删除他人课题')
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
            'creator_type': task.creator_type,
            'student_id': task.student_id,
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
        """
        教师任务列表（V1.1 统一版）：
        包含教师自己创建的任务 + 所管班级学生的自研课题。
        """
        from utils.page_util import PageUtil
        from module_admin.dao.edu_dao import EduDao
        # 获取教师所管理的班级ID列表
        teacher_classes = await EduDao.get_teacher_classes(db, teacher_id)
        class_ids = [tc['class_id'] for tc in teacher_classes]
        tasks = await TaskDao.get_teacher_all_tasks(db, teacher_id, class_ids)
        rows = [cls._task_to_dict(t) for t in tasks]
        return PageUtil.get_page_obj(rows, page_num, page_size).model_dump()

    @classmethod
    async def get_student_tasks(cls, db: AsyncSession, student_id: int, class_id: int | None, page_num: int = 1, page_size: int = 10) -> dict:
        """
        学生任务列表（V1.1 统一版）：
        教师指派的任务（通过班级分配）+ 自己的自研课题。
        全部统一从 edu_task 表查询，废弃旧的 task_id=NULL 临时方案。
        """
        from utils.page_util import PageUtil
        tasks = []
        # 1. 教师指派的任务（通过班级分配）
        if class_id:
            published = await TaskDao.get_published_tasks_by_dept_ids(db, [class_id])
            for t in published:
                tasks.append(cls._task_to_dict(t, source='assigned'))
        # 2. 自己创建的自研课题（从 edu_task 表直接查询）
        self_tasks = await TaskDao.get_student_self_tasks(db, student_id)
        for t in self_tasks:
            tasks.append(cls._task_to_dict(t, source='self_study'))
        return PageUtil.get_page_obj(tasks, page_num, page_size).model_dump()

    @classmethod
    async def publish_task(cls, db: AsyncSession, task_id: int, dept_ids: list[int], teacher_id: int) -> dict:
        task = await TaskDao.get_by_id(db, task_id)
        if not task:
            raise ValueError('任务不存在')
        if task.teacher_id != teacher_id:
            raise PermissionError('无权发布他人任务')
        if task.creator_type == '1':
            raise ValueError('学生自研课题无需发布到班级')
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
            creator_type='0',
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
            'creator_type': task.creator_type,
            'student_id': task.student_id,
            'preset_scenario': task.preset_scenario,
            'deadline': str(task.deadline) if task.deadline else None,
            'status': task.status,
            'source': source,
            'create_time': str(task.create_time) if task.create_time else None,
        }
