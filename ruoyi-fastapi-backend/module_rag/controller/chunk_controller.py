# module_rag/controller/chunk_controller.py
from typing import Annotated

from fastapi import Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import RoleInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency
from common.router import APIRouterPro
from module_rag.entity.vo.chunk_vo import ChunkResponseModel, ChunkUpdateModel
from module_rag.service.chunk_service import ChunkService
from utils.response_util import ResponseUtil

# ──────────────────────────────────────────────
# 路由定义
# 角色校验通过路由级依赖实现 AOP 效果，
# 所有注册在该路由下的接口自动生效，无需手动调用 check_role
# ──────────────────────────────────────────────
chunk_controller = APIRouterPro(
    prefix='/rag/chunk',
    order_num=21,
    tags=['RAG管理-分块'],
    dependencies=[
        PreAuthDependency(),
        RoleInterfaceAuthDependency(['admin', 'teacher']),
    ],
)


class ChunkController:
    """分块管理控制器 —— 仅做参数接收 + 调 service + 封装响应"""

    # ── 分块列表（按文档ID，分页）──────────
    @staticmethod
    @chunk_controller.get('/list/{doc_id}', summary='获取文档的分块列表')
    async def get_chunk_list(
        doc_id: Annotated[int, Path(description='文档ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        page_num: Annotated[int, Query(description='页码，从1开始')] = 1,
        page_size: Annotated[int, Query(description='每页条数')] = 20,
    ):
        """分页获取某文档的分块，供老师查看与修改（已排除 embedding 列，大文档不超时）"""
        total, chunks = await ChunkService.get_page_by_doc(query_db, doc_id, page_num, page_size)
        return ResponseUtil.success(data={
            'rows': [ChunkResponseModel.model_validate(c).model_dump() for c in chunks],
            'total': total,
        })

    # ── 修改分块内容（重新向量化）──────────
    @staticmethod
    @chunk_controller.put('', summary='修改分块内容')
    async def update_chunk(
        data: ChunkUpdateModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
    ):
        """修改分块内容并自动重新向量化"""
        await ChunkService.update_chunk(query_db, data)
        return ResponseUtil.success(msg='修改成功，已重新向量化')
