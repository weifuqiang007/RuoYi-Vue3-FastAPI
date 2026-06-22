from typing import Annotated

from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.rate_limit_annotation import ApiRateLimit, ApiRateLimitPreset
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.constant import ApiNamespace
from common.router import APIRouterPro
from common.vo import CrudResponseModel, DataResponseModel, PageModel, ResponseBaseModel
from module_admin.entity.vo.edu_vo import (
    AuditActionModel,
    AuditQueryModel,
    AuditVO,
    ManagedUserAuditModel,
    ManagedUserEditModel,
    ManagedUserQueryModel,
    ManagedUserVO,
    StudentInfoEditModel,
    StudentInfoModel,
    StudentClassUpdateModel,
    StudentRegisterModel,
    TeacherClassAddModel,
    TeacherClassModel,
    TeacherRegisterModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.edu_service import EduService
from utils.log_util import logger
from utils.response_util import ResponseUtil

edu_controller = APIRouterPro(prefix='/edu', order_num=10, tags=['教育模块'])


# ==================== 角色查询接口（无需登录） ====================


@edu_controller.get(
    '/roles',
    summary='获取可选角色列表',
    description='返回系统中可用于注册的角色列表（学生、教师），供前端注册页面渲染角色选择下拉框',
)
async def get_available_roles(
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await EduService.get_available_roles(query_db)
    return ResponseUtil.success(data=result)


# ==================== 注册接口（无需登录） ====================


@edu_controller.post(
    '/register/student',
    summary='学生注册',
    description='学生注册接口，注册后需管理员审核',
    response_model=DataResponseModel[CrudResponseModel],
)
@ApiRateLimit(namespace=ApiNamespace.REGISTER, preset=ApiRateLimitPreset.ANON_AUTH_REGISTER)
async def register_student(
    request: Request,
    reg: StudentRegisterModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await EduService.register_student(request, query_db, reg)
    logger.info(result.message)
    return ResponseUtil.success(data=result, msg=result.message)


@edu_controller.post(
    '/register/teacher',
    summary='教师注册',
    description='教师注册接口，注册后需管理员审核',
    response_model=DataResponseModel[CrudResponseModel],
)
@ApiRateLimit(namespace=ApiNamespace.REGISTER, preset=ApiRateLimitPreset.ANON_AUTH_REGISTER)
async def register_teacher(
    request: Request,
    reg: TeacherRegisterModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await EduService.register_teacher(request, query_db, reg)
    logger.info(result.message)
    return ResponseUtil.success(data=result, msg=result.message)


# ==================== 审核管理（需管理员登录） ====================


audit_controller = APIRouterPro(
    prefix='/edu/audit',
    order_num=11,
    tags=['教育模块-审核管理'],
    dependencies=[PreAuthDependency()],
)


@audit_controller.get(
    '/list',
    summary='审核列表',
    description='获取注册审核列表（管理员）',
    response_model=DataResponseModel[PageModel[AuditVO]],
)
async def get_audit_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    apply_role: str | None = None,
    audit_status: str | None = None,
    page_num: int = 1,
    page_size: int = 10,
) -> Response:
    query = AuditQueryModel(
        apply_role=apply_role,
        audit_status=audit_status,
        page_num=page_num,
        page_size=page_size,
    )
    result = await EduService.get_audit_list(query_db, query)
    return ResponseUtil.success(data=result)


@audit_controller.put(
    '/approve/{audit_id}',
    summary='审核通过',
    description='管理员审核通过注册申请',
    response_model=DataResponseModel[CrudResponseModel],
)
async def approve_audit(
    request: Request,
    audit_id: int,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    action: AuditActionModel | None = None,
) -> Response:
    result = await EduService.approve_audit(
        query_db,
        audit_id=audit_id,
        audited_by=current_user.user.user_id,
        audit_remark=action.audit_remark if action else None,
    )
    logger.info(result.message)
    return ResponseUtil.success(data=result, msg=result.message)


@audit_controller.put(
    '/reject/{audit_id}',
    summary='审核拒绝',
    description='管理员拒绝注册申请',
    response_model=DataResponseModel[CrudResponseModel],
)
async def reject_audit(
    request: Request,
    audit_id: int,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    action: AuditActionModel | None = None,
) -> Response:
    result = await EduService.reject_audit(
        query_db,
        audit_id=audit_id,
        audited_by=current_user.user.user_id,
        audit_remark=action.audit_remark if action else None,
    )
    logger.info(result.message)
    return ResponseUtil.success(data=result, msg=result.message)


# ==================== 教师管理班级学生（需教师登录） ====================


teacher_controller = APIRouterPro(
    prefix='/edu/teacher',
    order_num=12,
    tags=['教育模块-教师管理'],
    dependencies=[PreAuthDependency()],
)


@teacher_controller.get(
    '/classes',
    summary='教师班级列表',
    description='获取当前教师关联的班级列表',
    response_model=DataResponseModel[list[TeacherClassModel]],
)
async def get_teacher_classes(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await EduService.get_teacher_classes(query_db, current_user.user.user_id)
    return ResponseUtil.success(data=result)


@teacher_controller.post(
    '/class',
    summary='添加教师班级关联',
    description='教师关联一个班级',
    response_model=DataResponseModel[CrudResponseModel],
)
async def add_teacher_class(
    request: Request,
    class_data: TeacherClassAddModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await EduService.add_teacher_class(
        query_db,
        user_id=current_user.user.user_id,
        class_id=class_data.class_id,
        create_by=current_user.user.user_name or '',
    )
    logger.info(result.message)
    return ResponseUtil.success(data=result, msg=result.message)


@teacher_controller.delete(
    '/class/{tc_id}',
    summary='删除教师班级关联',
    description='删除教师与班级的关联',
    response_model=DataResponseModel[CrudResponseModel],
)
async def remove_teacher_class(
    request: Request,
    tc_id: int,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await EduService.remove_teacher_class(query_db, tc_id, current_user.user.user_id)
    logger.info(result.message)
    return ResponseUtil.success(data=result, msg=result.message)


@teacher_controller.get(
    '/students',
    summary='教师查看班级学生',
    description='教师查看自己管理班级的所有学生',
    response_model=DataResponseModel[list[StudentInfoModel]],
)
async def get_teacher_students(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await EduService.get_students_by_teacher(query_db, current_user.user.user_id)
    return ResponseUtil.success(data=result)


@teacher_controller.put(
    '/student/{student_user_id}',
    summary='教师修改学生信息',
    description='教师修改自己管理班级中的学生信息',
    response_model=DataResponseModel[CrudResponseModel],
)
async def update_student_info(
    request: Request,
    student_user_id: int,
    edit: StudentInfoEditModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await EduService.update_student_info(
        query_db,
        teacher_user_id=current_user.user.user_id,
        student_user_id=student_user_id,
        edit=edit,
    )
    logger.info(result.message)
    return ResponseUtil.success(data=result, msg=result.message)


# ==================== 审核管理（管理员/教师共用） ====================


manage_controller = APIRouterPro(
    prefix='/edu/manage',
    order_num=13,
    tags=['教育模块-审核管理'],
    dependencies=[PreAuthDependency()],
)


@manage_controller.get(
    '/users',
    summary='查询用户列表',
    description='管理员查看所有用户，教师仅查看自己管理班级的学生。支持按昵称模糊查询、班级、学号、审核状态筛选。',
    response_model=DataResponseModel[PageModel[ManagedUserVO]],
)
async def get_managed_users(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    nick_name: str | None = None,
    class_id: int | None = None,
    student_no: str | None = None,
    audit_status: str | None = None,
    apply_role: str | None = None,
    page_num: int = 1,
    page_size: int = 10,
) -> Response:
    query = ManagedUserQueryModel(
        nick_name=nick_name,
        class_id=class_id,
        student_no=student_no,
        audit_status=audit_status,
        apply_role=apply_role,
        page_num=page_num,
        page_size=page_size,
    )
    result = await EduService.get_managed_users(query_db, query, current_user)
    return ResponseUtil.success(data=result)


@manage_controller.post(
    '/user/student',
    summary='新增学生',
    description='管理员/教师新增学生，注册后进入待审核状态',
    response_model=DataResponseModel[CrudResponseModel],
)
async def managed_create_student(
    request: Request,
    reg: StudentRegisterModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await EduService.managed_create_student(request, query_db, reg)
    logger.info(result.message)
    return ResponseUtil.success(data=result, msg=result.message)


@manage_controller.post(
    '/user/teacher',
    summary='新增教师',
    description='管理员新增教师，注册后进入待审核状态',
    response_model=DataResponseModel[CrudResponseModel],
)
async def managed_create_teacher(
    request: Request,
    reg: TeacherRegisterModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await EduService.managed_create_teacher(request, query_db, reg)
    logger.info(result.message)
    return ResponseUtil.success(data=result, msg=result.message)


@manage_controller.put(
    '/user/{user_id}',
    summary='编辑用户信息',
    description='编辑用户信息（学号、班级编号不可修改）',
    response_model=DataResponseModel[CrudResponseModel],
)
async def managed_edit_user(
    request: Request,
    user_id: int,
    edit: ManagedUserEditModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await EduService.managed_edit_user(query_db, current_user, user_id, edit)
    logger.info(result.message)
    return ResponseUtil.success(data=result, msg=result.message)


@manage_controller.delete(
    '/user/{user_id}',
    summary='移除用户',
    description='管理员停用用户；教师将学生从班级中移除（学生信息保留，仅教师不可见）',
    response_model=DataResponseModel[CrudResponseModel],
)
async def managed_remove_user(
    request: Request,
    user_id: int,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await EduService.managed_remove_user(query_db, current_user, user_id)
    logger.info(result.message)
    return ResponseUtil.success(data=result, msg=result.message)


@manage_controller.put(
    '/audit/{user_id}',
    summary='审核用户',
    description='审核用户注册申请（通过/拒绝）',
    response_model=DataResponseModel[CrudResponseModel],
)
async def managed_audit_user(
    request: Request,
    user_id: int,
    audit_model: ManagedUserAuditModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await EduService.managed_audit_user(query_db, current_user, user_id, audit_model)
    logger.info(result.message)
    return ResponseUtil.success(data=result, msg=result.message)


# ==================== 学生个人中心-自管班级（需学生登录） ====================


student_controller = APIRouterPro(
    prefix='/edu/student',
    order_num=14,
    tags=['教育模块-学生自管'],
    dependencies=[PreAuthDependency()],
)


@student_controller.put(
    '/class',
    summary='学生修改自己的班级',
    description='学生在个人中心修改自己的所属班级（单选），同步更新所属部门显示',
    response_model=DataResponseModel[CrudResponseModel],
)
async def update_student_own_class(
    request: Request,
    class_data: StudentClassUpdateModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await EduService.update_student_own_class(
        query_db,
        user_id=current_user.user.user_id,
        class_id=class_data.class_id,
    )
    logger.info(result.message)
    return ResponseUtil.success(data=result, msg=result.message)


# ==================== 个人中心-部门(班级)树（登录即可） ====================


profile_controller = APIRouterPro(
    prefix='/edu/profile',
    order_num=15,
    tags=['教育模块-个人中心'],
    dependencies=[PreAuthDependency()],
)


@profile_controller.get(
    '/deptTree',
    summary='个人中心-部门(班级)树',
    description='返回全部在用部门，供学生/教师在个人中心选择班级（不限数据范围，仅需登录）',
)
async def get_profile_dept_tree(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    data = await EduService.get_profile_dept_tree(query_db)
    logger.info('获取个人中心部门树成功')
    return ResponseUtil.success(data=data)
