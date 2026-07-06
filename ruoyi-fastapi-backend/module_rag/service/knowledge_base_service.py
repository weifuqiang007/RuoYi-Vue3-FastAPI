# module_rag/service/knowledge_base_service.py
"""知识库管理服务"""
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.resource_scope import ScopeRegistry
from exceptions.exception import PermissionException
from module_rag.dao.knowledge_base_dao import KnowledgeBaseDao
from module_rag.entity.do.knowledge_base_do import RagKnowledgeBase
from module_rag.entity.vo.knowledge_base_vo import KnowledgeBaseCreateModel, KnowledgeBaseUpdateModel, KbScope
from module_rag.service.kb_scope_policy import KbPrincipal  # noqa: F401  （触发 ScopeRegistry 注册）


def _policy():
    return ScopeRegistry.get('rag.knowledge_base')


class KnowledgeBaseService:

    # ── 创建 ──────────────────────────────────────────────────
    @classmethod
    async def create(cls, db: AsyncSession, data: KnowledgeBaseCreateModel, principal: KbPrincipal) -> RagKnowledgeBase:
        # 作用域合法性由策略统一校验（设计方案 §3.4）
        _policy().validate_create(principal, data.kb_scope, data.scope_dept_id)
        # public/personal 无作用域部门；school/class 取前端传入（已由策略约束为本校/本班）
        scope_dept_id = data.scope_dept_id if data.kb_scope in (KbScope.SCHOOL, KbScope.CLASS) else None
        kb = RagKnowledgeBase(
            kb_name=data.kb_name,
            kb_desc=data.kb_desc,
            embedding_model=data.embedding_model,
            chunk_size=data.chunk_size,
            chunk_overlap=data.chunk_overlap,
            user_id=principal.user_id,
            owner_user_id=principal.user_id,
            kb_scope=data.kb_scope,
            scope_dept_id=scope_dept_id,
        )
        return await KnowledgeBaseDao.create(db, kb)

    # ── 列表（按可见性过滤）────────────────────────────────────
    @classmethod
    async def get_list(cls, db: AsyncSession, principal: KbPrincipal) -> list[RagKnowledgeBase]:
        cond = _policy().visible_filter(principal, RagKnowledgeBase)
        return await KnowledgeBaseDao.get_visible_list(db, cond)

    # ── 详情（带访问校验）──────────────────────────────────────
    @classmethod
    async def get_accessible(cls, db: AsyncSession, kb_id: int, principal: KbPrincipal) -> RagKnowledgeBase | None:
        kb = await KnowledgeBaseDao.get_by_id(db, kb_id)
        if kb is None:
            return None
        if not _policy().can_access(principal, kb):
            raise PermissionException(message='无权访问该知识库')
        return kb

    # ── 更新（仅 owner / admin）────────────────────────────────
    @classmethod
    async def update(cls, db: AsyncSession, data: KnowledgeBaseUpdateModel, principal: KbPrincipal) -> None:
        kb = await KnowledgeBaseDao.get_by_id(db, data.kb_id)
        if kb is None:
            raise PermissionException(message='知识库不存在')
        if not (principal.is_admin or kb.owner_user_id == principal.user_id):
            raise PermissionException(message='无权修改他人的知识库')
        update_data = {k: v for k, v in data.model_dump().items() if v is not None and k != 'kb_id'}
        await KnowledgeBaseDao.update_by_id(db, data.kb_id, **update_data)

    # ── 删除（仅 owner / admin）────────────────────────────────
    @classmethod
    async def delete(cls, db: AsyncSession, kb_id: int, principal: KbPrincipal) -> None:
        kb = await KnowledgeBaseDao.get_by_id(db, kb_id)
        if kb is None:
            raise PermissionException(message='知识库不存在')
        if not (principal.is_admin or kb.owner_user_id == principal.user_id):
            raise PermissionException(message='无权删除他人的知识库')
        await KnowledgeBaseDao.delete_by_id(db, kb_id)

    # ── 检索前置：过滤出当前主体有权访问的 kb_ids ──────────────
    @classmethod
    async def filter_accessible_ids(
        cls, db: AsyncSession, kb_ids: list[int], principal: KbPrincipal
    ) -> list[int]:
        policy = _policy()
        kbs = await KnowledgeBaseDao.get_by_ids(db, kb_ids)
        return [kb.kb_id for kb in kbs if policy.can_access(principal, kb)]
