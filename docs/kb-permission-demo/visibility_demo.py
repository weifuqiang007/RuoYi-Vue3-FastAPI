"""
知识库权限控制 - 可见性判定 Demo
================================
配合「知识库权限控制设计方案.md」§3 的算法，用纯 Python（无数据库依赖）演示：
  - OrgResolver.school_id_of(dept_id)     —— 走 ancestors 物化路径识别「学校」
  - KbViewerContext                        —— 按当前用户构造的请求级上下文
  - can_access(ctx, kb)                    —— 单库访问校验
  - visible_list(ctx, kbs)                 —— 列表可见性过滤

运行：  python visibility_demo.py
数据：  与同目录 schema.sql 一致（内存副本）。
"""

import sys
from dataclasses import dataclass, field

# Windows 控制台默认 GBK，强制 UTF-8 以正确显示中文
try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except Exception:
    pass


# =============================================================================
# 1. 内存数据（对应 schema.sql 的样例）
# =============================================================================
# sys_dept: dept_id -> (parent_id, ancestors)
SYS_DEPT = {
    100: (0,   "0"),            # 北京大学（学校根）
    110: (100, "0,100"),        # 计算机学院
    111: (110, "0,100,110"),    # 北大计科1班
    112: (110, "0,100,110"),    # 北大计科2班
    200: (0,   "0"),            # 清华大学（学校根）
    210: (200, "0,200"),        # 软件学院
    211: (210, "0,200,210"),    # 清华软工1班
}

STUDENT_CLASS = {1: 111, 2: 112, 3: 211}            # user_id -> class_id
TEACHER_DEPT = {10: 110, 20: 210}                   # user_id -> department_id
TEACHER_CLASS = [(10, 111), (20, 211)]              # (teacher_user_id, class_id)

# kb_id -> dict(kb_name, kb_scope, scope_dept_id, owner_user_id)
KNOWLEDGE_BASES = [
    {"kb_id": 1, "kb_name": "平台公共教案库",     "kb_scope": "public",   "scope_dept_id": None, "owner_user_id": 999},
    {"kb_id": 2, "kb_name": "北大-机器学习导引",  "kb_scope": "school",   "scope_dept_id": 100, "owner_user_id": 10},
    {"kb_id": 3, "kb_name": "北大计科1班-习题集", "kb_scope": "class",    "scope_dept_id": 111, "owner_user_id": 10},
    {"kb_id": 4, "kb_name": "学生1-个人错题本",   "kb_scope": "personal", "scope_dept_id": None, "owner_user_id": 1},
    {"kb_id": 5, "kb_name": "清华-算法基础",      "kb_scope": "school",   "scope_dept_id": 200, "owner_user_id": 20},
]


# =============================================================================
# 2. OrgResolver —— 「学校」识别（不改 sys_dept，走 ancestors）
# =============================================================================
def school_id_of(dept_id: int | None) -> int | None:
    """返回 dept_id 所属学校的 dept_id。
    规则：parent_id==0 时自己就是学校根；否则取 ancestors 中 0 之后的第一段。
    """
    if dept_id is None:
        return None
    parent_id, ancestors = SYS_DEPT[dept_id]
    if parent_id == 0:
        return dept_id
    # ancestors 形如 "0,100,110" -> 取第一个非 0 段 = 100
    for seg in ancestors.split(","):
        if seg and seg != "0":
            return int(seg)
    return dept_id


# =============================================================================
# 3. ViewerContext —— 请求级上下文（对应设计方案 §3.1）
# =============================================================================
@dataclass
class KbViewerContext:
    user_id: int
    is_admin: bool
    role: str                                   # 'admin' | 'teacher' | 'student'
    school_id: int | None = None
    class_id: int | None = None                 # 学生所在班级
    taught_class_ids: list[int] = field(default_factory=list)      # 教师任课班级
    owned_student_ids: list[int] = field(default_factory=list)     # 教师归属学生


