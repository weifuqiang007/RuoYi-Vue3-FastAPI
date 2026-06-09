from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from module_learning.dao.task_dao import TaskDao
from module_learning.entity.do.task_do import EduTask
from module_learning.entity.vo.task_vo import TaskCreateModel, TaskUpdateModel, StudentTaskCreateModel
from utils.page_util import PageUtil
from module_admin.dao.edu_dao import EduDao



class TaskService:

    @classmethod
    async def create_task_by_user(cls, db: AsyncSession, data: StudentTaskCreateModel,
                                  user_id: int, roles: list, create_by: str = '') -> dict:
        """
        统一自研课题创建入口：根据用户角色自动设置创建者字段。
        - student → creator_type='1', student_id=user_id（通过 /student/list 查看）
        - teacher → creator_type='1', teacher_id=user_id（通过 /list 查看，匹配 teacher_id 条件）
        - admin   → creator_type='1', student_id=user_id（通过 /student/list 查看）
        """
        role_keys = roles or []
        is_teacher = 'teacher' in role_keys

        task = EduTask(
            task_name=data.task_name,
            task_description=data.task_description,
            creator_type= '0' if is_teacher else '1',
            # 教师：通过 teacher_id 字段记录，这样 get_teacher_all_tasks 的 teacher_id==teacher_id 条件能匹配到
            # 学生/管理员：通过 student_id 字段记录，这样 get_student_self_tasks 能匹配到
            teacher_id=user_id if is_teacher else None,
            student_id=user_id if not is_teacher else None,
            status='1',  # 自研课题直接发布
            create_by=create_by,
        )
        task = await TaskDao.create_task(db, task)
        return {'task_id': task.task_id}

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
        # 如果创建时就指定了班级，直接分配
        if data.dept_ids:
            await TaskDao.assign_classes(db, task.task_id, data.dept_ids)
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
        # 更新任务字段（排除 task_id 和 dept_ids）
        update_fields = data.model_dump(exclude_unset=True, exclude={'task_id', 'dept_ids'})
        for k, v in update_fields.items():
            setattr(task, k, v)
        task.update_by = update_by
        task.update_time = datetime.now()
        await TaskDao.update_task(db, task)
        # 如果传了 dept_ids，同步更新班级分配（仅教师任务）
        if data.dept_ids is not None and task.creator_type == '0':
            await TaskDao.assign_classes(db, task.task_id, data.dept_ids)
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
        包含教师自己创建的任务 + 所管班级学生的自研课题，每个任务携带分配的班级信息。
        """

        teacher_classes = await EduDao.get_teacher_classes(db, teacher_id)
        class_ids = [tc['class_id'] for tc in teacher_classes]
        rows_data = await TaskDao.get_teacher_all_tasks(db, teacher_id, class_ids)
        # 收集所有 task_id，批量查班级
        task_ids = [row[0].task_id for row in rows_data]
        class_mapping = await TaskDao.get_assigned_classes_batch(db, task_ids)
        rows = [
            cls._task_to_dict(
                row[0], teacher_name=row[1], student_name=row[2],
                assigned_classes=class_mapping.get(row[0].task_id, [])
            )
            for row in rows_data
        ]
        return PageUtil.get_page_obj(rows, page_num, page_size).model_dump()

    @classmethod
    async def get_student_tasks(cls, db: AsyncSession, student_id: int, class_id: int | None,
                                roles: list | None = None, page_num: int = 1, page_size: int = 10) -> dict:
        """
        学生任务列表（V1.1 统一版）：
        - admin：看到所有任务（教师任务 + 学生自研课题）
        - 学生：教师指派的任务（通过班级分配）+ 自己的自研课题
        """
        from utils.page_util import PageUtil
        role_keys = roles or []
        tasks = []

        if 'admin' in role_keys:
            # admin 能看到所有任务
            rows_data = await TaskDao.get_all_tasks_for_admin(db)
            task_ids = [row[0].task_id for row in rows_data]
            class_mapping = await TaskDao.get_assigned_classes_batch(db, task_ids)
            for row in rows_data:
                task = row[0]
                source = 'self_study' if task.creator_type == '1' else 'teacher'
                tasks.append(cls._task_to_dict(
                    task, source=source,
                    teacher_name=row[1], student_name=row[2],
                    assigned_classes=class_mapping.get(task.task_id, []),
                ))
        else:
            # 1. 教师指派的任务
            if class_id:
                published = await TaskDao.get_published_tasks_by_dept_ids(db, [class_id])
                for t in published:
                    tasks.append(cls._task_to_dict(t, source='assigned'))
            # 2. 自己的自研课题
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
    def _task_to_dict(cls, task: EduTask, source: str = 'teacher',
                      teacher_name: str | None = None, student_name: str | None = None,
                      assigned_classes: list | None = None) -> dict:
        return {
            'task_id': task.task_id,
            'task_name': task.task_name,
            'task_description': task.task_description,
            'teacher_id': task.teacher_id,
            'teacher_name': teacher_name,
            'creator_type': task.creator_type,
            'student_id': task.student_id,
            'student_name': student_name,
            'preset_scenario': task.preset_scenario,
            'deadline': str(task.deadline) if task.deadline else None,
            'status': task.status,
            'source': source,
            'assigned_classes': assigned_classes or [],
            'create_time': str(task.create_time) if task.create_time else None,
        }
