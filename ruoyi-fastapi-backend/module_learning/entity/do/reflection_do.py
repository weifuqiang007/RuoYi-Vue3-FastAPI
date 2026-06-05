from datetime import datetime

from sqlalchemy import CHAR, BigInteger, Column, DateTime, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from config.database import Base


class EduReflectionData(Base):
    __tablename__ = 'edu_reflection_data'
    __table_args__ = {'comment': '反思区主数据表'}

    reflection_id = Column(BigInteger, primary_key=True, autoincrement=True)
    record_id = Column(BigInteger, nullable=False)
    scenario_id = Column(BigInteger, nullable=False)
    student_id = Column(BigInteger, nullable=False)
    content = Column(Text)
    depth_level = Column(String(20), server_default='descriptive')
    depth_score = Column(Numeric(3, 2), server_default='0.00')
    linked_theories = Column(JSONB)
    version = Column(Integer, server_default='1')
    status = Column(CHAR(1), server_default='0')
    del_flag = Column(CHAR(1), server_default='0')
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now)


class EduReflectionDialogue(Base):
    __tablename__ = 'edu_reflection_dialogue'
    __table_args__ = {'comment': '反思区AI对话记录'}

    dialogue_id = Column(BigInteger, primary_key=True, autoincrement=True)
    reflection_id = Column(BigInteger, nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    question_level = Column(String(20))
    depth_score_before = Column(Numeric(3, 2))
    depth_score_after = Column(Numeric(3, 2))
    linked_theories = Column(JSONB)
    create_time = Column(DateTime, default=datetime.now)


class EduReflectionDepthHistory(Base):
    __tablename__ = 'edu_reflection_depth_history'
    __table_args__ = {'comment': '反思深度演变历史'}

    history_id = Column(BigInteger, primary_key=True, autoincrement=True)
    reflection_id = Column(BigInteger, nullable=False)
    depth_score = Column(Numeric(3, 2), nullable=False)
    depth_level = Column(String(20), nullable=False)
    trigger_type = Column(String(30))
    create_time = Column(DateTime, default=datetime.now)
