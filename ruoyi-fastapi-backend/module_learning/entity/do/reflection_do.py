from datetime import datetime

from sqlalchemy import CHAR, BigInteger, Column, DateTime, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from config.database import Base


class EduReflectionData(Base):
    """反思区主数据表 —— 存储学生的反思文本、AI评估的反思深度、关联的专业理论"""
    __tablename__ = 'edu_reflection_data'
    __table_args__ = {'comment': '反思区主数据表'}

    reflection_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='反思区数据主键ID')
    record_id = Column(BigInteger, nullable=False, comment='关联的学习记录ID，关联edu_learning_record.record_id')
    scenario_id = Column(BigInteger, nullable=False, comment='关联的情境区数据ID，用于AI生成提问时回溯情境背景')
    student_id = Column(BigInteger, nullable=False, comment='学生用户ID，关联sys_user.user_id')
    # 反思内容与AI评估
    content = Column(Text, comment='学生撰写的反思文本内容，持续更新，支持多轮迭代')
    depth_level = Column(String(20), server_default='descriptive', comment='AI评估的反思深度等级（descriptive描述性/analytical分析性/reflexive反身性）')
    depth_score = Column(Numeric(3, 2), server_default='0.00', comment='AI评估的反思深度分数（0.00-1.00，描述性0.20-0.40/分析性0.41-0.70/反身性0.71-1.00）')
    linked_theories = Column(JSONB, comment='AI关联的专业理论列表，JSON数组如[{"name":"赋权理论","description":"关联说明"}]')
    version = Column(Integer, server_default='1', comment='编辑版本号，每次保存内容时自增，用于追踪修改次数')
    # 状态控制
    status = Column(CHAR(1), server_default='0', comment='反思区状态（0草稿/编辑中 1已确认）')
    del_flag = Column(CHAR(1), server_default='0', comment='删除标志（0存在 2删除）')
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')
    update_time = Column(DateTime, default=datetime.now, comment='最后更新时间')


class EduReflectionDialogue(Base):
    """反思区AI对话记录 —— 存储AI三层递进提问和学生的回应，记录每轮提问前后的深度分数变化"""
    __tablename__ = 'edu_reflection_dialogue'
    __table_args__ = {'comment': '反思区AI对话记录'}

    dialogue_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='对话记录主键ID')
    reflection_id = Column(BigInteger, nullable=False, comment='关联的反思区数据ID，关联edu_reflection_data.reflection_id')
    role = Column(String(20), nullable=False, comment='发言角色（user学生 / assistant AI助手）')
    content = Column(Text, nullable=False, comment='对话内容，AI的结构化追问或学生的反思回应')
    question_level = Column(String(20), comment='AI提问的目标层次（descriptive描述性/analytical分析性/reflexive反身性/theory理论连接）')
    depth_score_before = Column(Numeric(3, 2), comment='本轮对话前学生的反思深度分数')
    depth_score_after = Column(Numeric(3, 2), comment='本轮对话后学生的反思深度分数')
    linked_theories = Column(JSONB, comment='本轮AI推荐关联的专业理论列表')
    create_time = Column(DateTime, default=datetime.now, comment='对话创建时间')


class EduReflectionDepthHistory(Base):
    """反思深度演变历史 —— 记录每次深度评估的分数变化，用于前端绘制深度变化折线图"""
    __tablename__ = 'edu_reflection_depth_history'
    __table_args__ = {'comment': '反思深度演变历史'}

    history_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='历史记录主键ID')
    reflection_id = Column(BigInteger, nullable=False, comment='关联的反思区数据ID，关联edu_reflection_data.reflection_id')
    depth_score = Column(Numeric(3, 2), nullable=False, comment='本次评估的深度分数（0.00-1.00）')
    depth_level = Column(String(20), nullable=False, comment='本次评估的深度等级（descriptive/analytical/reflexive）')
    trigger_type = Column(String(30), comment='触发评估的方式（save学生保存触发 / ai_question AI提问后触发）')
    create_time = Column(DateTime, default=datetime.now, comment='评估时间')
