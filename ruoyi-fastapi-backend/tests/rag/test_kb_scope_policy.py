from types import SimpleNamespace

from common.aspect.resource_scope import ScopeRegistry
from module_learning.service.kb_scope_policy import (
    LearningKbPrincipal,
    LearningKbScopePolicy,
    register_learning_kb_scope_policy,
)
from module_rag.entity.vo.knowledge_base_vo import KbScope
from module_rag.service.kb_scope_policy import DefaultKbScopePolicy, KbPrincipal


def test_default_policy_is_product_neutral_and_owner_safe() -> None:
    policy = DefaultKbScopePolicy()
    principal = KbPrincipal(user_id=7, is_admin=False, role='member')

    assert policy.can_access(principal, SimpleNamespace(kb_scope=KbScope.PUBLIC, owner_user_id=None))
    assert policy.can_access(principal, SimpleNamespace(kb_scope=KbScope.PERSONAL, owner_user_id=7))
    assert not policy.can_access(principal, SimpleNamespace(kb_scope=KbScope.PERSONAL, owner_user_id=8))


def test_learning_policy_handles_class_and_owned_student_scopes() -> None:
    policy = LearningKbScopePolicy()
    teacher = LearningKbPrincipal(
        user_id=1,
        is_admin=False,
        role='teacher',
        school_id=10,
        taught_class_ids=[20],
        school_dept_ids=[10, 20],
        owned_student_ids=[30],
    )

    assert policy.can_access(
        teacher,
        SimpleNamespace(kb_scope=KbScope.CLASS, scope_dept_id=20, owner_user_id=None),
    )
    assert policy.can_access(
        teacher,
        SimpleNamespace(kb_scope=KbScope.PERSONAL, scope_dept_id=None, owner_user_id=30),
    )
    assert not policy.can_access(
        teacher,
        SimpleNamespace(kb_scope=KbScope.PERSONAL, scope_dept_id=None, owner_user_id=31),
    )


def test_learning_module_can_override_default_scope_policy() -> None:
    register_learning_kb_scope_policy()

    assert isinstance(ScopeRegistry.get('rag.knowledge_base'), LearningKbScopePolicy)
