from typing import Annotated

from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_learning.entity.vo.decision_vo import DecisionSaveModel, DecisionEthicsModel
from module_learning.service.decision_service import DecisionService
from utils.response_util import ResponseUtil

decision_controller = APIRouterPro(
    prefix='/learning/decision',
    order_num=34,
    tags=['学习模块-决策区'],
    dependencies=[PreAuthDependency()],
)


class DecisionController:

    @staticmethod
    @decision_controller.post('/save', summary='保存决策记录')
    @decision_controller.put('/save', summary="更新决策记录")
    async def save_decision(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        data: DecisionSaveModel,
    ) -> Response:
        result = await DecisionService.save(query_db, data, current_user.user.user_id)
        return ResponseUtil.success(data=result)

    @staticmethod
    @decision_controller.post('/ethics-analyze', summary='AI伦理分析')
    async def ethics_analyze(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        data: DecisionEthicsModel,
    ) -> Response:
        try:
            result = await DecisionService.ethics_analyze(query_db, data.decision_id)
            return ResponseUtil.success(data=result)
        except ValueError as e:
            return ResponseUtil.failure(msg=str(e))
        except Exception as e:
            import logging
            logging.error('[决策区] ethics-analyze 接口异常: %s', e, exc_info=True)
            return ResponseUtil.failure(msg='AI分析服务暂时不可用，请稍后重试')

    @staticmethod
    @decision_controller.get('/list/{record_id}', summary='获取决策记录列表')
    async def get_decision_list(
        request: Request,
        record_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    ) -> Response:
        result = await DecisionService.get_list(query_db, record_id)
        return ResponseUtil.success(data=result)

    @staticmethod
    @decision_controller.put('/confirm/{record_id}', summary='确认决策完成')
    async def confirm(
        request: Request,
        record_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    ) -> Response:
        try:
            result = await DecisionService.confirm(query_db, record_id)
            return ResponseUtil.success(data=result)
        except ValueError as e:
            return ResponseUtil.failure(msg=str(e))
