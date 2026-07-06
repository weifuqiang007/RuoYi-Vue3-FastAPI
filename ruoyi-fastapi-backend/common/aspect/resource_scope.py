"""资源作用域（Resource Scope）—— 框架级可见性机制

与 `common/aspect/data_scope.py`（角色视角、按 dept 的行级权限）互补：
data_scope 回答「这个角色能看哪些行」，resource_scope 回答「这条资源对哪些主体可见」。

设计原则（见知识库权限控制设计方案 §9）：
- 本模块只提供「机制」，不含任何领域词（school/class/teacher/student 等）。
- 领域「规则」由业务模块继承 ScopePolicy 实现，并通过 ScopeRegistry 注册。
- 扩展点是「注册一个 Policy + 声明 scope 类型」，而非纯配置。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Annotated, Any, Generic, TypeVar

from fastapi import Depends, Request, params
from sqlalchemy import ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.context import RequestContext

T = TypeVar('T')  # 资源 ORM 模型类型


@dataclass
class Principal:
    """请求级主体身份（领域无关基类）。

    业务模块继承本类，扩展领域专属字段（如 school_id / class_id 等），
    使框架层不必感知任何业务语义。
    """

    user_id: int
    is_admin: bool
    role: str  # 业务自定义的主角色标识，框架不解释其含义
    role_keys: list[str] = field(default_factory=list)
    attrs: dict[str, Any] = field(default_factory=dict)  # 预留：业务自定义扩展属性


class ScopePolicy(ABC, Generic[T]):
    """资源可见性策略抽象。业务模块为每类资源注册一个实现。"""

    @abstractmethod
    async def build_principal(self, db: AsyncSession, current_user) -> Principal:
        """从当前登录用户构造 Principal（业务在此查询组织关系并填充领域字段）。"""

    @abstractmethod
    def visible_filter(self, principal: Principal, model: type[T]) -> ColumnElement:
        """列表过滤：返回 where 条件（SQL 级，保证列表可扩展）。

        admin 场景应返回永真条件，由调用方拼入主查询。
        """

    @abstractmethod
    def can_access(self, principal: Principal, resource: T) -> bool:
        """单条访问判定（详情/检索/改删前置），纯 Python，principal 须已含全部所需字段。"""


class ScopeRegistry:
    """按 resource_key 注册/查找 ScopePolicy。"""

    _map: dict[str, ScopePolicy] = {}

    @classmethod
    def register(cls, resource_key: str, policy: ScopePolicy) -> None:
        cls._map[resource_key] = policy

    @classmethod
    def get(cls, resource_key: str) -> ScopePolicy:
        if resource_key not in cls._map:
            raise KeyError(f'未注册资源作用域策略: {resource_key}')
        return cls._map[resource_key]


def ViewerDependency(resource_key: str) -> params.Depends:  # noqa: N802
    """注入当前请求的 Principal（按 resource_key 取对应 policy 构造）。

    依赖 PreAuth 已先执行（其会经 LoginService.get_current_user 写入 RequestContext）。
    """

    async def _resolve(
        request: Request,  # noqa: ARG001
        query_db: Annotated[AsyncSession, DBSessionDependency()],  # noqa: ARG001
    ) -> Principal:
        current_user = RequestContext.get_current_user()
        policy = ScopeRegistry.get(resource_key)
        return await policy.build_principal(query_db, current_user)

    return Depends(_resolve)
