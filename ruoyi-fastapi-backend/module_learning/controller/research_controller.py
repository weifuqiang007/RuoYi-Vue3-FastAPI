from typing import Annotated

from fastapi import Body, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_learning.entity.vo.research_vo import ResearchFrameworkModel, ResearchChapterSaveModel, ResearchChapterDraftModel, ResearchSaveModel
from module_learning.service.research_service import ResearchService
from utils.response_util import ResponseUtil

research_controller = APIRouterPro(
    prefix='/learning/research',
    order_num=36,
    tags=['学习模块-研究生成区'],
    dependencies=[PreAuthDependency()],
)


class ResearchController:

    @staticmethod
    @research_controller.post('/init/{record_id}', summary='初始化研究区')
    async def init_research(
        request: Request,
        record_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    ) -> Response:
        try:
            result = await ResearchService.init_research(query_db, record_id, current_user.user.user_id)
            return ResponseUtil.success(data=result)
        except Exception as e:
            return ResponseUtil.failure(msg=str(e))

    @staticmethod
    @research_controller.put('/save', summary='保存研究区数据')
    async def save_research(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        data: ResearchSaveModel,
    ) -> Response:
        try:
            result = await ResearchService.save(query_db, data)
            return ResponseUtil.success(data=result)
        except Exception as e:
            return ResponseUtil.failure(msg=str(e))

    @staticmethod
    @research_controller.post('/questions', summary='AI生成研究问题')
    async def generate_questions(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        research_id: int = Body(..., embed=True, description='研究ID'),
    ) -> Response:
        try:
            result = await ResearchService.generate_questions(query_db, research_id)
            return ResponseUtil.success(data=result)
        except Exception as e:
            return ResponseUtil.failure(msg=str(e))

    @staticmethod
    @research_controller.post('/questions/stream', summary='AI流式生成研究问题')
    async def generate_questions_stream(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        research_id: int = Body(..., embed=True, description='研究ID'),
    ) -> StreamingResponse:
        stream = ResearchService.generate_questions_stream(query_db, research_id)
        return StreamingResponse(content=stream, media_type='text/event-stream')

    @staticmethod
    @research_controller.post('/framework', summary='AI生成论文框架')
    async def generate_framework(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        data: ResearchFrameworkModel,
    ) -> Response:
        try:
            result = await ResearchService.generate_framework(query_db, data.research_id, data.selected_question)
            return ResponseUtil.success(data=result)
        except Exception as e:
            return ResponseUtil.failure(msg=str(e))

    @staticmethod
    @research_controller.post('/framework/stream', summary='AI流式生成论文框架')
    async def generate_framework_stream(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        data: ResearchFrameworkModel,
    ) -> StreamingResponse:
        stream = ResearchService.generate_framework_stream(query_db, data.research_id, data.selected_question)
        return StreamingResponse(content=stream, media_type='text/event-stream')

    @staticmethod
    @research_controller.put('/chapter/save', summary='保存章节')
    async def save_chapter(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        data: ResearchChapterSaveModel,
    ) -> Response:
        result = await ResearchService.save_chapter(query_db, data, current_user.user.user_id)
        return ResponseUtil.success(data=result)

    @staticmethod
    @research_controller.post('/chapter/draft', summary='AI辅助撰写章节')
    async def chapter_draft(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        data: ResearchChapterDraftModel,
    ) -> Response:
        try:
            result = await ResearchService.chapter_draft(query_db, data.research_id, data.chapter_index)
            return ResponseUtil.success(data={'content': result})
        except Exception as e:
            return ResponseUtil.failure(msg=str(e))

    @staticmethod
    @research_controller.post('/chapter/draft/stream', summary='AI流式辅助撰写章节')
    async def chapter_draft_stream(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        data: ResearchChapterDraftModel,
    ) -> StreamingResponse:
        stream = ResearchService.chapter_draft_stream(query_db, data.research_id, data.chapter_index)
        return StreamingResponse(content=stream, media_type='text/event-stream')

    @staticmethod
    @research_controller.get('/detail/{record_id}', summary='研究区完整数据')
    async def get_detail(
        request: Request,
        record_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    ) -> Response:
        result = await ResearchService.get_detail(query_db, record_id)
        if not result:
            return ResponseUtil.success(data={})
        return ResponseUtil.success(data=result)

    @staticmethod
    @research_controller.post('/references', summary='AI推荐参考文献')
    async def recommend_references(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        research_id: int = Body(..., embed=True, description='研究ID'),
    ) -> Response:
        try:
            result = await ResearchService.recommend_references(query_db, research_id)
            return ResponseUtil.success(data=result)
        except Exception as e:
            return ResponseUtil.failure(msg=str(e))

    @staticmethod
    @research_controller.post('/references/stream', summary='AI流式推荐参考文献')
    async def recommend_references_stream(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        research_id: int = Body(..., embed=True, description='研究ID'),
    ) -> StreamingResponse:
        stream = ResearchService.recommend_references_stream(query_db, research_id)
        return StreamingResponse(content=stream, media_type='text/event-stream')

    @staticmethod
    @research_controller.put('/submit', summary='提交研究成果')
    async def submit(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        record_id: int = Body(..., embed=True, description='学习记录ID'),
    ) -> Response:
        try:
            result = await ResearchService.submit(query_db, record_id, current_user.user.user_id)
            return ResponseUtil.success(data=result)
        except (ValueError, PermissionError) as e:
            return ResponseUtil.failure(msg=str(e))
