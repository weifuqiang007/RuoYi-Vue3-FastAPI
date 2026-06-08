from datetime import datetime

from sqlalchemy import CHAR, BigInteger, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from config.database import Base


class EduResearchData(Base):
    """研究生成区主数据表 —— 存储AI生成的候选研究问题、学生选定的论题、论文框架和推荐文献"""
    __tablename__ = 'edu_research_data'
    __table_args__ = {'comment': '研究生成区主数据表'}

    research_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='研究区数据主键ID')
    record_id = Column(BigInteger, nullable=False, comment='关联的学习记录ID，关联edu_learning_record.record_id')
    student_id = Column(BigInteger, nullable=False, comment='学生用户ID，关联sys_user.user_id')
    # 材料汇总（系统自动生成，学生可编辑）
    material_summary = Column(Text, comment='前三区材料的综合摘要，初始化时由系统从情境+决策+反思数据中自动聚合')
    # 研究问题
    candidate_questions = Column(JSONB, comment='AI生成的候选研究问题列表，JSON数组如[{"question":"...","rationale":"...","approach":"..."}]')
    selected_question = Column(Text, comment='学生最终选定的研究问题文本（也可自行拟定）')
    # 论文框架与文献
    framework = Column(JSONB, comment='论文大纲结构，JSON数组如[{"index":1,"title":"绪论","description":"章节说明"}]')
    ref_literature = Column(JSONB, comment='AI推荐的相关文献列表（字段名避开PostgreSQL保留字references）')
    # 状态控制
    status = Column(CHAR(1), server_default='0', comment='研究区状态（0进行中 1已提交）')
    del_flag = Column(CHAR(1), server_default='0', comment='删除标志（0存在 2删除）')
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')
    update_time = Column(DateTime, default=datetime.now, comment='最后更新时间')


class EduResearchChapter(Base):
    """研究区章节表 —— 论文每个章节独立存储，避免单个JSONB大字段的并发写入问题"""
    __tablename__ = 'edu_research_chapter'
    __table_args__ = {'comment': '研究区章节表'}

    chapter_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='章节主键ID')
    research_id = Column(BigInteger, nullable=False, comment='关联的研究区数据ID，关联edu_research_data.research_id')
    chapter_index = Column(Integer, nullable=False, comment='章节序号，从1开始，对应framework中的index')
    chapter_title = Column(String(200), comment='章节标题，如"绪论"、"文献综述"等')
    content = Column(Text, comment='学生撰写的章节正文内容')
    ai_suggestion = Column(Text, comment='AI为该章节生成的写作建议和段落草稿')
    status = Column(CHAR(1), server_default='0', comment='章节状态（0草稿 1已完成）')
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')
    update_time = Column(DateTime, default=datetime.now, comment='最后更新时间')
