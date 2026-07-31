"""知识库默认作用域策略。

本模块只提供产品无关的 public/personal 规则。学校、班级、师生关系等领域规则
由业务模块注册同一 resource_key 的策略覆盖。
"""

from dataclasses import dataclass
from typing import Any

from sqlalchemy import ColumnElement, and_, or_, true
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.resource_scope import Principal, ScopePolicy, ScopeRegistry
from exceptions.exception import PermissionException
from module_rag.entity.do.knowledge_base_do import RagKnowledgeBase
from module_rag.entity.vo.knowledge_base_vo import KbScope


@dataclass
class KbPrincipal(Principal):
    """知识库请求主体；领域扩展数据放入 Principal.attrs。"""


class DefaultKbScopePolicy(ScopePolicy[RagKnowledgeBase]):
    """默认仅支持公共库和本人个人库，适合作为独立 RAG 模块的安全兜底。"""

    async def build_principal(self, db: AsyncSession, current_user: Any) -> KbPrincipal:
        user = getattr(current_user, 'user', None)
        user_id = getattr(user, 'user_id', None)
        role_keys = [role.role_key for role in (getattr(user, 'role', None) or [])]
        is_admin = bool(getattr(user, 'admin', False)) or 'admin' in role_keys
        return KbPrincipal(
            user_id=user_id,
            is_admin=is_admin,
            role='admin' if is_admin else (role_keys[0] if role_keys else ''),
            role_keys=role_keys,
        )

    def visible_filter(self, principal: KbPrincipal, model: type[RagKnowledgeBase]) -> ColumnElement:
        if principal.is_admin:
            return true()
        return or_(
            model.kb_scope == KbScope.PUBLIC,
            and_(
                model.kb_scope == KbScope.PERSONAL,
                model.owner_user_id == principal.user_id,
            ),
        )

    def can_access(self, principal: KbPrincipal, kb: RagKnowledgeBase) -> bool:
        if principal.is_admin:
            return True
        scope = KbScope(kb.kb_scope) if not isinstance(kb.kb_scope, KbScope) else kb.kb_scope
        return scope == KbScope.PUBLIC or (
            scope == KbScope.PERSONAL and kb.owner_user_id == principal.user_id
        )

    def validate_create(
        self,
        principal: KbPrincipal,
        kb_scope: KbScope,
        scope_dept_id: int | None,
    ) -> None:
        if principal.is_admin:
            return
        if kb_scope != KbScope.PERSONAL:
            raise PermissionException(message='当前产品未注册该知识库作用域的创建策略')


ScopeRegistry.register('rag.knowledge_base', DefaultKbScopePolicy())