def build_context(user_id: int, role: str) -> KbViewerContext:
    is_admin = role == "admin"
    ctx = KbViewerContext(user_id=user_id, is_admin=is_admin, role=role)

    if role == "student":
        ctx.class_id = STUDENT_CLASS.get(user_id)
        ctx.school_id = school_id_of(ctx.class_id)

    elif role == "teacher":
        dept = TEACHER_DEPT.get(user_id)
        ctx.school_id = school_id_of(dept)
        ctx.taught_class_ids = [c for (t, c) in TEACHER_CLASS if t == user_id]
        # 归属学生 = 任课班级里的学生
        ctx.owned_student_ids = [
            uid for uid, cid in STUDENT_CLASS.items() if cid in ctx.taught_class_ids
        ]
    return ctx


# =============================================================================
# 4. 判定核心：can_access / visible_list（对应设计方案 §3.2 / §3.3）
# =============================================================================
def can_access(ctx: KbViewerContext, kb: dict) -> bool:
    if ctx.is_admin:
        return True

    scope = kb["kb_scope"]

    if scope == "public":
        return True

    if scope == "school":
        # 同校师生均可见
        return kb["scope_dept_id"] == ctx.school_id

    if scope == "class":
        if ctx.role == "student":
            return kb["scope_dept_id"] == ctx.class_id
        if ctx.role == "teacher":
            # 推荐方案 Q1：同校教师均可看班级级
            return school_id_of(kb["scope_dept_id"]) == ctx.school_id
        return False

    if scope == "personal":
        if ctx.role == "student":
            return kb["owner_user_id"] == ctx.user_id
        if ctx.role == "teacher":
            return kb["owner_user_id"] in ctx.owned_student_ids
        return False

    return False


def visible_list(ctx: KbViewerContext) -> list[int]:
    return [kb["kb_id"] for kb in KNOWLEDGE_BASES if can_access(ctx, kb)]


def assert_seen(label: str, ctx: KbViewerContext, expected: set[int]):
    got = set(visible_list(ctx))
    ok = got == expected
    print(f"[{'PASS' if ok else 'FAIL'}] {label:<14} 可见={sorted(got)}  期望={sorted(expected)}")
    assert ok, f"{label} 断言失败: {got} != {expected}"


# =============================================================================
# 5. 场景断言（对应设计方案 §6 的 5 个场景）
# =============================================================================
def main():
    print("== 知识库权限可见性 Demo ==\n")

    # 场景1：admin 看全部
    assert_seen("admin", build_context(999, "admin"), {1, 2, 3, 4, 5})

    # 场景2：北大教师10 —— public + 本校school(2) + 同校class(3) + 归属学生个人库(4)；看不到清华(5)
    assert_seen("北大教师10", build_context(10, "teacher"), {1, 2, 3, 4})

    # 场景3：清华教师20 —— public(1) + 本校school(5)；看不到北大(2,3)、学生个人库(4)
    assert_seen("清华教师20", build_context(20, "teacher"), {1, 5})

    # 场景4：北大学生1 —— public(1) + 本校school(2) + 本班class(3) + 本人个人库(4)；看不到清华(5)
    assert_seen("北大学生1", build_context(1, "student"), {1, 2, 3, 4})

    # 场景5：清华学生3 —— public(1) + 本校school(5)
    assert_seen("清华学生3", build_context(3, "student"), {1, 5})

    # 附加：检索越权防护 —— 学生1 试图检索 kb_ids=[2,4,5]，应被过滤为仅有权的 [4]（2同校可见其实也允许，5被拒）
    ctx = build_context(1, "student")
    requested = [2, 4, 5]
    kb_map = {kb["kb_id"]: kb for kb in KNOWLEDGE_BASES}
    allowed = [kid for kid in requested if can_access(ctx, kb_map[kid])]
    print(f"\n[越权防护] 学生1 请求检索 kb_ids={requested} -> 放行={allowed}  期望=[2, 4]")
    assert set(allowed) == {2, 4}, allowed

    print("\n全部断言通过 [OK]")


if __name__ == "__main__":
    main()
