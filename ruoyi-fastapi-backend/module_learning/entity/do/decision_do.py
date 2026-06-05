from datetime import datetime

from sqlalchemy import CHAR, BigInteger, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from config.database import Base


class EduDecisionData(Base):
    __tablename__ = 'edu_decision_data'
    __table_args__ = {'comment': '决策区数据表'}

    decision_id = Column(BigInteger, primary_key=True, autoincrement=True)
    record_id = Column(BigInteger, nullable=False)
    scenario_id = Column(BigInteger, nullable=False)
    student_id = Column(BigInteger, nullable=False)
    key_event_index = Column(Integer)
    key_event_desc = Column(Text)
    is_intervened = Column(Boolean)
    action_taken = Column(Text)
    reasoning = Column(Text)
    psychological_state = Column(Text)
    alternatives = Column(Text)
    expected_outcome = Column(Text)
    actual_outcome = Column(Text)
    ethics_analysis = Column(JSONB)
    status = Column(CHAR(1), server_default='0')
    del_flag = Column(CHAR(1), server_default='0')
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now)


class EduDecisionDialogue(Base):
    __tablename__ = 'edu_decision_dialogue'
    __table_args__ = {'comment': '决策区AI对话记录'}

    dialogue_id = Column(BigInteger, primary_key=True, autoincrement=True)
    decision_id = Column(BigInteger, nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    dialogue_type = Column(String(30))
    create_time = Column(DateTime, default=datetime.now)
