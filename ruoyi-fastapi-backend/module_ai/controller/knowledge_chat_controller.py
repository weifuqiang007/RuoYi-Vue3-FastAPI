"""知识对话（社会工作教学与研究助手）控制器。

复用现有认证与角色机制：PreAuthDependency 做登录校验，
RoleInterfaceAuthDependency 限定教师/管理员进入，ViewerDependency 注入知识库可见主体。
"""

from typing import Annotated

from fastapi import Path, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import RoleInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency
from common.aspect.resource_scope import ViewerDependency
from common.router import APIRouterPro
from module_ai.entity.vo.knowledge_chat_vo import (
    KbChatSessionCreateModel,
    KbChatSessionPageQueryModel,
    KbChatStreamRequestModel,
)
from module_ai.service.knowledge_chat_service import KnowledgeChatService
from module_rag.service.kb_scope_policy import KbPrincipal
from utils.response_util import ResponseUtil

knowledge_chat_controller = APIRouterPro(
    prefix='/ai/knowledge-chat',
    order_num=20,
    tags=['AI管理-知识对话'],
    dependencies=[
        PreAuthDependency(),
        RoleInterfaceAuthDependency(['admin', 'teacher']),
    ],
)


class KnowledgeChatController:
    """知识对话控制器 —— 会话、消息、引用与知识库范围"""

    # ── 知识库范围 ────────────────────────────────────────
    @staticmethod
    @knowledge_chat_controller.get('/knowledge-bases', summary='获取授权知识库列表')
    async def get_knowledge_bases(
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        principal: KbPrincipal = ViewerDependency('rag.knowledge_base'),
    ) -> Response:
        kb_list = await KnowledgeChatService.list_accessible_knowledge_bases(query_db, principal)
        return ResponseUtil.success(data=kb_list)

    # ── 会话 ──────────────────────────────────────────────
    @staticmethod
    @knowledge_chat_controller.post('/sessions', summary='创建知识对话会话')
    async def create_session(
        data: KbChatSessionCreateModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        principal: KbPrincipal = ViewerDependency('rag.knowledge_base'),
    ) -> Response:
        kb_ids = KnowledgeChatService.parse_kb_ids(data.kb_ids)
        session = await KnowledgeChatService.create_scoped_session(query_db, principal, kb_ids)
        return ResponseUtil.success(data=KnowledgeChatService.session_dict(session))

    @staticmethod
    @knowledge_chat_controller.get('/sessions', summary='获取知识对话会话列表')
    async def list_sessions(
        page_query: Annotated[KbChatSessionPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        principal: KbPrincipal = ViewerDependency('rag.knowledge_base'),
    ) -> Response:
        sessions, total = await KnowledgeChatService.list_sessions(
            query_db, principal.user_id, page_query.page_num, page_query.page_size
        )
        return ResponseUtil.success(data={'total': total, 'items': sessions})

    # ── 消息历史 ──────────────────────────────────────────
    @staticmethod
    @knowledge_chat_controller.get('/sessions/{session_id}/messages', summary='获取会话消息历史')
    async def list_messages(
        session_id: Annotated[str, Path(description='会话ID')],
        page_query: Annotated[KbChatSessionPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        principal: KbPrincipal = ViewerDependency('rag.knowledge_base'),
    ) -> Response:
        messages, total = await KnowledgeChatService.list_messages(
            query_db, principal.user_id, session_id, page_query.page_num, page_query.page_size
        )
        return ResponseUtil.success(data={'total': total, 'items': messages})

    # ── 流式发送 ──────────────────────────────────────────
    @staticmethod
    @knowledge_chat_controller.post(
        '/sessions/{session_id}/messages/stream',
        summary='流式发送知识对话消息',
        description='NDJSON 流式返回，type 字段区分 meta/status/delta/citations/done/error/duplicate',
        response_class=StreamingResponse,
    )
    async def stream_message(
        session_id: Annotated[str, Path(description='会话ID')],
        data: KbChatStreamRequestModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        principal: KbPrincipal = ViewerDependency('rag.knowledge_base'),
    ) -> StreamingResponse:
        data.session_id = session_id
        stream = KnowledgeChatService.stream_answer(query_db, principal.user_id, principal, data)
        return StreamingResponse(content=stream, media_type='text/event-stream')

    # ── 引用详情 ──────────────────────────────────────────
    @staticmethod
    @knowledge_chat_controller.get(
        '/messages/{message_id}/citations/{citation_no}', summary='获取引用详情（含原文，二次鉴权）'
    )
    async def get_citation(
        message_id: Annotated[int, Path(description='消息ID')],
        citation_no: Annotated[int, Path(description='引用编号')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        principal: KbPrincipal = ViewerDependency('rag.knowledge_base'),
    ) -> Response:
        citation = await KnowledgeChatService.get_citation(query_db, principal, message_id, citation_no)
        return ResponseUtil.success(data=citation)
