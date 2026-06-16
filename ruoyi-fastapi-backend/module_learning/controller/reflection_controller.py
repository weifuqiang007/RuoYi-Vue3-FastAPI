from typing import Annotated

from fastapi import Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from module_admin.entity.vo.user_vo import CurrentUserModel
from fastapi import Body

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
    @reflection_controller.put('/save', summary='更新反思文本')
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
    @reflection_controller.post('/questions/stream', summary='AI流式生成理论指导')
    async def generate_questions_stream(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        data: ReflectionQuestionModel,
    ) -> StreamingResponse:
        """流式生成理论指导：逐字回显可读内容，结束后返回结构化结果并落库"""
        stream = ReflectionService.generate_questions_stream(query_db, data.reflection_id)
        return StreamingResponse(content=stream, media_type='text/event-stream')

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
    @reflection_controller.put('/confirm', summary='确认反思完成')
    async def confirm(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        record_id: int = Body(..., embed=True, description='学习记录ID'),
    ) -> Response:
        try:
            result = await ReflectionService.confirm(query_db, record_id, current_user.user.user_id)
            return ResponseUtil.success(data=result)
        except ValueError as e:
            return ResponseUtil.failure(msg=str(e))

    @staticmethod
    @reflection_controller.get('/list/{record_id}', summary='获取学习记录下所有反思（按决策分Tab）')
    async def get_list(
        request: Request,
        record_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    ) -> Response:
        result = await ReflectionService.get_list_by_record(query_db, record_id)
        return ResponseUtil.success(data=result)

    @staticmethod
    @reflection_controller.get('/detail-by-decision/{decision_id}', summary='获取单个决策的反思详情')
    async def get_detail_by_decision(
        request: Request,
        decision_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    ) -> Response:
        result = await ReflectionService.get_by_decision(query_db, decision_id)
        if not result:
            return ResponseUtil.success(data={})
        return ResponseUtil.success(data=result)
