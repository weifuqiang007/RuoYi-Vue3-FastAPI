# module_rag/entity/do/chunk_do.py
from datetime import datetime
from sqlalchemy import CHAR, BigInteger, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from config.database import Base


class RagChunk(Base):
    """RAG文档分块表"""
    __tablename__ = 'rag_chunk'
    __table_args__ = {'comment': 'RAG文档分块表'}

    chunk_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='分块主键')
    doc_id = Column(BigInteger, nullable=False, comment='文档ID')
    kb_id = Column(BigInteger, nullable=False, comment='知识库ID')
    chunk_index = Column(Integer, nullable=False, comment='分块序号')
    content = Column(Text, nullable=False, comment='分块内容')
    token_count = Column(Integer, nullable=True, server_default='0', comment='Token数量')
    embedding = Column(Vector(1024), nullable=True, comment='文本向量')  # pgvector 向量字段（智谱 embedding-3 指定 dimensions=1024 输出）
    chunk_metadata = Column('metadata', JSONB, nullable=True, comment='元数据')
    del_flag = Column(CHAR(1), nullable=True, server_default='0', comment='删除标志')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')