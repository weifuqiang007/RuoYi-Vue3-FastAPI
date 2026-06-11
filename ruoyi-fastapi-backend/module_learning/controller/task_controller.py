from typing import Annotated

from fastapi import Query, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from common.vo import DataResponseModel, PageModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_learning.entity.vo.task_vo import TaskCreateModel, TaskUpdateModel, TaskPublishModel, StudentTaskCreateModel, TaskListQueryModel
from module_learning.service.task_service import TaskService
from utils.response_util import ResponseUtil


from module_admin.dao.edu_dao import EduDao

task_controller = APIRouterPro(
    prefix='/learning/task',
    order_num=31,
    tags=['学习模块-教学任务'],
    dependencies=[PreAuthDependency()],
)


class TaskController:

    @staticmethod
    @task_controller.get('/list', summary='教师任务列表（含所管班级学生自研课题）')
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
    @task_controller.post('/create', summary='教师创建教学任务')
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
    @task_controller.post('/student/create', summary='学生、老师自建自研课题')
    async def create_student_task(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        data: StudentTaskCreateModel,
    ) -> Response:
        # 身份鉴权：根据 current_user.roles 判断角色，service 层自动设置正确的创建者字段
        # student → student_id  teacher → teacher_id  admin → student_id
        # 所有角色都只能为自己创建，user_id 来自 JWT 不可伪造
        result = await TaskService.create_task_by_user(
            query_db,
            data,
            user_id=current_user.user.user_id,
            roles=current_user.roles,
            create_by=current_user.user.user_name or '',
        )
        return ResponseUtil.success(data=result)

    @staticmethod
    @task_controller.put('/update', summary='编辑任务/课题')
    async def update_task(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        data: TaskUpdateModel,
    ) -> Response:
        result = await TaskService.update_task(
            query_db, data,
            user_id=current_user.user.user_id,
            update_by=current_user.user.user_name or '',
        )
        return ResponseUtil.success(data=result)

    @staticmethod
    @task_controller.delete('/delete/{task_id}', summary='删除任务/课题')
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
    @task_controller.get('/student/list', summary='学生任务列表（指派+自研）')
    async def get_student_tasks(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        query: Annotated[TaskListQueryModel, Query()],
    ) -> Response:
        # 分页参数从模型中取出
        page_num = query.page_num
        page_size = query.page_size
        # 只传有值的过滤条件
        filters = query.model_dump(exclude_none=True, exclude={'page_num', 'page_size'})

        profile = await EduDao.get_student_profile_by_user_id(query_db, current_user.user.user_id)
        class_id = profile.class_id if profile else None
        result = await TaskService.get_student_tasks(
            query_db, current_user.user.user_id, class_id,
            roles=current_user.roles, filters=filters or None,
            page_num=page_num, page_size=page_size,
        )
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
