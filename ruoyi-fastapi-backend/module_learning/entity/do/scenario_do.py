from datetime import datetime

from sqlalchemy import CHAR, BigInteger, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from config.database import Base


class EduScenarioData(Base):
    """情境区主数据表 —— 存储学生描述的实践场景、AI分析出的关键事件和专业问题"""
    __tablename__ = 'edu_scenario_data'
    __table_args__ = {'comment': '情境区主数据表'}

    scenario_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='情境区数据主键ID')
    record_id = Column(BigInteger, nullable=False, comment='关联的学习记录ID，关联edu_learning_record.record_id')
    student_id = Column(BigInteger, nullable=False, comment='学生用户ID，关联sys_user.user_id')
    # 学生输入的原始场景描述
    description = Column(Text, comment='学生撰写的实践场景描述正文，建议300-800字')
    # AI分析结果（LLM返回后存储）
    key_events = Column(JSONB, comment='AI识别的关键事件节点列表，JSON数组如[{"index":1,"event":"张大爷情绪失控"}]')
    identified_problems = Column(JSONB, comment='AI识别的专业问题列表，JSON数组如[{"title":"服务对象阻抗","domain":"老年社工"}]')
    category_tags = Column(JSONB, comment='场景分类标签，JSON数组如["老年社工","危机干预"]，AI自动推荐+学生确认')
    # 状态控制
    status = Column(CHAR(1), server_default='0', comment='情境区状态（0草稿/编辑中 1已确认，确认后可进入决策区）')
    del_flag = Column(CHAR(1), server_default='0', comment='删除标志（0存在 2删除）')
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')
    update_time = Column(DateTime, default=datetime.now, comment='最后更新时间')


class EduScenarioDialogue(Base):
    """情境区AI对话记录 —— 存储学生与AI在情境区的追问交互历史"""
    __tablename__ = 'edu_scenario_dialogue'
    __table_args__ = {'comment': '情境区AI对话记录'}

    dialogue_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='对话记录主键ID')
    scenario_id = Column(BigInteger, nullable=False, comment='关联的情境区数据ID，关联edu_scenario_data.scenario_id')
    role = Column(String(20), nullable=False, comment='发言角色（user学生 / assistant AI助手）')
    content = Column(Text, nullable=False, comment='对话内容，学生输入的消息或AI返回的分析/追问文本')
    dialogue_type = Column(String(30), comment='对话类型（analyze首次AI分析 / followup AI追问 / user_reply学生回复）')
    create_time = Column(DateTime, default=datetime.now, comment='对话创建时间')
