# module_rag/controller/knowledge_base_controller.py
from typing import Annotated

from fastapi import Path
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import RoleInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_rag.entity.vo.knowledge_base_vo import (
    KnowledgeBaseCreateModel,
    KnowledgeBaseResponseModel,
    KnowledgeBaseUpdateModel,
)
from module_rag.service.knowledge_base_service import KnowledgeBaseService
from utils.response_util import ResponseUtil

# ──────────────────────────────────────────────
# 路由定义
# 角色校验通过路由级依赖实现 AOP 效果，
# 所有注册在该路由下的接口自动生效，无需手动调用 check_role
# ──────────────────────────────────────────────
knowledge_base_controller = APIRouterPro(
    prefix='/rag/kb',
    order_num=20,
    tags=['RAG管理-知识库'],
    dependencies=[
        PreAuthDependency(),
        RoleInterfaceAuthDependency(['admin', 'teacher']),
    ],
)


class KnowledgeBaseController:
    """知识库管理控制器 —— 将增删改查接口以类形式组织"""

    # ── 创建 ──────────────────────────────────
    @staticmethod
    @knowledge_base_controller.post('', summary='创建知识库')
    async def create(
        data: KnowledgeBaseCreateModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: CurrentUserModel = CurrentUserDependency(),
    ):
        kb = await KnowledgeBaseService.create(query_db, data, current_user.user.user_id)
        return ResponseUtil.success(data={'kb_id': kb.kb_id})

    # ── 列表 ──────────────────────────────────
    @staticmethod
    @knowledge_base_controller.get('/list', summary='获取知识库列表')
    async def get_list(
        query_db: Annotated[AsyncSession, DBSessionDependency()],
    ):
        kb_list = await KnowledgeBaseService.get_list(query_db)
        return ResponseUtil.success(
            data=[KnowledgeBaseResponseModel.model_validate(kb).model_dump() for kb in kb_list]
        )

    # ── 详情 ──────────────────────────────────
    @staticmethod
    @knowledge_base_controller.get('/{kb_id}', summary='获取知识库详情')
    async def get_detail(
        kb_id: Annotated[int, Path(description='知识库ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
    ):
        kb = await KnowledgeBaseService.get_by_id(query_db, kb_id)
        if not kb:
            return ResponseUtil.failure(msg='知识库不存在')
        return ResponseUtil.success(
            data=KnowledgeBaseResponseModel.model_validate(kb).model_dump()
        )

    # ── 更新 ──────────────────────────────────
    @staticmethod
    @knowledge_base_controller.put('', summary='更新知识库')
    async def update(
        data: KnowledgeBaseUpdateModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
    ):
        await KnowledgeBaseService.update(query_db, data)
        return ResponseUtil.success(msg='更新成功')

    # ── 删除 ──────────────────────────────────
    @staticmethod
    @knowledge_base_controller.delete('/{kb_ids}', summary='删除知识库')
    async def delete(
        kb_ids: Annotated[str, Path(description='知识库ID，多个用逗号分隔')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
    ):
        for kb_id in kb_ids.split(','):
            await KnowledgeBaseService.delete(query_db, int(kb_id))
        return ResponseUtil.success(msg='删除成功')
