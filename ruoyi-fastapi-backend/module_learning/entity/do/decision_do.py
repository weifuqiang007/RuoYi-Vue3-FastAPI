from datetime import datetime

from sqlalchemy import CHAR, BigInteger, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from config.database import Base


class EduDecisionData(Base):
    """决策区数据表 —— 每个关键事件节点对应一条决策记录，存储学生的伦理决策分析和AI伦理评估结果"""
    __tablename__ = 'edu_decision_data'
    __table_args__ = {'comment': '决策区数据表（每个关键事件节点一条）'}

    decision_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='决策记录主键ID')
    record_id = Column(BigInteger, nullable=False, comment='关联的学习记录ID，关联edu_learning_record.record_id')
    scenario_id = Column(BigInteger, nullable=False, comment='关联的情境区数据ID，关联edu_scenario_data.scenario_id')
    student_id = Column(BigInteger, nullable=False, comment='学生用户ID，关联sys_user.user_id')
    # 关联情境区的关键事件（从情境区的key_events中选取）
    key_event_index = Column(Integer, comment='关联的关键事件在key_events数组中的索引序号，从0开始')
    key_event_desc = Column(Text, comment='关键事件描述文本（冗余存储，方便直接展示，无需回查情境区）')
    # 学生填写的结构化决策内容
    is_intervened = Column(Boolean, comment='是否决定介入（true介入 / false不介入）')
    action_taken = Column(Text, comment='学生采取的具体行动描述')
    reasoning = Column(Text, comment='学生选择该行动的理由和依据')
    psychological_state = Column(Text, comment='决策时学生的心理活动和感受')
    alternatives = Column(Text, comment='学生考虑过但未采用的替代方案')
    expected_outcome = Column(Text, comment='学生预期的行动结果')
    actual_outcome = Column(Text, comment='行动后实际发生的结果（事后补充填写）')
    # AI分析结果
    ethics_analysis = Column(JSONB, comment='AI伦理分析结果，JSON对象含ethics_dimensions/relevant_codes/analysis/further_questions')
    # 状态控制
    status = Column(CHAR(1), server_default='0', comment='决策记录状态（0草稿 1已完成）')
    del_flag = Column(CHAR(1), server_default='0', comment='删除标志（0存在 2删除）')
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')
    update_time = Column(DateTime, default=datetime.now, comment='最后更新时间')


class EduDecisionDialogue(Base):
    """决策区AI对话记录 —— 存储学生与AI在决策区的伦理分析交互历史"""
    __tablename__ = 'edu_decision_dialogue'
    __table_args__ = {'comment': '决策区AI对话记录'}

    dialogue_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='对话记录主键ID')
    decision_id = Column(BigInteger, nullable=False, comment='关联的决策记录ID，关联edu_decision_data.decision_id')
    role = Column(String(20), nullable=False, comment='发言角色（user学生 / assistant AI助手）')
    content = Column(Text, nullable=False, comment='对话内容，学生提问或AI返回的伦理分析/建议')
    dialogue_type = Column(String(30), comment='对话类型（ethics_analyze伦理分析 / alternative替代方案 / followup追问）')
    create_time = Column(DateTime, default=datetime.now, comment='对话创建时间')
