"""知识库可见性策略（业务层规则）

对应「知识库权限控制设计方案」§3 / §9.4。
- 机制（Principal/ScopePolicy/ScopeRegistry/ViewerDependency）来自框架层 `common.aspect.resource_scope`。
- 本文件只实现教育领域专属规则：学校/班级/师生/归属老师。
- 学校识别走 `sys_dept.ancestors` 物化路径（Python 解析），不改框架表、不依赖 find_in_set。
  （本部署为 PostgreSQL，find_in_set 不可用，故同校判定用可移植的 CONCAT/LIKE。）
"""
from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import ColumnElement, and_, false, func, or_, select, true
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.resource_scope import Principal, ScopePolicy, ScopeRegistry
from exceptions.exception import PermissionException
from module_admin.entity.do.dept_do import SysDept
from module_learning.dao.edu_dao import EduDao
from module_rag.entity.do.knowledge_base_do import RagKnowledgeBase
from module_rag.entity.vo.knowledge_base_vo import KbScope


# ──────────────────────────────────────────────────────────────
# 组织解析工具（基于 ancestors 物化路径，领域无关但放在业务层）
# ──────────────────────────────────────────────────────────────
async def school_id_of_dept(db: AsyncSession, dept_id: int | None) -> int | None:
    """返回 dept_id 所属学校的 dept_id。

    规则：parent_id==0 时自己即学校根；否则取 ancestors 中 0 之后的第一段。
    ancestors 形如 "0,100,110"（学校100 → 院系110 → 班级）。
    """
    if dept_id is None:
        return None
    row = (
        await db.execute(select(SysDept).where(SysDept.dept_id == dept_id, SysDept.del_flag == '0'))
    ).scalars().first()
    if row is None:
        return None
    if row.parent_id in (0, None):
        return dept_id
    for seg in (row.ancestors or '').split(','):
        if seg and seg != '0':
            return int(seg)
    return None


async def dept_ids_under_school(db: AsyncSession, school_id: int | None) -> list[int]:
    """某学校及其所有后代部门的 dept_id 集合（用于「同校」判定）。

    使用 CONCAT/LIKE 判断 ancestors 是否包含 school_id，MySQL/PostgreSQL 均可移植。
    """
    if school_id is None:
        return []
    stmt = select(SysDept.dept_id).where(
        SysDept.del_flag == '0',
        or_(
            SysDept.dept_id == school_id,
            func.concat(',', SysDept.ancestors, ',').like(f'%,{school_id},%'),
        ),
    )
    return [row[0] for row in (await db.execute(stmt)).all()]


# ──────────────────────────────────────────────────────────────
# 业务 Principal：在框架基类上扩展教育领域身份字段
# ──────────────────────────────────────────────────────────────
@dataclass
class KbPrincipal(Principal):
    school_id: int | None = None
    class_id: int | None = None                      # 学生所在班级
    taught_class_ids: list[int] = field(default_factory=list)      # 教师任课班级
    owned_student_ids: list[int] = field(default_factory=list)     # 教师归属学生（任课班级里的学生）
    school_dept_ids: list[int] = field(default_factory=list)       # 教师所属学校的全部部门（用于同校班级级判定）


