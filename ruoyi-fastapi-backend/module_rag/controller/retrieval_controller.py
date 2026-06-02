# module_rag/controller/retrieval_controller.py
from typing import Annotated
from fastapi import Body
from sqlalchemy.ext.asyncio import AsyncSession
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import PreAuthDependency
from common.router import APIRouterPro
from module_rag.entity.vo.retrieval_vo import RetrievalRequestModel
from module_rag.service.embedding_service import EmbeddingService
from module_rag.service.retrieval_service import RetrievalService
from utils.response_util import ResponseUtil

retrieval_controller = APIRouterPro(
    prefix='/rag/retrieval', order_num=22, tags=['RAG管理-检索'], dependencies=[PreAuthDependency()]
)


@retrieval_controller.post('/search', summary='混合检索')
async def search(
    data: RetrievalRequestModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
):
    # 1. 向量化查询
    query_embedding = await EmbeddingService.embed_single(data.query)

    # 2. 混合检索
    results = await RetrievalService.hybrid_search(
        db=query_db,
        query_text=data.query,
        query_embedding=query_embedding,
        kb_ids=data.kb_ids,
        top_k=data.top_k,
    )

    return ResponseUtil.success(data=[{
        "chunk_id": r["chunk_id"],
        "doc_id": r["doc_id"],
        "content": r["content"][:200],
        "score": float(r.get("score", 0)),
    } for r in results])