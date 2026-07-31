"""反身性学习产品的知识库学校/班级/师生作用域策略。"""

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import ColumnElement, and_, false, func, or_, select, true
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.resource_scope import ScopePolicy, ScopeRegistry
from exceptions.exception import PermissionException
from module_admin.entity.do.dept_do import SysDept
from module_learning.dao.edu_dao import EduDao
from module_rag.entity.do.knowledge_base_do import RagKnowledgeBase
from module_rag.entity.vo.knowledge_base_vo import KbScope
from module_rag.service.kb_scope_policy import KbPrincipal


async def school_id_of_dept(db: AsyncSession, dept_id: int | None) -> int | None:
    """返回部门所属学校根节点 ID。"""
    if dept_id is None:
        return None
    row = (
        await db.execute(select(SysDept).where(SysDept.dept_id == dept_id, SysDept.del_flag == '0'))
    ).scalars().first()
    if row is None:
        return None
    if row.parent_id in (0, None):
        return dept_id
    for segment in (row.ancestors or '').split(','):
        if segment and segment != '0':
            return int(segment)
    return None


async def dept_ids_under_school(db: AsyncSession, school_id: int | None) -> list[int]:
    """返回学校及其全部后代部门 ID。"""
    if school_id is None:
        return []
    statement = select(SysDept.dept_id).where(
        SysDept.del_flag == '0',
        or_(
            SysDept.dept_id == school_id,
            func.concat(',', SysDept.ancestors, ',').like(f'%,{school_id},%'),
        ),
    )
    return [row[0] for row in (await db.execute(statement)).all()]


@dataclass
class LearningKbPrincipal(KbPrincipal):
    """反身性学习知识库主体，扩展学校、班级和师生归属。"""

    school_id: int | None = None
    class_id: int | None = None
    taught_class_ids: list[int] = field(default_factory=list)
    owned_student_ids: list[int] = field(default_factory=list)
    school_dept_ids: list[int] = field(default_factory=list)


class LearningKbScopePolicy(ScopePolicy[RagKnowledgeBase]):
    """反身性学习产品的 public/school/class/personal 四级权限规则。"""

    async def build_principal(self, db: AsyncSession, current_user: Any) -> LearningKbPrincipal:
        user = getattr(current_user, 'user', None)
        user_id = getattr(user, 'user_id', None)
        role_keys = [role.role_key for role in (getattr(user, 'role', None) or [])]
        is_admin = bool(getattr(user, 'admin', False)) or 'admin' in role_keys
        role = 'admin' if is_admin else (
            'teacher' if 'teacher' in role_keys else ('student' if 'student' in role_keys else '')
        )
        if is_admin:
            return LearningKbPrincipal(user_id=user_id, is_admin=True, role=role, role_keys=role_keys)

        if role == 'student':
            profile = await EduDao.get_student_profile_by_user_id(db, user_id)
            class_id = getattr(profile, 'class_id', None)
            return LearningKbPrincipal(
                user_id=user_id,
                is_admin=False,
                role=role,
                role_keys=role_keys,
                school_id=await school_id_of_dept(db, class_id),
                class_id=class_id,
            )

        if role == 'teacher':
            profile = await EduDao.get_teacher_profile_by_user_id(db, user_id)
            department_id = getattr(profile, 'department_id', None) or getattr(user, 'dept_id', None)
            school_id = await school_id_of_dept(db, department_id)
            taught_rows = await EduDao.get_teacher_classes(db, user_id)
            taught_class_ids = [row['class_id'] for row in taught_rows if row.get('class_id')]
            student_rows = await EduDao.get_students_by_class_ids(db, taught_class_ids) if taught_class_ids else []
            return LearningKbPrincipal(
                user_id=user_id,
                is_admin=False,
                role=role,
                role_keys=role_keys,
                school_id=school_id,
                taught_class_ids=taught_class_ids,
                owned_student_ids=[row['user_id'] for row in student_rows],
                school_dept_ids=await dept_ids_under_school(db, school_id),
            )

        return LearningKbPrincipal(user_id=user_id, is_admin=False, role=role, role_keys=role_keys)

    def visible_filter(self, principal: LearningKbPrincipal, model: type[RagKnowledgeBase]) -> ColumnElement:
        if principal.is_admin:
            return true()
        conditions: list[ColumnElement] = [model.kb_scope == KbScope.PUBLIC]
        if principal.school_id is not None:
            conditions.append(and_(model.kb_scope == KbScope.SCHOOL, model.scope_dept_id == principal.school_id))
        if principal.role == 'student' and principal.class_id is not None:
            conditions.append(and_(model.kb_scope == KbScope.CLASS, model.scope_dept_id == principal.class_id))
            conditions.append(and_(model.kb_scope == KbScope.PERSONAL, model.owner_user_id == principal.user_id))
        if principal.role == 'teacher':
            if principal.school_dept_ids:
                conditions.append(
                    and_(model.kb_scope == KbScope.CLASS, model.scope_dept_id.in_(principal.school_dept_ids))
                )
            if principal.owned_student_ids:
                conditions.append(
                    and_(model.kb_scope == KbScope.PERSONAL, model.owner_user_id.in_(principal.owned_student_ids))
                )
        return or_(*conditions) if conditions else false()

    def can_access(self, principal: LearningKbPrincipal, kb: RagKnowledgeBase) -> bool:
        if principal.is_admin:
            return True
        scope = KbScope(kb.kb_scope) if not isinstance(kb.kb_scope, KbScope) else kb.kb_scope
        if scope == KbScope.PUBLIC:
            return True
        if scope == KbScope.SCHOOL:
            return kb.scope_dept_id == principal.school_id
        if scope == KbScope.CLASS:
            if principal.role == 'student':
                return kb.scope_dept_id == principal.class_id
            return principal.role == 'teacher' and kb.scope_dept_id in principal.school_dept_ids
        if scope == KbScope.PERSONAL:
            if principal.role == 'student':
                return kb.owner_user_id == principal.user_id
            return principal.role == 'teacher' and kb.owner_user_id in principal.owned_student_ids
        return False

    def validate_create(
        self,
        principal: LearningKbPrincipal,
        kb_scope: KbScope,
        scope_dept_id: int | None,
    ) -> None:
        if principal.is_admin:
            return
        if kb_scope == KbScope.PUBLIC:
            raise PermissionException(message='仅管理员可创建公共知识库')
        if principal.role == 'teacher':
            if kb_scope == KbScope.SCHOOL and scope_dept_id != principal.school_id:
                raise PermissionException(message='学校级知识库作用域必须为本人所属学校')
            if kb_scope == KbScope.CLASS and scope_dept_id not in principal.taught_class_ids:
                raise PermissionException(message='班级级知识库作用域必须为本人任课班级')
            if kb_scope not in (KbScope.SCHOOL, KbScope.CLASS):
                raise PermissionException(message='教师仅可创建学校级/班级级知识库')
            return
        if principal.role == 'student' and kb_scope == KbScope.PERSONAL:
            return
        raise PermissionException(message='当前角色无权创建知识库')


def register_learning_kb_scope_policy() -> None:
    """用教育领域策略覆盖 RAG 模块的安全默认策略。"""
    ScopeRegistry.register('rag.knowledge_base', LearningKbScopePolicy())
