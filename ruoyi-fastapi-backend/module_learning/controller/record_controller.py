from typing import Annotated

from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_learning.service.record_service import RecordService
from utils.response_util import ResponseUtil

record_controller = APIRouterPro(
    prefix='/learning/record',
    order_num=32,
    tags=['学习模块-学习记录'],
    dependencies=[PreAuthDependency()],
)


class RecordController:

    @staticmethod
    @record_controller.post('/start/{task_id}', summary='开始任务')
    async def start_task(
        request: Request,
        task_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    ) -> Response:
        result = await RecordService.start_task(query_db, task_id, current_user.user.user_id)
        return ResponseUtil.success(data=result)

    @staticmethod
    @record_controller.post('/create-self', summary='创建自研课题')
    async def create_self_study(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    ) -> Response:
        result = await RecordService.create_self_study(query_db, current_user.user.user_id)
        return ResponseUtil.success(data=result)

    @staticmethod
    @record_controller.get('/my', summary='我的学习记录')
    async def get_my_records(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        page_num: int = 1,
        page_size: int = 10,
    ) -> Response:
        result = await RecordService.get_my_records(query_db, current_user.user.user_id, page_num, page_size)
        return ResponseUtil.success(data=result)

    @staticmethod
    @record_controller.get('/detail/{record_id}', summary='记录详情')
    async def get_detail(
        request: Request,
        record_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    ) -> Response:
        result = await RecordService.get_detail(query_db, record_id)
        if not result:
            return ResponseUtil.failure(msg='记录不存在')
        return ResponseUtil.success(data=result)

    @staticmethod
    @record_controller.put('/advance/{record_id}', summary='推进到下一区')
    async def advance_stage(
        request: Request,
        record_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    ) -> Response:
        try:
            result = await RecordService.advance_stage(query_db, record_id, current_user.user.user_id)
            return ResponseUtil.success(data=result)
        except (ValueError, PermissionError) as e:
            return ResponseUtil.failure(msg=str(e))
