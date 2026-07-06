# module_rag/controller/retrieval_controller.py
from typing import Annotated
from fastapi import Body
from sqlalchemy.ext.asyncio import AsyncSession
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import RoleInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency
from common.aspect.resource_scope import ViewerDependency
from common.router import APIRouterPro
from module_rag.entity.vo.retrieval_vo import RetrievalRequestModel
from module_rag.service.embedding_service import EmbeddingService
from module_rag.service.kb_scope_policy import KbPrincipal
from module_rag.service.knowledge_base_service import KnowledgeBaseService
from module_rag.service.retrieval_service import RetrievalService
from utils.response_util import ResponseUtil

# ──────────────────────────────────────────────
# 路由定义
# 角色校验通过路由级依赖实现 AOP 效果，
# 所有注册在该路由下的接口自动生效，无需手动调用 check_role
# ──────────────────────────────────────────────
retrieval_controller = APIRouterPro(
    prefix='/rag/retrieval',
    order_num=22,
    tags=['RAG管理-检索'],
    dependencies=[
        PreAuthDependency(),
        # 学生有个人级知识库，检索须对学生放开
        RoleInterfaceAuthDependency(['admin', 'teacher', 'student']),
    ],
)


class RetrievalController:

    @staticmethod
    @retrieval_controller.post('/search', summary='混合检索')
    async def search(
        data: RetrievalRequestModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        principal: KbPrincipal = ViewerDependency('rag.knowledge_base'),
    ):
        # 0. 越权防护：只对当前主体有权访问的知识库检索（设计方案 §4.6）
        allowed_ids = await KnowledgeBaseService.filter_accessible_ids(query_db, data.kb_ids, principal)
        if not allowed_ids:
            return ResponseUtil.success(data=[])

        # 1. 向量化查询
        query_embedding = await EmbeddingService.embed_single(data.query)

        # 2. 混合检索（仅限有权 kb_ids）
        results = await RetrievalService.hybrid_search(
            db=query_db,
            query_text=data.query,
            query_embedding=query_embedding,
            kb_ids=allowed_ids,
            top_k=data.top_k,
        )

        return ResponseUtil.success(data=[{
            "chunk_id": r["chunk_id"],
            "doc_id": r["doc_id"],
            "content": r["content"][:200],
            "score": float(r.get("score", 0)),
        } for r in results])
