from typing import Annotated

from fastapi import Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from common.vo import DataResponseModel, PageModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_learning.entity.vo.task_vo import TaskCreateModel, TaskUpdateModel, TaskPublishModel
from module_learning.service.task_service import TaskService
from utils.response_util import ResponseUtil

task_controller = APIRouterPro(
    prefix='/learning/task',
    order_num=31,
    tags=['学习模块-教学任务'],
    dependencies=[PreAuthDependency()],
)


class TaskController:

    @staticmethod
    @task_controller.get('/list', summary='教师任务列表')
    async def get_teacher_tasks(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        page_num: int = 1,
        page_size: int = 10,
    ) -> Response:
        result = await TaskService.get_teacher_tasks(query_db, current_user.user.user_id, page_num, page_size)
        return ResponseUtil.success(data=result)

    @staticmethod
    @task_controller.post('/create', summary='创建任务')
    async def create_task(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        data: TaskCreateModel,
    ) -> Response:
        result = await TaskService.create_task(
            query_db, data,
            teacher_id=current_user.user.user_id,
            create_by=current_user.user.user_name or '',
        )
        return ResponseUtil.success(data=result)

    @staticmethod
    @task_controller.put('/update', summary='编辑任务')
    async def update_task(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        data: TaskUpdateModel,
    ) -> Response:
        result = await TaskService.update_task(
            query_db, data,
            teacher_id=current_user.user.user_id,
            update_by=current_user.user.user_name or '',
        )
        return ResponseUtil.success(data=result)

    @staticmethod
    @task_controller.delete('/delete/{task_id}', summary='删除任务')
    async def delete_task(
        request: Request,
        task_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    ) -> Response:
        result = await TaskService.delete_task(query_db, task_id, current_user.user.user_id)
        return ResponseUtil.success(data=result)

    @staticmethod
    @task_controller.put('/publish/{task_id}', summary='发布任务到班级')
    async def publish_task(
        request: Request,
        task_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        data: TaskPublishModel,
    ) -> Response:
        result = await TaskService.publish_task(query_db, task_id, data.dept_ids, current_user.user.user_id)
        return ResponseUtil.success(data=result)

    @staticmethod
    @task_controller.post('/copy/{task_id}', summary='复制任务')
    async def copy_task(
        request: Request,
        task_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    ) -> Response:
        result = await TaskService.copy_task(
            query_db, task_id,
            teacher_id=current_user.user.user_id,
            create_by=current_user.user.user_name or '',
        )
        return ResponseUtil.success(data=result)

    @staticmethod
    @task_controller.get('/student/list', summary='学生任务列表')
    async def get_student_tasks(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        page_num: int = 1,
        page_size: int = 10,
    ) -> Response:
        # 获取学生班级ID
        from module_admin.dao.edu_dao import EduDao
        profile = await EduDao.get_student_profile_by_user_id(query_db, current_user.user.user_id)
        class_id = profile.class_id if profile else None
        result = await TaskService.get_student_tasks(query_db, current_user.user.user_id, class_id, page_num, page_size)
        return ResponseUtil.success(data=result)

    @staticmethod
    @task_controller.get('/detail/{task_id}', summary='任务详情')
    async def get_task_detail(
        request: Request,
        task_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    ) -> Response:
        result = await TaskService.get_task_detail(query_db, task_id)
        if not result:
            return ResponseUtil.failure(msg='任务不存在')
        return ResponseUtil.success(data=result)
