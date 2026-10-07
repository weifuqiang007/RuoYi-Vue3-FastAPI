# module_rag/entity/do/document_do.py
from datetime import datetime

from sqlalchemy import CHAR, BigInteger, Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB

from config.database import Base


class RagDocument(Base):
    """RAG文档表"""
    __tablename__ = 'rag_document'
    __table_args__ = {'comment': 'RAG文档表'}

    doc_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='文档主键')
    kb_id = Column(BigInteger, nullable=False, comment='知识库ID')
    doc_name = Column(String(255), nullable=False, comment='文档名称')
    file_path = Column(String(500), nullable=False, comment='文件路径')
    file_type = Column(String(20), nullable=True, comment='文件类型')
    file_size = Column(BigInteger, nullable=True, server_default='0', comment='文件大小')
    chunk_count = Column(Integer, nullable=True, server_default='0', comment='分块数量')
    parse_status = Column(CHAR(1), nullable=True, server_default='0', comment='解析状态')
    embed_status = Column(CHAR(1), nullable=True, server_default='0', comment='向量化状态')
    error_msg = Column(String(500), nullable=True, comment='错误信息')
    user_id = Column(BigInteger, nullable=True, comment='用户ID')
    dept_id = Column(BigInteger, nullable=True, comment='部门ID')
    # ── 书目元数据（社会工作教学与研究助手引用展示用，上传者/管理员可编辑）──
    source_type = Column(String(20), nullable=True, comment='文献类型（textbook 教材 article 文章 other 其他）')
    title = Column(String(255), nullable=True, comment='正式文献标题，区别于上传文件名 doc_name')
    authors = Column(JSONB, nullable=True, comment='作者列表，JSON数组如["张三"]')
    publication_year = Column(Integer, nullable=True, comment='出版/发表年份')
    edition = Column(String(50), nullable=True, comment='版次')
    publisher_or_journal = Column(String(255), nullable=True, comment='出版社/期刊名')
    doi_or_url = Column(String(500), nullable=True, comment='DOI或URL')
    del_flag = Column(CHAR(1), nullable=True, server_default='0', comment='删除标志')
    create_by = Column(String(64), nullable=True, server_default="''", comment='创建者')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    update_by = Column(String(64), nullable=True, server_default="''", comment='更新者')
    update_time = Column(DateTime, nullable=True, default=datetime.now, comment='更新时间')
