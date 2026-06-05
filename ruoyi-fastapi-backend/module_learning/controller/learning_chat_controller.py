# module_learning/controller/learning_chat_controller.py
from typing import Annotated

from fastapi import Body
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from module_admin.entity.vo.user_vo import CurrentUserModel
from utils.response_util import ResponseUtil

learning_chat_controller = APIRouterPro(
    prefix='/learning/chat',
    order_num=30,
    tags=['学习模块-AI对话'],
    dependencies=[PreAuthDependency()],
)

class LearningChatController:

    @staticmethod
    @learning_chat_controller.post('/send', summary='流式对话')
    async def send_chat(
            query_db: Annotated[AsyncSession, DBSessionDependency()],
            current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
            message: str = Body(..., embed=True, description='用户消息'),
            model_id: int = Body(..., embed=True, description="模型Id"),
            session_id: str = Body(None, embed=True, description='会话ID')
    ):
        """流式对话接口，返回SSE流"""
        user_id = current_user.user.user_id if current_user and current_user.user else 1
        # from module_learning.service.llm_call import call_llm_stream
        from module_learning.service.llm_call import AiCall

        chat_stream = AiCall.call_llm_stream(
            query_db=query_db,
            model_id=model_id,
            prompt=message,
            session_id=session_id,
            user_id=str(user_id)
        )
        return StreamingResponse(content=chat_stream, media_type='text/event-stream')

    @staticmethod
    @learning_chat_controller.post('/analyze', summary='非流式分析')
    async def analyze(
            query_db: Annotated[AsyncSession, DBSessionDependency()],
            prompt: str = Body(..., embed=True, description='分析提示词'),
            model_id: int = Body(..., embed=True, description='模型ID'),
    ):
        """非流式分析接口，返回完整文本结果。"""
        from module_learning.service.llm_call import AiCall
        result = await AiCall.call_llm_non_stream(query_db, model_id, prompt)
        return ResponseUtil.success(data={'content': result})


    @staticmethod
    @learning_chat_controller.post('/analyze-json', summary='非流式 JSON 分析')
    async def analyze_json(
            query_db: Annotated[AsyncSession, DBSessionDependency()],
            prompt: str = Body(..., embed=True, description='分析提示词'),
            model_id: int = Body(..., embed=True, description='模型ID'),
    ):
        """非流式分析接口，返回解析后的 JSON dict。"""
        from module_learning.service.llm_call import AiCall
        result = await AiCall.call_llm_json(query_db, model_id, prompt)
        return ResponseUtil.success(data=result)