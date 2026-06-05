from typing import Annotated

from fastapi import Body, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_learning.entity.vo.evaluation_vo import EvaluationSubmitModel
from module_learning.service.evaluation_service import MonitorService, EvaluationService
from utils.response_util import ResponseUtil

monitor_controller = APIRouterPro(
    prefix='/learning/monitor',
    order_num=37,
    tags=['学习模块-教师监控'],
    dependencies=[PreAuthDependency()],
)


class MonitorController:

    @staticmethod
    @monitor_controller.get('/class/{task_id}', summary='班级进度概览')
    async def get_class_overview(
        request: Request,
        task_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    ) -> Response:
        result = await MonitorService.get_class_overview(query_db, task_id)
        return ResponseUtil.success(data=result)

    @staticmethod
    @monitor_controller.get('/student/{record_id}', summary='学生详情')
    async def get_student_detail(
        request: Request,
        record_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    ) -> Response:
        result = await MonitorService.get_student_detail(query_db, record_id)
        return ResponseUtil.success(data=result)


evaluation_controller = APIRouterPro(
    prefix='/learning/evaluation',
    order_num=38,
    tags=['学习模块-评价'],
    dependencies=[PreAuthDependency()],
)


class EvaluationController:

    @staticmethod
    @evaluation_controller.post('/submit', summary='教师提交评价')
    async def submit_evaluation(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        data: EvaluationSubmitModel,
    ) -> Response:
        try:
            result = await EvaluationService.submit(query_db, data, current_user.user.user_id)
            return ResponseUtil.success(data=result)
        except (ValueError, PermissionError) as e:
            return ResponseUtil.failure(msg=str(e))

    @staticmethod
    @evaluation_controller.get('/detail/{record_id}', summary='查看评价')
    async def get_detail(
        request: Request,
        record_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    ) -> Response:
        result = await EvaluationService.get_detail(query_db, record_id)
        if not result:
            return ResponseUtil.success(data={})
        return ResponseUtil.success(data=result)

    @staticmethod
    @evaluation_controller.put('/mark-excellent/{record_id}', summary='标记优秀案例')
    async def mark_excellent(
        request: Request,
        record_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    ) -> Response:
        try:
            result = await EvaluationService.mark_excellent(query_db, record_id, current_user.user.user_id)
            return ResponseUtil.success(data=result)
        except ValueError as e:
            return ResponseUtil.failure(msg=str(e))


case_controller = APIRouterPro(
    prefix='/learning/case',
    order_num=39,
    tags=['学习模块-优秀案例'],
    dependencies=[PreAuthDependency()],
)


class CaseController:

    @staticmethod
    @case_controller.get('/list', summary='优秀案例列表')
    async def get_cases(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    ) -> Response:
        result = await EvaluationService.get_cases(query_db)
        return ResponseUtil.success(data=result)

    @staticmethod
    @case_controller.get('/detail/{case_id}', summary='优秀案例详情')
    async def get_case_detail(
        request: Request,
        case_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    ) -> Response:
        result = await EvaluationService.get_case_detail(query_db, case_id)
        if not result:
            return ResponseUtil.failure(msg='案例不存在')
        return ResponseUtil.success(data=result)
