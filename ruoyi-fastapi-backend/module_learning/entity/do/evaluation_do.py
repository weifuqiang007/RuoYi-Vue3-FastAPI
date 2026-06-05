from datetime import datetime

from sqlalchemy import CHAR, BigInteger, Boolean, Column, DateTime, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from config.database import Base


class EduEvaluation(Base):
    __tablename__ = 'edu_evaluation'
    __table_args__ = {'comment': '教师评价表'}

    evaluation_id = Column(BigInteger, primary_key=True, autoincrement=True)
    record_id = Column(BigInteger, nullable=False)
    teacher_id = Column(BigInteger, nullable=False)
    scenario_score = Column(Numeric(5, 2))
    decision_score = Column(Numeric(5, 2))
    reflection_score = Column(Numeric(5, 2))
    research_score = Column(Numeric(5, 2))
    total_score = Column(Numeric(5, 2))
    scenario_feedback = Column(Text)
    decision_feedback = Column(Text)
    reflection_feedback = Column(Text)
    research_feedback = Column(Text)
    overall_feedback = Column(Text)
    is_excellent = Column(Boolean, server_default='false')
    status = Column(CHAR(1), server_default='0')
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now)


class EduExcellentCase(Base):
    __tablename__ = 'edu_excellent_case'
    __table_args__ = {'comment': '优秀案例库（匿名化）'}

    case_id = Column(BigInteger, primary_key=True, autoincrement=True)
    source_record_id = Column(BigInteger)
    task_id = Column(BigInteger, nullable=False)
    scenario_desc = Column(Text)
    decision_data = Column(JSONB)
    reflection_data = Column(Text)
    research_data = Column(Text)
    teacher_comment = Column(Text)
    tags = Column(JSONB)
    status = Column(CHAR(1), server_default='0')
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now)
