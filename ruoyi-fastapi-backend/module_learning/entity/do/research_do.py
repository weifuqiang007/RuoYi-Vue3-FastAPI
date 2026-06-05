from datetime import datetime

from sqlalchemy import CHAR, BigInteger, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from config.database import Base


class EduResearchData(Base):
    __tablename__ = 'edu_research_data'
    __table_args__ = {'comment': '研究生成区主数据表'}

    research_id = Column(BigInteger, primary_key=True, autoincrement=True)
    record_id = Column(BigInteger, nullable=False)
    student_id = Column(BigInteger, nullable=False)
    material_summary = Column(Text)
    candidate_questions = Column(JSONB)
    selected_question = Column(Text)
    framework = Column(JSONB)
    ref_literature = Column(JSONB)
    status = Column(CHAR(1), server_default='0')
    del_flag = Column(CHAR(1), server_default='0')
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now)


class EduResearchChapter(Base):
    __tablename__ = 'edu_research_chapter'
    __table_args__ = {'comment': '研究区章节表'}

    chapter_id = Column(BigInteger, primary_key=True, autoincrement=True)
    research_id = Column(BigInteger, nullable=False)
    chapter_index = Column(Integer, nullable=False)
    chapter_title = Column(String(200))
    content = Column(Text)
    ai_suggestion = Column(Text)
    status = Column(CHAR(1), server_default='0')
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now)
