# module_rag/controller/knowledge_base_controller.py
from typing import Annotated
from fastapi import Body, Path
from sqlalchemy.ext.asyncio import AsyncSession
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_rag.entity.vo.knowledge_base_vo import KnowledgeBaseCreateModel, KnowledgeBaseUpdateModel
from module_rag.service.knowledge_base_service import KnowledgeBaseService
from utils.response_util import ResponseUtil

knowledge_base_controller = APIRouterPro(
    prefix='/rag/kb', order_num=20, tags=['RAG管理-知识库'], dependencies=[PreAuthDependency()]
)


@knowledge_base_controller.post('', summary='创建知识库')
async def create_kb(
    data: KnowledgeBaseCreateModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: CurrentUserModel = CurrentUserDependency(),
):
    kb = await KnowledgeBaseService.create(query_db, data, current_user.user.user_id)
    return ResponseUtil.success(data={"kb_id": kb.kb_id})


@knowledge_base_controller.get('/list', summary='获取知识库列表')
async def get_kb_list(
    query_db: Annotated[AsyncSession, DBSessionDependency()],
):
    kb_list = await KnowledgeBaseService.get_list(query_db)
    return ResponseUtil.success(data=[{
        "kb_id": kb.kb_id,
        "kb_name": kb.kb_name,
        "kb_desc": kb.kb_desc,
        "doc_count": kb.doc_count,
        "create_time": str(kb.create_time),
    } for kb in kb_list])