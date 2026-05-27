from datetime import datetime

from sqlalchemy import CHAR, BigInteger, Column, DateTime, String

from config.database import Base


class EduStudentProfile(Base):
    __tablename__ = 'edu_student_profile'
    __table_args__ = {'comment': '学生信息扩展表'}

    profile_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='档案ID')
    user_id = Column(BigInteger, nullable=False, comment='关联用户ID')
    student_no = Column(String(30), nullable=True, comment='学号')
    class_id = Column(BigInteger, nullable=True, comment='所属班级（复用部门体系）')
    major = Column(String(100), nullable=True, comment='专业')
    grade = Column(String(20), nullable=True, comment='年级')
    del_flag = Column(CHAR(1), nullable=True, server_default='0', comment='删除标志（0存在 1删除）')
    create_by = Column(String(64), nullable=True, server_default="''", comment='创建者')
    create_time = Column(DateTime, nullable=True, default=datetime.now(), comment='创建时间')
    update_by = Column(String(64), nullable=True, server_default="''", comment='更新者')
    update_time = Column(DateTime, nullable=True, default=datetime.now(), comment='更新时间')


class EduTeacherProfile(Base):
    __tablename__ = 'edu_teacher_profile'
    __table_args__ = {'comment': '教师信息扩展表'}

    profile_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='档案ID')
    user_id = Column(BigInteger, nullable=False, comment='关联用户ID')
    teacher_no = Column(String(30), nullable=True, comment='工号')
    department_id = Column(BigInteger, nullable=True, comment='所属院系')
    title = Column(String(50), nullable=True, comment='职称')
    research_area = Column(String(200), nullable=True, comment='研究方向')
    del_flag = Column(CHAR(1), nullable=True, server_default='0', comment='删除标志（0存在 1删除）')
    create_by = Column(String(64), nullable=True, server_default="''", comment='创建者')
    create_time = Column(DateTime, nullable=True, default=datetime.now(), comment='创建时间')
    update_by = Column(String(64), nullable=True, server_default="''", comment='更新者')
    update_time = Column(DateTime, nullable=True, default=datetime.now(), comment='更新时间')


class EduRegistrationAudit(Base):
    __tablename__ = 'edu_registration_audit'
    __table_args__ = {'comment': '注册审核表'}

    audit_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='审核ID')
    user_id = Column(BigInteger, nullable=False, comment='关联用户ID')
    apply_role = Column(String(30), nullable=False, comment='申请的角色标识')
    real_name = Column(String(50), nullable=True, comment='真实姓名')
    org_name = Column(String(200), nullable=True, comment='所属单位')
    audit_status = Column(CHAR(1), nullable=True, server_default='0', comment='审核状态（0待审核 1已通过 2已拒绝）')
    audit_remark = Column(String(500), nullable=True, comment='审核备注')
    audited_by = Column(BigInteger, nullable=True, comment='审核人')
    audited_time = Column(DateTime, nullable=True, comment='审核时间')
    create_time = Column(DateTime, nullable=True, default=datetime.now(), comment='创建时间')


class EduTeacherClass(Base):
    __tablename__ = 'edu_teacher_class'
    __table_args__ = {'comment': '教师班级关联表'}

    id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='关联ID')
    user_id = Column(BigInteger, nullable=False, comment='教师用户ID')
    class_id = Column(BigInteger, nullable=False, comment='班级ID（关联sys_dept）')
    create_by = Column(String(64), nullable=True, server_default="''", comment='创建者')
    create_time = Column(DateTime, nullable=True, default=datetime.now(), comment='创建时间')
