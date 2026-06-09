from datetime import datetime

from sqlalchemy import CHAR, BigInteger, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from config.database import Base


class EduTask(Base):
    """教学任务表 —— 教师创建反身性研究任务，配置各区知识库和AI参数，发布到指定班级"""
    __tablename__ = 'edu_task'
    __table_args__ = {'comment': '教学任务表'}

    task_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='任务主键ID')
    task_name = Column(String(200), nullable=False, comment='任务名称，如"张大爷案例行动研究"')
    task_description = Column(Text, comment='任务描述/给学生看的引导语，说明任务要求和目标')
    teacher_id = Column(BigInteger, nullable=True, comment='创建任务的教师用户ID，关联sys_user.user_id；学生自研课题时为NULL')
    creator_type = Column(CHAR(1), server_default='0', comment='创建者类型（0教师创建的教学任务 1学生自己创建的自研课题 2 admin用户创建的课题）')
    student_id = Column(BigInteger, nullable=True, comment='学生创建者ID，关联sys_user.user_id；教师创建时为NULL，学生自研时填写自己的用户ID')
    # 教师可预先指定一个情境场景（可选），学生进入情境区时会自动填入
    preset_scenario = Column(Text, comment='预设情境文本，教师可为学生指定一个场景描述，为空则学生自行填写')
    # 各区使用的知识库ID列表，格式如 [1, 2]，决定AI检索时从哪些知识库取专业知识
    scenario_kb_ids = Column(JSONB, comment='情境区使用的知识库ID列表，JSON数组如[1,2]，AI分析场景时从这些知识库检索')
    decision_kb_ids = Column(JSONB, comment='决策区使用的知识库ID列表，通常指向伦理守则知识库，用于AI伦理分析')
    reflection_kb_ids = Column(JSONB, comment='反思区使用的知识库ID列表，通常指向理论概念知识库，用于AI关联专业理论')
    research_kb_ids = Column(JSONB, comment='研究生成区使用的知识库ID列表，用于AI生成研究问题时检索学术文献')
    # 各区AI行为配置（可选），不配则使用系统默认Prompt
    scenario_config = Column(JSONB, comment='情境区AI配置，JSON对象，可自定义提问方向、分析重点等，为空用默认配置')
    reflection_config = Column(JSONB, comment='反思区AI配置，JSON对象，可设置最小反思深度要求、追问策略等，为空用默认配置')
    deadline = Column(DateTime, comment='任务截止时间，超过后学生仍可查看但标记为已过期')
    status = Column(CHAR(1), server_default='0', comment='任务状态（0草稿 1已发布 2已关闭）')
    del_flag = Column(CHAR(1), server_default='0', comment='删除标志（0存在 2删除）')
    create_by = Column(String(64), server_default='', comment='创建者用户名')
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')
    update_by = Column(String(64), server_default='', comment='最后更新者用户名')
    update_time = Column(DateTime, default=datetime.now, comment='最后更新时间')


class EduTaskClass(Base):
    """任务-班级分配表 —— 一个教学任务可分配给多个班级，通过此表建立多对多关系"""
    __tablename__ = 'edu_task_class'
    __table_args__ = {'comment': '任务-班级分配表'}

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='分配记录主键ID')
    task_id = Column(BigInteger, nullable=False, comment='关联的教学任务ID，关联edu_task.task_id')
    dept_id = Column(BigInteger, nullable=False, comment='班级ID，复用sys_dept部门体系中的班级节点')
    create_time = Column(DateTime, default=datetime.now, comment='分配创建时间')
