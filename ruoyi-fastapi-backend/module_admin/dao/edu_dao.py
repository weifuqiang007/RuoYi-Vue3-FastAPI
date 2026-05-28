from sqlalchemy import delete, desc, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.dept_do import SysDept
from module_admin.entity.do.edu_do import EduRegistrationAudit, EduStudentProfile, EduTeacherClass, EduTeacherProfile
from module_admin.entity.do.role_do import SysRole
from module_admin.entity.do.user_do import SysUser, SysUserRole
from module_admin.entity.vo.edu_vo import AuditQueryModel, ManagedUserQueryModel
from utils.page_util import PageUtil


class EduDao:
    @classmethod
    async def get_student_by_no(cls, db: AsyncSession, student_no: str) -> EduStudentProfile | None:
        result = await db.execute(select(EduStudentProfile).where(EduStudentProfile.student_no == student_no))
        return result.scalars().first()

    @classmethod
    async def get_teacher_by_no(cls, db: AsyncSession, teacher_no: str) -> EduTeacherProfile | None:
        result = await db.execute(select(EduTeacherProfile).where(EduTeacherProfile.teacher_no == teacher_no))
        return result.scalars().first()

    @classmethod
    async def add_student_profile(cls, db: AsyncSession, user_id: int, student_no: str, **kwargs) -> EduStudentProfile:
        profile = EduStudentProfile(user_id=user_id, student_no=student_no, **kwargs)
        db.add(profile)
        await db.flush()
        return profile

    @classmethod
    async def add_teacher_profile(cls, db: AsyncSession, user_id: int, teacher_no: str, **kwargs) -> EduTeacherProfile:
        profile = EduTeacherProfile(user_id=user_id, teacher_no=teacher_no, **kwargs)
        db.add(profile)
        await db.flush()
        return profile

    @classmethod
    async def add_registration_audit(cls, db: AsyncSession, audit: EduRegistrationAudit) -> EduRegistrationAudit:
        db.add(audit)
        await db.flush()
        return audit

    @classmethod
    async def get_audit_by_id(cls, db: AsyncSession, audit_id: int) -> EduRegistrationAudit | None:
        result = await db.execute(select(EduRegistrationAudit).where(EduRegistrationAudit.audit_id == audit_id))
        return result.scalars().first()

    @classmethod
    async def get_audit_by_user_id(cls, db: AsyncSession, user_id: int) -> EduRegistrationAudit | None:
        result = (
            await db.execute(
                select(EduRegistrationAudit)
                .where(EduRegistrationAudit.user_id == user_id)
                .order_by(desc(EduRegistrationAudit.create_time))
            )
        )
        return result.scalars().first()

    @classmethod
    async def get_audit_list(cls, db: AsyncSession, query: AuditQueryModel) -> PageModel:
        stmt = select(
            EduRegistrationAudit,
            SysUser.user_name,
            SysUser.nick_name,
            SysUser.email,
        ).outerjoin(SysUser, EduRegistrationAudit.user_id == SysUser.user_id)

        if query.audit_status:
            stmt = stmt.where(EduRegistrationAudit.audit_status == query.audit_status)
        if query.apply_role:
            stmt = stmt.where(EduRegistrationAudit.apply_role == query.apply_role)

        stmt = stmt.order_by(desc(EduRegistrationAudit.create_time))
        result = await db.execute(stmt)
        rows = result.all()

        audit_list = []
        for row in rows:
            audit_dict = {
                'audit_id': row[0].audit_id,
                'user_id': row[0].user_id,
                'apply_role': row[0].apply_role,
                'real_name': row[0].real_name,
                'org_name': row[0].org_name,
                'audit_status': row[0].audit_status,
                'audit_remark': row[0].audit_remark,
                'audited_by': row[0].audited_by,
                'audited_time': row[0].audited_time,
                'create_time': row[0].create_time,
                'user_name': row[1],
                'nick_name': row[2],
                'email': row[3],
            }
            audit_list.append(audit_dict)

        return PageUtil.get_page_obj(audit_list, query.page_num, query.page_size)

    @classmethod
    async def update_audit_status(
        cls,
        db: AsyncSession,
        audit_id: int,
        audit_status: str,
        audited_by: int,
        audit_remark: str | None = None,
    ) -> None:
        await db.execute(
            update(EduRegistrationAudit)
            .where(EduRegistrationAudit.audit_id == audit_id)
            .values(
                audit_status=audit_status,
                audited_by=audited_by,
                audited_time=__import__('datetime').datetime.now(),
                audit_remark=audit_remark,
            )
        )

    @classmethod
    async def add_teacher_class(cls, db: AsyncSession, user_id: int, class_id: int, create_by: str = '') -> EduTeacherClass:
        tc = EduTeacherClass(user_id=user_id, class_id=class_id, create_by=create_by)
        db.add(tc)
        await db.flush()
        return tc

    @classmethod
    async def get_teacher_classes(cls, db: AsyncSession, user_id: int) -> list:
        result = await db.execute(
            select(EduTeacherClass, SysDept.dept_name)
            .outerjoin(SysDept, EduTeacherClass.class_id == SysDept.dept_id)
            .where(EduTeacherClass.user_id == user_id)
        )
        rows = result.all()
        return [
            {
                'id': row[0].id,
                'user_id': row[0].user_id,
                'class_id': row[0].class_id,
                'dept_name': row[1],
            }
            for row in rows
        ]

    @classmethod
    async def remove_teacher_class(cls, db: AsyncSession, tc_id: int) -> None:
        await db.execute(delete(EduTeacherClass).where(EduTeacherClass.id == tc_id))

    @classmethod
    async def get_students_by_class_ids(cls, db: AsyncSession, class_ids: list[int]) -> list:
        result = await db.execute(
            select(EduStudentProfile, SysUser)
            .outerjoin(SysUser, EduStudentProfile.user_id == SysUser.user_id)
            .where(
                EduStudentProfile.class_id.in_(class_ids),
                SysUser.del_flag == '0',
            )
        )
        rows = result.all()
        return [
            {
                'user_id': row[1].user_id,
                'user_name': row[1].user_name,
                'nick_name': row[1].nick_name,
                'email': row[1].email,
                'status': row[1].status,
                'student_no': row[0].student_no,
                'class_id': row[0].class_id,
                'major': row[0].major,
                'grade': row[0].grade,
            }
            for row in rows
        ]

    @classmethod
    async def update_student_profile(cls, db: AsyncSession, user_id: int, **kwargs) -> None:
        values = {k: v for k, v in kwargs.items() if v is not None}
        if not values:
            return
        await db.execute(update(EduStudentProfile).where(EduStudentProfile.user_id == user_id).values(**values))

    @classmethod
    async def update_teacher_profile(cls, db: AsyncSession, user_id: int, **kwargs) -> None:
        values = {k: v for k, v in kwargs.items() if v is not None}
        if not values:
            return
        await db.execute(update(EduTeacherProfile).where(EduTeacherProfile.user_id == user_id).values(**values))

    # ==================== 审核管理（ManagedUser）====================

    @classmethod
    async def get_managed_user_list(
        cls,
        db: AsyncSession,
        query: ManagedUserQueryModel,
        class_ids: list[int] | None = None,
    ) -> PageModel:
        """
        查询审核管理用户列表。
        class_ids 不为 None 时按班级范围过滤（教师），为 None 时查全部（管理员）。
        """
        stmt = (
            select(
                SysUser.user_id,
                SysUser.user_name,
                SysUser.nick_name,
                SysUser.email,
                SysUser.phonenumber,
                SysUser.status,
                SysUser.sex,
                SysUser.create_time,
                EduRegistrationAudit.audit_id,
                EduRegistrationAudit.apply_role,
                EduRegistrationAudit.real_name,
                EduRegistrationAudit.audit_status,
                EduRegistrationAudit.audit_remark,
                EduStudentProfile.student_no,
                EduStudentProfile.class_id,
                EduStudentProfile.major,
                EduStudentProfile.grade,
                EduTeacherProfile.teacher_no,
                EduTeacherProfile.department_id,
                EduTeacherProfile.title,
                EduTeacherProfile.research_area,
                SysDept.dept_name,
            )
            .outerjoin(EduRegistrationAudit, SysUser.user_id == EduRegistrationAudit.user_id)
            .outerjoin(EduStudentProfile, SysUser.user_id == EduStudentProfile.user_id)
            .outerjoin(EduTeacherProfile, SysUser.user_id == EduTeacherProfile.user_id)
            .outerjoin(SysDept, EduStudentProfile.class_id == SysDept.dept_id)
            .where(SysUser.del_flag == '0')
        )

        # 班级范围过滤（教师视角）
        if class_ids is not None:
            stmt = stmt.where(
                or_(
                    EduStudentProfile.class_id.in_(class_ids),
                    EduTeacherProfile.user_id.isnot(None),
                )
            )

        # 条件筛选
        if query.nick_name:
            stmt = stmt.where(SysUser.nick_name.ilike(f'%{query.nick_name}%'))
        if query.class_id:
            stmt = stmt.where(EduStudentProfile.class_id == query.class_id)
        if query.student_no:
            stmt = stmt.where(EduStudentProfile.student_no == query.student_no)
        if query.audit_status:
            stmt = stmt.where(EduRegistrationAudit.audit_status == query.audit_status)
        if query.apply_role:
            stmt = stmt.where(EduRegistrationAudit.apply_role == query.apply_role)

        stmt = stmt.order_by(desc(SysUser.create_time))
        result = await db.execute(stmt)
        rows = result.all()

        user_list = []
        for row in rows:
            user_list.append({
                'user_id': row[0],
                'user_name': row[1],
                'nick_name': row[2],
                'email': row[3],
                'phonenumber': row[4],
                'status': row[5],
                'sex': row[6],
                'create_time': str(row[7]) if row[7] else None,
                'audit_id': row[8],
                'apply_role': row[9],
                'real_name': row[10],
                'audit_status': row[11],
                'audit_remark': row[12],
                'student_no': row[13],
                'class_id': row[14],
                'major': row[15],
                'grade': row[16],
                'teacher_no': row[17],
                'department_id': row[18],
                'title': row[19],
                'research_area': row[20],
                'dept_name': row[21],
            })

        # 批量查询每个用户的系统角色
        if user_list:
            user_ids = [u['user_id'] for u in user_list]
            role_stmt = (
                select(SysUserRole.user_id, SysRole.role_key)
                .join(SysRole, SysUserRole.role_id == SysRole.role_id)
                .where(SysUserRole.user_id.in_(user_ids))
            )
            role_result = await db.execute(role_stmt)
            role_rows = role_result.all()
            role_map: dict[int, list[str]] = {}
            for uid, rk in role_rows:
                role_map.setdefault(uid, []).append(rk)
            for u in user_list:
                u['role_keys'] = ','.join(role_map.get(u['user_id'], []))

        return PageUtil.get_page_obj(user_list, query.page_num, query.page_size)

    @classmethod
    async def get_student_profile_by_user_id(cls, db: AsyncSession, user_id: int) -> EduStudentProfile | None:
        result = await db.execute(select(EduStudentProfile).where(EduStudentProfile.user_id == user_id))
        return result.scalars().first()

    @classmethod
    async def get_teacher_profile_by_user_id(cls, db: AsyncSession, user_id: int) -> EduTeacherProfile | None:
        result = await db.execute(select(EduTeacherProfile).where(EduTeacherProfile.user_id == user_id))
        return result.scalars().first()

    @classmethod
    async def remove_student_from_class(cls, db: AsyncSession, user_id: int) -> None:
        """将学生从班级中移除（class_id 置空），教师视角下该学生不再可见"""
        await db.execute(
            update(EduStudentProfile).where(EduStudentProfile.user_id == user_id).values(class_id=None)
        )

    @classmethod
    async def get_available_roles(cls, db: AsyncSession) -> list[dict]:
        """获取可用于注册的角色列表（排除admin角色）"""
        result = await db.execute(
            select(SysRole.role_id, SysRole.role_name, SysRole.role_key).where(
                SysRole.role_id != 1, SysRole.status == '0', SysRole.del_flag == '0'
            )
        )
        return [{'role_id': r[0], 'role_name': r[1], 'role_key': r[2]} for r in result.all()]