# ──────────────────────────────────────────────────────────────
# 知识库可见性策略
# ──────────────────────────────────────────────────────────────
class KbScopePolicy(ScopePolicy[RagKnowledgeBase]):
    """知识库四级作用域可见性规则（设计方案 §3）。"""

    # ---- 构造请求级主体 ----------------------------------------
    async def build_principal(self, db: AsyncSession, current_user) -> KbPrincipal:
        user = getattr(current_user, 'user', None)
        user_id = getattr(user, 'user_id', None)
        role_keys = [r.role_key for r in (user.role or []) if getattr(user, 'role', None)] if user else []
        is_admin = bool(getattr(user, 'admin', False)) or 'admin' in role_keys
        role = 'admin' if is_admin else ('teacher' if 'teacher' in role_keys else ('student' if 'student' in role_keys else ''))

        # admin 无需加载组织关系
        if is_admin:
            return KbPrincipal(user_id=user_id, is_admin=True, role='admin', role_keys=role_keys)

        if role == 'student':
            profile = await EduDao.get_student_profile_by_user_id(db, user_id)
            class_id = getattr(profile, 'class_id', None)
            school_id = await school_id_of_dept(db, class_id) if class_id else None
            return KbPrincipal(
                user_id=user_id, is_admin=False, role='student', role_keys=role_keys,
                school_id=school_id, class_id=class_id,
            )

        if role == 'teacher':
            profile = await EduDao.get_teacher_profile_by_user_id(db, user_id)
            dept_ref = getattr(profile, 'department_id', None) or getattr(user, 'dept_id', None)
            school_id = await school_id_of_dept(db, dept_ref) if dept_ref else None
            taught_rows = await EduDao.get_teacher_classes(db, user_id)
            taught_class_ids = [r['class_id'] for r in taught_rows if r.get('class_id')]
            student_rows = await EduDao.get_students_by_class_ids(db, taught_class_ids) if taught_class_ids else []
            owned_student_ids = [r['user_id'] for r in student_rows]
            school_dept_ids = await dept_ids_under_school(db, school_id)
            return KbPrincipal(
                user_id=user_id, is_admin=False, role='teacher', role_keys=role_keys,
                school_id=school_id, taught_class_ids=taught_class_ids,
                owned_student_ids=owned_student_ids, school_dept_ids=school_dept_ids,
            )

        # 未识别角色：仅能见公共库
        return KbPrincipal(user_id=user_id, is_admin=False, role=role, role_keys=role_keys)

    # ---- 列表过滤（SQL 级）-------------------------------------
    def visible_filter(self, p: KbPrincipal, model: type[RagKnowledgeBase]) -> ColumnElement:
        if p.is_admin:
            return true()

        conds: list[ColumnElement] = [model.kb_scope == KbScope.PUBLIC]

        # 学校级：同校师生
        if p.school_id is not None:
            conds.append(and_(model.kb_scope == KbScope.SCHOOL, model.scope_dept_id == p.school_id))

        # 班级级
        if p.role == 'student' and p.class_id is not None:
            conds.append(and_(model.kb_scope == KbScope.CLASS, model.scope_dept_id == p.class_id))
        if p.role == 'teacher' and p.school_dept_ids:
            conds.append(and_(model.kb_scope == KbScope.CLASS, model.scope_dept_id.in_(p.school_dept_ids)))

        # 个人级
        if p.role == 'student':
            conds.append(and_(model.kb_scope == KbScope.PERSONAL, model.owner_user_id == p.user_id))
        if p.role == 'teacher' and p.owned_student_ids:
            conds.append(and_(model.kb_scope == KbScope.PERSONAL, model.owner_user_id.in_(p.owned_student_ids)))

        return or_(*conds) if conds else false()

    # ---- 单条访问判定（纯 Python）------------------------------
    def can_access(self, p: KbPrincipal, kb: RagKnowledgeBase) -> bool:
        if p.is_admin:
            return True

        scope = KbScope(kb.kb_scope) if not isinstance(kb.kb_scope, KbScope) else kb.kb_scope

        if scope == KbScope.PUBLIC:
            return True
        if scope == KbScope.SCHOOL:
            return kb.scope_dept_id == p.school_id
        if scope == KbScope.CLASS:
            if p.role == 'student':
                return kb.scope_dept_id == p.class_id
            if p.role == 'teacher':
                return kb.scope_dept_id in (p.school_dept_ids or [])
            return False
        if scope == KbScope.PERSONAL:
            if p.role == 'student':
                return kb.owner_user_id == p.user_id
            if p.role == 'teacher':
                return kb.owner_user_id in (p.owned_student_ids or [])
            return False
        return False

    # ---- 创建时的作用域合法性校验（设计方案 §3.4）---------------
    def validate_create(self, p: KbPrincipal, kb_scope: KbScope, scope_dept_id: int | None) -> None:
        if p.is_admin:
            return  # admin 可建任意级别
        if kb_scope == KbScope.PUBLIC:
            raise PermissionException(message='仅管理员可创建公共知识库')
        if p.role == 'teacher':
            if kb_scope == KbScope.SCHOOL:
                if scope_dept_id is None or scope_dept_id != p.school_id:
                    raise PermissionException(message='学校级知识库作用域必须为本人所属学校')
            elif kb_scope == KbScope.CLASS:
                if scope_dept_id is None or scope_dept_id not in (p.taught_class_ids or []):
                    raise PermissionException(message='班级级知识库作用域必须为本人任课班级')
            else:
                raise PermissionException(message='教师仅可创建学校级/班级级知识库')
        elif p.role == 'student':
            if kb_scope != KbScope.PERSONAL:
                raise PermissionException(message='学生仅可创建个人知识库')
        else:
            raise PermissionException(message='当前角色无权创建知识库')


# 模块加载即注册（控制器经 auto_register_routers 导入本模块时触发）
ScopeRegistry.register('rag.knowledge_base', KbScopePolicy())
