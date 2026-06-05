from typing import Annotated

from fastapi import Body, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_learning.entity.vo.scenario_vo import ScenarioSaveModel, ScenarioAnalyzeModel, ScenarioFollowupModel
from module_learning.service.scenario_service import ScenarioService
from utils.response_util import ResponseUtil

scenario_controller = APIRouterPro(
    prefix='/learning/scenario',
    order_num=33,
    tags=['学习模块-情境区'],
    dependencies=[PreAuthDependency()],
)


class ScenarioController:

    @staticmethod
    @scenario_controller.post('/save', summary='保存情境描述')
    async def save_scenario(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        data: ScenarioSaveModel,
    ) -> Response:
        result = await ScenarioService.save(query_db, data, current_user.user.user_id)
        return ResponseUtil.success(data=result)

    @staticmethod
    @scenario_controller.post('/analyze', summary='AI分析情境')
    async def analyze_scenario(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        data: ScenarioAnalyzeModel,
    ) -> Response:
        try:
            result = await ScenarioService.analyze(query_db, data.scenario_id)
            return ResponseUtil.success(data=result)
        except Exception as e:
            return ResponseUtil.failure(msg=str(e))

    @staticmethod
    @scenario_controller.post('/followup', summary='AI追问')
    async def followup(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        data: ScenarioFollowupModel,
    ) -> Response:
        try:
            result = await ScenarioService.followup(query_db, data.scenario_id, data.user_message)
            return ResponseUtil.success(data={'content': result})
        except Exception as e:
            return ResponseUtil.failure(msg=str(e))

    @staticmethod
    @scenario_controller.put('/confirm', summary='确认情境完成')
    async def confirm(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        record_id: int = Body(..., embed=True, description='学习记录ID'),
    ) -> Response:
        try:
            result = await ScenarioService.confirm(query_db, record_id, current_user.user.user_id)
            return ResponseUtil.success(data=result)
        except ValueError as e:
            return ResponseUtil.failure(msg=str(e))

    @staticmethod
    @scenario_controller.get('/detail/{record_id}', summary='获取情境区数据')
    async def get_detail(
        request: Request,
        record_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    ) -> Response:
        result = await ScenarioService.get_detail(query_db, record_id)
        if not result:
            return ResponseUtil.success(data={})
        return ResponseUtil.success(data=result)
