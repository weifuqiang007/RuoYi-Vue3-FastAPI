import json
from typing import Annotated

from fastapi import Body, Query, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_learning.entity.vo.review_vo import AiCommentScopeModel, ReviewListQueryModel, TeacherCommentModel
from module_learning.service.review_service import ReviewService
from utils.response_util import ResponseUtil

review_controller = APIRouterPro(
    prefix='/learning/review',
    order_num=40,
    tags=['学习模块-反思批阅'],
    dependencies=[PreAuthDependency()],
)


class ReviewController:
    """教师反思批阅：查看学生反思研究成果、AI(裁判模型)评论、老师针对结论点评"""

    @staticmethod
    @review_controller.get('/records', summary='教师批阅列表（按班级/任务/学生/状态筛选）')
    async def get_records(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        query: Annotated[ReviewListQueryModel, Query()],
    ) -> Response:
        page_num = query.page_num
        page_size = query.page_size
        filters = query.model_dump(exclude_none=True, exclude={'page_num', 'page_size'})
        result = await ReviewService.get_records(
            query_db, current_user,
            filters=filters or None,
            page_num=page_num, page_size=page_size,
        )
        return ResponseUtil.success(data=result)

    @staticmethod
    @review_controller.get('/detail/{record_id}', summary='批阅详情（四区+反思列表+批阅数据）')
    async def get_detail(
        request: Request,
        record_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    ) -> Response:
        try:
            result = await ReviewService.get_detail(query_db, record_id, current_user)
            if not result:
                return ResponseUtil.failure(msg='学习记录不存在')
            return ResponseUtil.success(data=result)
        except PermissionError as e:
            return ResponseUtil.failure(msg=str(e))

    @staticmethod
    @review_controller.post('/ai-comment/{record_id}', summary='生成/重新生成AI评论（裁判模型，超时约30-60秒）')
    async def generate_ai_comment(
        request: Request,
        record_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        data: AiCommentScopeModel = AiCommentScopeModel(),
    ) -> Response:
        try:
            result = await ReviewService.generate_ai_comment(
                query_db, record_id, scope=data.scope, current_user=current_user,
            )
            return ResponseUtil.success(data=result)
        except (ValueError, PermissionError) as e:
            return ResponseUtil.failure(msg=str(e))

    @staticmethod
    @review_controller.post('/ai-comment/stream/{record_id}', summary='流式生成AI评论（SSE）')
    async def generate_ai_comment_stream(
        request: Request,
        record_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        data: AiCommentScopeModel = AiCommentScopeModel(),
    ) -> StreamingResponse:
        """流式生成AI评论。当前为「状态消息 + 最终JSON」的SSE包装，复用 generate_ai_comment；后续可改为 call_llm_stream 逐字回显。"""
        async def event_stream():
            yield json.dumps(
                {'type': 'status', 'message': '裁判模型正在分析学生反思研究，请稍候（约30-60秒）...'},
                ensure_ascii=False,
            ) + '\n'
            try:
                result = await ReviewService.generate_ai_comment(
                    query_db, record_id, scope=data.scope, current_user=current_user,
                )
                yield json.dumps({'type': 'result', 'data': result}, ensure_ascii=False, default=str) + '\n'
            except (ValueError, PermissionError) as e:
                yield json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False) + '\n'

        return StreamingResponse(content=event_stream(), media_type='text/event-stream')

    @staticmethod
    @review_controller.put('/comment/{record_id}', summary='老师提交/更新点评（评分+评语）')
    async def submit_comment(
        request: Request,
        record_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        data: TeacherCommentModel,
    ) -> Response:
        try:
            result = await ReviewService.submit_comment(query_db, record_id, data, current_user)
            return ResponseUtil.success(data=result)
        except (ValueError, PermissionError) as e:
            return ResponseUtil.failure(msg=str(e))

    @staticmethod
    @review_controller.get('/ai-comment-history/{record_id}', summary='AI评论历史版本')
    async def get_ai_comment_history(
        request: Request,
        record_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    ) -> Response:
        try:
            result = await ReviewService.get_ai_comment_history(query_db, record_id, current_user)
            return ResponseUtil.success(data=result)
        except PermissionError as e:
            return ResponseUtil.failure(msg=str(e))
