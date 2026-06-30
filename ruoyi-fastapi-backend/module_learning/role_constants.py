"""
反身性学习模块 —— 角色判断工具层（集中管理业务角色标识，避免硬编码散落）。

设计要点
--------
1. ``admin`` 是**框架系统超管**角色（role_id=1，SQL 内置）；``teacher``/``student`` 是本模块业务角色。
2. 本类放在模块根（``module_learning/role_constants.py``）而非 ``service/`` 下，
   是为了让 ``dao``/``entity.vo`` 等下层也能复用常量，避免反向依赖 service 层。
3. 未来框架抽取（Phase 2）时，``ADMIN`` 常量与 ``is_admin`` 应上移到 ``common`` 层，
   本类只保留业务角色（teacher/student）。律师等其它产品请建各自的角色工具类，勿复用本类。
"""

from typing import Sequence


class LearningRoles:
    """反身性学习模块的角色标识常量 + 判断工具。"""

    # ===== 角色标识常量（与 sys_role.role_key 对应）=====
    ADMIN = 'admin'
    TEACHER = 'teacher'
    STUDENT = 'student'

    # ===== 角色 → 任务列表跳转页（供动态墙/任务访问校验返回前端跳转地址）=====
    ROLE_REDIRECT = {
        ADMIN: '/learning/task-manage',
        TEACHER: '/learning/task-manage',
        STUDENT: '/learning/my-tasks',
    }

    @staticmethod
    def _norm(roles: Sequence[str] | None) -> list[str]:
        return list(roles or [])

    @classmethod
    def has(cls, roles: Sequence[str] | None, *keys: str) -> bool:
        """roles 中是否含有任意一个指定角色。"""
        r = cls._norm(roles)
        return any(k in r for k in keys)

    @classmethod
    def is_admin(cls, roles: Sequence[str] | None) -> bool:
        """是否为框架超管。"""
        return cls.ADMIN in cls._norm(roles)

    @classmethod
    def is_teacher(cls, roles: Sequence[str] | None) -> bool:
        """是否含有教师角色（不排除 admin）。"""
        return cls.TEACHER in cls._norm(roles)

    @classmethod
    def is_student(cls, roles: Sequence[str] | None) -> bool:
        """是否含有学生角色。"""
        return cls.STUDENT in cls._norm(roles)

    @classmethod
    def is_teacher_only(cls, roles: Sequence[str] | None) -> bool:
        """是教师且不是管理员 —— 用于"教师视角、需排除 admin 全量"的业务分支。"""
        r = cls._norm(roles)
        return cls.TEACHER in r and cls.ADMIN not in r

    @classmethod
    def redirect_for(cls, role_key: str) -> str:
        """按角色取任务列表跳转地址，未知角色返回空串。"""
        return cls.ROLE_REDIRECT.get(role_key, '')
