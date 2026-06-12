from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from datetime import datetime

from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.dao.edu_dao import EduDao
from module_admin.dao.user_dao import UserDao
from module_admin.entity.do.edu_do import EduRegistrationAudit
from module_admin.entity.do.user_do import SysUserRole
from module_admin.entity.vo.edu_vo import (
    AuditQueryModel,
    AuditVO,
    ManagedUserAuditModel,
    ManagedUserEditModel,
    ManagedUserQueryModel,
    StudentInfoEditModel,
    StudentInfoModel,
    StudentRegisterModel,
    TeacherClassModel,
    TeacherRegisterModel,
)
from module_admin.entity.vo.user_vo import UserModel, UserRoleModel
from utils.pwd_util import PwdUtil

ROLE_ID_STUDENT = 3
ROLE_ID_TEACHER = 4


class EduService:
    @classmethod
    async def get_available_roles(cls, query_db: AsyncSession) -> list[dict]:
        """获取可用于注册的角色列表（排除admin）"""
        return await EduDao.get_available_roles(query_db)

    @classmethod
    async def register_student(
        cls, request: Request, query_db: AsyncSession, reg: StudentRegisterModel
    ) -> CrudResponseModel:
        if reg.password != reg.confirm_password:
            raise ServiceException(message='两次输入的密码不一致')

        existing = await EduDao.get_student_by_no(query_db, reg.student_no)
        if existing:
            raise ServiceException(message=f'学号 {reg.student_no} 已注册')

        existing_user = await UserDao.get_user_by_name(query_db, reg.student_no)
        if existing_user:
            raise ServiceException(message=f'账号 {reg.student_no} 已存在')

        add_user = UserModel(
            user_name=reg.student_no,
            nick_name=reg.nick_name,
            email=reg.email,
            password=PwdUtil.get_password_hash(reg.password),
            status='1',
        )
        db_user = await UserDao.add_user_dao(query_db, add_user)
        user_id = db_user.user_id

        if reg.apply_role != 'student':
            raise ServiceException(message='学生注册接口 applyRole 须为 student')
        query_db.add(SysUserRole(user_id=user_id, role_id=ROLE_ID_STUDENT))

        student_profile = await EduDao.add_student_profile(
            query_db,
            user_id=user_id,
            student_no=reg.student_no,
            major=reg.major,
            grade=reg.grade,
        )

        # 如果学生档案关联了班级，同步更新 sys_user.dept_id 以便个人中心显示所属部门
        if student_profile and student_profile.class_id:
            await UserDao.edit_user_dao(query_db, {'user_id': user_id, 'dept_id': student_profile.class_id})

        audit = EduRegistrationAudit(
            user_id=user_id,
            apply_role='student',
            real_name=reg.nick_name,
        )
        await EduDao.add_registration_audit(query_db, audit)

        await query_db.commit()
        return CrudResponseModel(is_success=True, message='注册成功，请等待管理员审核')

    @classmethod
    async def register_teacher(
        cls, request: Request, query_db: AsyncSession, reg: TeacherRegisterModel
    ) -> CrudResponseModel:
        if reg.password != reg.confirm_password:
            raise ServiceException(message='两次输入的密码不一致')

        existing = await EduDao.get_teacher_by_no(query_db, reg.teacher_no)
        if existing:
            raise ServiceException(message=f'教师编号 {reg.teacher_no} 已注册')

        existing_user = await UserDao.get_user_by_name(query_db, reg.teacher_no)
        if existing_user:
            raise ServiceException(message=f'账号 {reg.teacher_no} 已存在')

        add_user = UserModel(
            user_name=reg.teacher_no,
            nick_name=reg.nick_name,
            email=reg.email,
            password=PwdUtil.get_password_hash(reg.password),
            status='1',
        )
        db_user = await UserDao.add_user_dao(query_db, add_user)
        user_id = db_user.user_id

        if reg.apply_role != 'teacher':
            raise ServiceException(message='教师注册接口 applyRole 须为 teacher')
        query_db.add(SysUserRole(user_id=user_id, role_id=ROLE_ID_TEACHER))

        await EduDao.add_teacher_profile(
            query_db,
            user_id=user_id,
            teacher_no=reg.teacher_no,
            title=reg.title,
            research_area=reg.research_area,
        )

        audit = EduRegistrationAudit(
            user_id=user_id,
            apply_role='teacher',
            real_name=reg.nick_name,
        )
        await EduDao.add_registration_audit(query_db, audit)

        await query_db.commit()
        return CrudResponseModel(is_success=True, message='注册成功，请等待管理员审核')

    @classmethod
    async def get_audit_list(cls, query_db: AsyncSession, query: AuditQueryModel) -> PageModel:
        return await EduDao.get_audit_list(query_db, query)

    @classmethod
    async def approve_audit(
        cls, query_db: AsyncSession, audit_id: int, audited_by: int, audit_remark: str | None = None
    ) -> CrudResponseModel:
        audit = await EduDao.get_audit_by_id(query_db, audit_id)
        if not audit:
            raise ServiceException(message='审核记录不存在')
        if audit.audit_status != '0':
            raise ServiceException(message='该记录已审核，请勿重复操作')

        await EduDao.update_audit_status(query_db, audit_id, '1', audited_by, audit_remark)

        await UserDao.edit_user_dao(
            query_db,
            {'user_id': audit.user_id, 'status': '0', 'pwd_update_date': datetime.now()},
        )

        role_id = ROLE_ID_STUDENT if audit.apply_role == 'student' else ROLE_ID_TEACHER
        existing_role = (await query_db.execute(
            select(SysUserRole).where(SysUserRole.user_id == audit.user_id, SysUserRole.role_id == role_id)
        )).scalars().first()
        if not existing_role:
            query_db.add(SysUserRole(user_id=audit.user_id, role_id=role_id))

        await query_db.commit()
        return CrudResponseModel(is_success=True, message='审核通过')

    @classmethod
    async def reject_audit(
        cls, query_db: AsyncSession, audit_id: int, audited_by: int, audit_remark: str | None = None
    ) -> CrudResponseModel:
        audit = await EduDao.get_audit_by_id(query_db, audit_id)
        if not audit:
            raise ServiceException(message='审核记录不存在')
        if audit.audit_status != '0':
            raise ServiceException(message='该记录已审核，请勿重复操作')

        await EduDao.update_audit_status(query_db, audit_id, '2', audited_by, audit_remark)
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='已拒绝')

    @classmethod
    async def get_teacher_classes(cls, query_db: AsyncSession, user_id: int) -> list[dict]:
        return await EduDao.get_teacher_classes(query_db, user_id)

    @classmethod
    async def add_teacher_class(
        cls, query_db: AsyncSession, user_id: int, class_id: int, create_by: str = ''
    ) -> CrudResponseModel:
        existing = await EduDao.get_teacher_classes(query_db, user_id)
        for item in existing:
            if item['class_id'] == class_id:
                raise ServiceException(message='该班级已关联，请勿重复添加')

        await EduDao.add_teacher_class(query_db, user_id, class_id, create_by)
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='关联成功')

    @classmethod
    async def remove_teacher_class(cls, query_db: AsyncSession, tc_id: int, user_id: int) -> CrudResponseModel:
        classes = await EduDao.get_teacher_classes(query_db, user_id)
        owned_ids = {item['id'] for item in classes}
        if tc_id not in owned_ids:
            raise ServiceException(message='无权删除此关联')

        await EduDao.remove_teacher_class(query_db, tc_id)
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='删除成功')

    @classmethod
    async def get_students_by_teacher(cls, query_db: AsyncSession, user_id: int) -> list[dict]:
        classes = await EduDao.get_teacher_classes(query_db, user_id)
        if not classes:
            return []
        class_ids = [item['class_id'] for item in classes]
        return await EduDao.get_students_by_class_ids(query_db, class_ids)

    @classmethod
    async def update_student_info(
        cls, query_db: AsyncSession, teacher_user_id: int, student_user_id: int, edit: StudentInfoEditModel
    ) -> CrudResponseModel:
        classes = await EduDao.get_teacher_classes(query_db, teacher_user_id)
        if not classes:
            raise ServiceException(message='您尚未关联任何班级')

        class_ids = [item['class_id'] for item in classes]
        students = await EduDao.get_students_by_class_ids(query_db, class_ids)
        student_user_ids = {s['user_id'] for s in students}
        if student_user_id not in student_user_ids:
            raise ServiceException(message='该学生不在您管理的班级中')

        update_data = edit.model_dump(exclude_unset=True, by_alias=False)
        if not update_data:
            raise ServiceException(message='无更新数据')

        await EduDao.update_student_profile(query_db, student_user_id, **update_data)
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='更新成功')

    # ==================== 审核管理（ManagedUser）====================

    @classmethod
    def _is_admin(cls, current_user: 'CurrentUserModel') -> bool:
        return 'admin' in (current_user.roles or [])

    @classmethod
    def _is_teacher(cls, current_user: 'CurrentUserModel') -> bool:
        return 'teacher' in (current_user.roles or [])

    @classmethod
    async def get_managed_users(
        cls,
        query_db: AsyncSession,
        query: ManagedUserQueryModel,
        current_user: 'CurrentUserModel',
    ) -> PageModel:
        if cls._is_admin(current_user):
            return await EduDao.get_managed_user_list(query_db, query, class_ids=None)
        elif cls._is_teacher(current_user):
            classes = await EduDao.get_teacher_classes(query_db, current_user.user.user_id)
            if not classes:
                return PageModel(rows=[], page_num=query.page_num, page_size=query.page_size, total=0, has_next=False)
            class_ids = [item['class_id'] for item in classes]
            return await EduDao.get_managed_user_list(query_db, query, class_ids=class_ids)
        raise ServiceException(message='无权访问')

    @classmethod
    async def managed_create_student(
        cls, request: Request, query_db: AsyncSession, reg: StudentRegisterModel
    ) -> CrudResponseModel:
        return await cls.register_student(request, query_db, reg)

    @classmethod
    async def managed_create_teacher(
        cls, request: Request, query_db: AsyncSession, reg: TeacherRegisterModel
    ) -> CrudResponseModel:
        return await cls.register_teacher(request, query_db, reg)

    @classmethod
    async def managed_edit_user(
        cls,
        query_db: AsyncSession,
        current_user: 'CurrentUserModel',
        target_user_id: int,
        edit: ManagedUserEditModel,
    ) -> CrudResponseModel:
        update_data = edit.model_dump(exclude_unset=True, by_alias=False)
        if not update_data:
            raise ServiceException(message='无更新数据')

        # 分离 sys_user 字段和 profile 字段
        user_fields = {}
        profile_fields = {}
        user_keys = {'nick_name', 'email', 'phonenumber', 'sex'}
        for k, v in update_data.items():
            if k in user_keys:
                user_fields[k] = v
            else:
                profile_fields[k] = v

        # 权限校验：教师只能编辑自己班级的学生
        if cls._is_teacher(current_user):
            classes = await EduDao.get_teacher_classes(query_db, current_user.user.user_id)
            if not classes:
                raise ServiceException(message='您尚未关联任何班级')
            class_ids = [item['class_id'] for item in classes]
            students = await EduDao.get_students_by_class_ids(query_db, class_ids)
            if target_user_id not in {s['user_id'] for s in students}:
                raise ServiceException(message='无权编辑该用户')

        if user_fields:
            await UserDao.edit_user_dao(query_db, {'user_id': target_user_id, **user_fields})

        student_profile = await EduDao.get_student_profile_by_user_id(query_db, target_user_id)
        if student_profile and profile_fields:
            await EduDao.update_student_profile(query_db, target_user_id, **profile_fields)

        teacher_profile = await EduDao.get_teacher_profile_by_user_id(query_db, target_user_id)
        if teacher_profile and profile_fields:
            await EduDao.update_teacher_profile(query_db, target_user_id, **profile_fields)

        await query_db.commit()
        return CrudResponseModel(is_success=True, message='更新成功')

    @classmethod
    async def managed_remove_user(
        cls,
        query_db: AsyncSession,
        current_user: 'CurrentUserModel',
        target_user_id: int,
    ) -> CrudResponseModel:
        if cls._is_admin(current_user):
            # 管理员：停用用户
            await UserDao.edit_user_dao(query_db, {'user_id': target_user_id, 'status': '1'})
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='已停用该用户')
        elif cls._is_teacher(current_user):
            # 教师：将学生从班级移除
            classes = await EduDao.get_teacher_classes(query_db, current_user.user.user_id)
            if not classes:
                raise ServiceException(message='您尚未关联任何班级')
            class_ids = [item['class_id'] for item in classes]
            students = await EduDao.get_students_by_class_ids(query_db, class_ids)
            if target_user_id not in {s['user_id'] for s in students}:
                raise ServiceException(message='该学生不在您管理的班级中')
            await EduDao.remove_student_from_class(query_db, target_user_id)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='已将该学生从班级中移除')
        raise ServiceException(message='无权操作')

    @classmethod
    async def managed_audit_user(
        cls,
        query_db: AsyncSession,
        current_user: 'CurrentUserModel',
        target_user_id: int,
        audit_model: ManagedUserAuditModel,
    ) -> CrudResponseModel:
        audit = await EduDao.get_audit_by_user_id(query_db, target_user_id)
        if not audit:
            raise ServiceException(message='该用户无审核记录')
        if audit.audit_status != '0':
            raise ServiceException(message='该记录已审核，请勿重复操作')

        if audit_model.audit_status == '1':
            return await cls.approve_audit(
                query_db,
                audit_id=audit.audit_id,
                audited_by=current_user.user.user_id,
                audit_remark=audit_model.audit_remark,
            )
        elif audit_model.audit_status == '2':
            return await cls.reject_audit(
                query_db,
                audit_id=audit.audit_id,
                audited_by=current_user.user.user_id,
                audit_remark=audit_model.audit_remark,
            )
        raise ServiceException(message='audit_status 仅支持 1（通过）或 2（拒绝）')
