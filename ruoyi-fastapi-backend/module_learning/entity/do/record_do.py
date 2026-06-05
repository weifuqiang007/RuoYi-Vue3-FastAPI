from datetime import datetime

from sqlalchemy import CHAR, BigInteger, Column, DateTime, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from config.database import Base


class EduLearningRecord(Base):
    __tablename__ = 'edu_learning_record'
    __table_args__ = {'comment': '学习记录主表（四区联动主控）'}

    record_id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_id = Column(BigInteger)
    student_id = Column(BigInteger, nullable=False)
    current_stage = Column(String(20), server_default='scenario')
    scenario_status = Column(CHAR(1), server_default='0')
    decision_status = Column(CHAR(1), server_default='0')
    reflection_status = Column(CHAR(1), server_default='0')
    research_status = Column(CHAR(1), server_default='0')
    scenario_id = Column(BigInteger)
    decision_id = Column(BigInteger)
    reflection_id = Column(BigInteger)
    research_id = Column(BigInteger)
    status = Column(String(20), server_default='ongoing')
    score = Column(Numeric(5, 2))
    teacher_feedback = Column(Text)
    start_time = Column(DateTime, default=datetime.now)
    submit_time = Column(DateTime)
    complete_time = Column(DateTime)
    del_flag = Column(CHAR(1), server_default='0')
    create_by = Column(String(64), server_default='')
    create_time = Column(DateTime, default=datetime.now)
    update_by = Column(String(64), server_default='')
    update_time = Column(DateTime, default=datetime.now)
