from typing import Annotated

from fastapi import Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_learning.service.activity_service import ActivityService
from utils.response_util import ResponseUtil

# 首页动态：登录后访问，挂 PreAuthDependency()
activity_controller = APIRouterPro(
    prefix='/learning/activity',
    order_num=5,
    tags=['学习模块-首页动态'],
    dependencies=[PreAuthDependency()],
)


@activity_controller.get('/recent', summary='获取最近操作动态')
async def get_recent_activities(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    limit: Annotated[int, Query(description='返回条数，默认20', ge=1, le=50)] = 20,
) -> Response:
    data = await ActivityService.get_recent_activities(query_db, request, limit=limit)
    return ResponseUtil.success(data=data)


@activity_controller.get('/user-card', summary='获取用户名片（动态墙人名点击）')
async def get_user_card(
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    user_id: Annotated[int, Query(description='用户ID', ge=1)],
) -> Response:
    data = await ActivityService.get_user_card(query_db, user_id)
    return ResponseUtil.success(data=data)


@activity_controller.get('/check-task-access', summary='校验当前用户对任务的数据权限，返回是否可访问及跳转路径')
async def check_task_access(
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    task_id: Annotated[int, Query(description='任务ID', ge=1)],
) -> Response:
    data = await ActivityService.check_task_access(query_db, current_user, task_id)
    return ResponseUtil.success(data=data)
