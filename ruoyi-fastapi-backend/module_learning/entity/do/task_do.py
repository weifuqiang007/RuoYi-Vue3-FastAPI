from datetime import datetime

from sqlalchemy import CHAR, BigInteger, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from config.database import Base


class EduTask(Base):
    __tablename__ = 'edu_task'
    __table_args__ = {'comment': '教学任务表'}

    task_id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_name = Column(String(200), nullable=False)
    task_description = Column(Text)
    teacher_id = Column(BigInteger, nullable=False)
    preset_scenario = Column(Text)
    scenario_kb_ids = Column(JSONB)
    decision_kb_ids = Column(JSONB)
    reflection_kb_ids = Column(JSONB)
    research_kb_ids = Column(JSONB)
    scenario_config = Column(JSONB)
    reflection_config = Column(JSONB)
    deadline = Column(DateTime)
    status = Column(CHAR(1), server_default='0')
    del_flag = Column(CHAR(1), server_default='0')
    create_by = Column(String(64), server_default='')
    create_time = Column(DateTime, default=datetime.now)
    update_by = Column(String(64), server_default='')
    update_time = Column(DateTime, default=datetime.now)


class EduTaskClass(Base):
    __tablename__ = 'edu_task_class'
    __table_args__ = {'comment': '任务-班级分配表'}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_id = Column(BigInteger, nullable=False)
    dept_id = Column(BigInteger, nullable=False)
    create_time = Column(DateTime, default=datetime.now)
