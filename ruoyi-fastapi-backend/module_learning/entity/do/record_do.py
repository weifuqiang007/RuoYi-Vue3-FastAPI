from datetime import datetime

from sqlalchemy import CHAR, BigInteger, Column, DateTime, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from config.database import Base


class EduLearningRecord(Base):
    """学习记录主表 —— 四区联动主控表，记录一个学生完成一个任务的完整状态流转"""
    __tablename__ = 'edu_learning_record'
    __table_args__ = {'comment': '学习记录主表（四区联动主控）'}

    record_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='学习记录主键ID')
    task_id = Column(BigInteger, comment='关联的教学任务ID，关联edu_task.task_id；为NULL时表示学生自研课题')
    student_id = Column(BigInteger, nullable=False, comment='学生用户ID，关联sys_user.user_id')
    # 当前所在阶段，驱动四区状态机流转：scenario→decision→reflection→research→submitted→completed
    current_stage = Column(String(20), server_default='scenario', comment='当前所在阶段（scenario/decision/reflection/research/submitted/completed）')
    # 各区完成状态，用于前端展示进度和状态机前置校验
    scenario_status = Column(CHAR(1), server_default='0', comment='情境区完成状态（0未开始 1进行中 2已完成）')
    decision_status = Column(CHAR(1), server_default='0', comment='决策区完成状态（0未开始 1进行中 2已完成）')
    reflection_status = Column(CHAR(1), server_default='0', comment='反思区完成状态（0未开始 1进行中 2已完成）')
    research_status = Column(CHAR(1), server_default='0', comment='研究生成区完成状态（0未开始 1进行中 2已完成）')
    # 各区数据ID，方便快速查找，避免每次JOIN；在各区首次保存数据时回填
    scenario_id = Column(BigInteger, comment='关联的情境区数据ID，关联edu_scenario_data.scenario_id')
    decision_id = Column(BigInteger, comment='关联的决策区最新/汇总数据ID，关联edu_decision_data.decision_id')
    reflection_id = Column(BigInteger, comment='关联的反思区数据ID，关联edu_reflection_data.reflection_id')
    research_id = Column(BigInteger, comment='关联的研究区数据ID，关联edu_research_data.research_id')
    # 整体状态与评价
    status = Column(String(20), server_default='ongoing', comment='整体状态（ongoing进行中/submitted已提交/completed已完成）')
    score = Column(Numeric(5, 2), comment='教师评分，加权总分（情境20%+决策20%+反思30%+研究30%）')
    teacher_feedback = Column(Text, comment='教师总评语')
    # 时间节点
    start_time = Column(DateTime, default=datetime.now, comment='学生开始任务的时间')
    submit_time = Column(DateTime, comment='学生提交研究成果的时间')
    complete_time = Column(DateTime, comment='教师评分完成、记录关闭的时间')
    # 审计字段
    del_flag = Column(CHAR(1), server_default='0', comment='删除标志（0存在 2删除）')
    create_by = Column(String(64), server_default='', comment='创建者用户名')
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')
    update_by = Column(String(64), server_default='', comment='最后更新者用户名')
    update_time = Column(DateTime, default=datetime.now, comment='最后更新时间')
