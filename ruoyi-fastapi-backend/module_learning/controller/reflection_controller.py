from typing import Annotated

from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_learning.entity.vo.reflection_vo import ReflectionSaveModel, ReflectionQuestionModel
from module_learning.service.reflection_service import ReflectionService
from utils.response_util import ResponseUtil

reflection_controller = APIRouterPro(
    prefix='/learning/reflection',
    order_num=35,
    tags=['学习模块-反思区'],
    dependencies=[PreAuthDependency()],
)


class ReflectionController:

    @staticmethod
    @reflection_controller.post('/save', summary='保存反思文本')
    async def save_reflection(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        data: ReflectionSaveModel,
    ) -> Response:
        try:
            result = await ReflectionService.save(query_db, data, current_user.user.user_id)
            return ResponseUtil.success(data=result)
        except Exception as e:
            return ResponseUtil.failure(msg=str(e))

    @staticmethod
    @reflection_controller.post('/questions', summary='AI生成结构化提问')
    async def generate_questions(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        data: ReflectionQuestionModel,
    ) -> Response:
        try:
            result = await ReflectionService.generate_questions(query_db, data.reflection_id)
            return ResponseUtil.success(data=result)
        except Exception as e:
            return ResponseUtil.failure(msg=str(e))

    @staticmethod
    @reflection_controller.get('/depth/{reflection_id}', summary='获取深度评估')
    async def get_depth(
        request: Request,
        reflection_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    ) -> Response:
        try:
            result = await ReflectionService.get_depth(query_db, reflection_id)
            return ResponseUtil.success(data=result)
        except Exception as e:
            return ResponseUtil.failure(msg=str(e))

    @staticmethod
    @reflection_controller.get('/depth-history/{reflection_id}', summary='深度变化曲线')
    async def get_depth_history(
        request: Request,
        reflection_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    ) -> Response:
        result = await ReflectionService.get_depth_history(query_db, reflection_id)
        return ResponseUtil.success(data=result)

    @staticmethod
    @reflection_controller.get('/detail/{record_id}', summary='反思区完整数据')
    async def get_detail(
        request: Request,
        record_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    ) -> Response:
        result = await ReflectionService.get_detail(query_db, record_id)
        if not result:
            return ResponseUtil.success(data={})
        return ResponseUtil.success(data=result)
