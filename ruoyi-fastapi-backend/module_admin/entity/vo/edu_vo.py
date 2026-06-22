import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from exceptions.exception import ModelValidatorException


class StudentRegisterModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel)

    student_no: str = Field(description='学号')
    nick_name: str = Field(description='学生名称')
    email: str = Field(description='邮箱')
    password: str = Field(description='密码')
    confirm_password: str = Field(description='确认密码')
    apply_role: str = Field(default='student', description='申请角色，固定值 student')
    code: str | None = Field(default=None, description='验证码')
    uuid: str | None = Field(default=None, description='会话编号')
    major: str | None = Field(default=None, description='专业')
    grade: str | None = Field(default=None, description='年级')

    @model_validator(mode='after')
    def check_password(self) -> 'StudentRegisterModel':
        pattern = r"""^[^<>"'|\\]+$"""
        if self.password is None or re.match(pattern, self.password):
            return self
        raise ModelValidatorException(message='密码不能包含非法字符：< > " \' \\ |')


class TeacherRegisterModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel)

    teacher_no: str = Field(description='教师编号')
    nick_name: str = Field(description='教师名称')
    email: str = Field(description='邮箱')
    password: str = Field(description='密码')
    confirm_password: str = Field(description='确认密码')
    apply_role: str = Field(default='teacher', description='申请角色，固定值 teacher')
    code: str | None = Field(default=None, description='验证码')
    uuid: str | None = Field(default=None, description='会话编号')
    title: str | None = Field(default=None, description='职称')
    research_area: str | None = Field(default=None, description='研究方向')

    @model_validator(mode='after')
    def check_password(self) -> 'TeacherRegisterModel':
        pattern = r"""^[^<>"'|\\]+$"""
        if self.password is None or re.match(pattern, self.password):
            return self
        raise ModelValidatorException(message='密码不能包含非法字符：< > " \' \\ |')


class AuditQueryModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel)

    audit_status: str | None = Field(default=None, description='审核状态（0待审核 1已通过 2已拒绝）')
    apply_role: str | None = Field(default=None, description='申请角色')
    begin_time: str | None = Field(default=None, description='开始时间')
    end_time: str | None = Field(default=None, description='结束时间')
    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class AuditActionModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel)

    audit_remark: str | None = Field(default=None, description='审核备注')


class AuditVO(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    audit_id: int | None = Field(default=None, description='审核ID')
    user_id: int | None = Field(default=None, description='关联用户ID')
    apply_role: str | None = Field(default=None, description='申请的角色标识')
    real_name: str | None = Field(default=None, description='真实姓名')
    org_name: str | None = Field(default=None, description='所属单位')
    audit_status: str | None = Field(default=None, description='审核状态')
    audit_remark: str | None = Field(default=None, description='审核备注')
    audited_by: int | None = Field(default=None, description='审核人')
    audited_time: datetime | None = Field(default=None, description='审核时间')
    create_time: datetime | None = Field(default=None, description='创建时间')
    user_name: str | None = Field(default=None, description='用户账号')
    nick_name: str | None = Field(default=None, description='用户昵称')
    email: str | None = Field(default=None, description='邮箱')


class TeacherClassModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    id: int | None = Field(default=None, description='关联ID')
    user_id: int | None = Field(default=None, description='教师用户ID')
    class_id: int | None = Field(default=None, description='班级ID')
    dept_name: str | None = Field(default=None, description='班级名称')


class TeacherClassAddModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel)

    class_id: int = Field(description='班级ID')


class StudentClassUpdateModel(BaseModel):
    """学生个人中心-修改自己的班级"""

    model_config = ConfigDict(alias_generator=to_camel)

    class_id: int = Field(description='班级ID')


class StudentInfoModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    user_id: int | None = Field(default=None, description='用户ID')
    user_name: str | None = Field(default=None, description='用户账号')
    nick_name: str | None = Field(default=None, description='用户昵称')
    email: str | None = Field(default=None, description='邮箱')
    status: str | None = Field(default=None, description='状态')
    student_no: str | None = Field(default=None, description='学号')
    class_id: int | None = Field(default=None, description='班级ID')
    major: str | None = Field(default=None, description='专业')
    grade: str | None = Field(default=None, description='年级')


class StudentInfoEditModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel)

    nick_name: str | None = Field(default=None, description='用户昵称')
    email: str | None = Field(default=None, description='邮箱')
    student_no: str | None = Field(default=None, description='学号')
    class_id: int | None = Field(default=None, description='班级ID')
    major: str | None = Field(default=None, description='专业')
    grade: str | None = Field(default=None, description='年级')


class ManagedUserQueryModel(BaseModel):
    """审核管理-用户分页查询模型"""

    model_config = ConfigDict(alias_generator=to_camel)

    nick_name: str | None = Field(default=None, description='用户昵称（模糊查询）')
    class_id: int | None = Field(default=None, description='班级ID')
    student_no: str | None = Field(default=None, description='学号')
    audit_status: str | None = Field(default=None, description='审核状态（0待审核 1已通过 2已拒绝）')
    apply_role: str | None = Field(default=None, description='申请角色（student/teacher）')
    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class ManagedUserVO(BaseModel):
    """审核管理-用户信息视图"""

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    user_id: int | None = Field(default=None, description='用户ID')
    user_name: str | None = Field(default=None, description='用户账号')
    nick_name: str | None = Field(default=None, description='用户昵称')
    email: str | None = Field(default=None, description='邮箱')
    phonenumber: str | None = Field(default=None, description='手机号')
    status: str | None = Field(default=None, description='账号状态')
    sex: str | None = Field(default=None, description='性别')
    apply_role: str | None = Field(default=None, description='申请角色')
    real_name: str | None = Field(default=None, description='真实姓名')
    audit_status: str | None = Field(default=None, description='审核状态')
    audit_remark: str | None = Field(default=None, description='审核备注')
    audit_id: int | None = Field(default=None, description='审核记录ID')
    student_no: str | None = Field(default=None, description='学号')
    class_id: int | None = Field(default=None, description='班级ID')
    dept_name: str | None = Field(default=None, description='班级名称')
    major: str | None = Field(default=None, description='专业')
    grade: str | None = Field(default=None, description='年级')
    teacher_no: str | None = Field(default=None, description='教师编号')
    department_id: int | None = Field(default=None, description='所属院系')
    title: str | None = Field(default=None, description='职称')
    research_area: str | None = Field(default=None, description='研究方向')
    create_time: str | None = Field(default=None, description='注册时间')


class ManagedUserEditModel(BaseModel):
    """审核管理-编辑用户模型（不可修改学号和班级编号）"""

    model_config = ConfigDict(alias_generator=to_camel)

    nick_name: str | None = Field(default=None, description='用户昵称')
    email: str | None = Field(default=None, description='邮箱')
    phonenumber: str | None = Field(default=None, description='手机号')
    sex: str | None = Field(default=None, description='性别')
    major: str | None = Field(default=None, description='专业')
    grade: str | None = Field(default=None, description='年级')
    title: str | None = Field(default=None, description='职称')
    research_area: str | None = Field(default=None, description='研究方向')


class ManagedUserAuditModel(BaseModel):
    """审核管理-审核操作模型"""

    model_config = ConfigDict(alias_generator=to_camel)

    audit_status: str = Field(description='审核状态（1通过 2拒绝）')
    audit_remark: str | None = Field(default=None, description='审核备注')
