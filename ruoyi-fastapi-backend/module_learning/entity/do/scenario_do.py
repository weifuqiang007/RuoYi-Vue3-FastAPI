from datetime import datetime

from sqlalchemy import CHAR, BigInteger, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from config.database import Base


class EduScenarioData(Base):
    __tablename__ = 'edu_scenario_data'
    __table_args__ = {'comment': '情境区主数据表'}

    scenario_id = Column(BigInteger, primary_key=True, autoincrement=True)
    record_id = Column(BigInteger, nullable=False)
    student_id = Column(BigInteger, nullable=False)
    description = Column(Text)
    key_events = Column(JSONB)
    identified_problems = Column(JSONB)
    category_tags = Column(JSONB)
    status = Column(CHAR(1), server_default='0')
    del_flag = Column(CHAR(1), server_default='0')
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now)


class EduScenarioDialogue(Base):
    __tablename__ = 'edu_scenario_dialogue'
    __table_args__ = {'comment': '情境区AI对话记录'}

    dialogue_id = Column(BigInteger, primary_key=True, autoincrement=True)
    scenario_id = Column(BigInteger, nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    dialogue_type = Column(String(30))
    create_time = Column(DateTime, default=datetime.now)
