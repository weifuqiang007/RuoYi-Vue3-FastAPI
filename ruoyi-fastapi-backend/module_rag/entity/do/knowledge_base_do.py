# module_rag/entity/do/knowledge_base_do.py

from datetime import datetime
from sqlalchemy import CHAR, BigInteger, Column, DateTime, Integer, String, Text
from config.database import Base
from config.env import DataBaseConfig
from utils.common_util import SqlalchemyUtil

class RagKnowledgeBase(Base):
    """rag知识库表"""
    __tablename__ = 'rag_knowledge_base'
    __table_args__ = {'comment':'rag知识库表'}

    kb_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='知识库主键')
    kb_name = Column(String(100), nullable=False, comment='知识库名称')
    kb_desc = Column(String(500), nullable=True, comment='知识库描述')
    embedding_model = Column(String(100), nullable=True, server_default='embedding-3', comment='Embedding模型')
    chunk_size = Column(Integer, nullable=True, server_default='500', comment='分块大小')
    chunk_overlap = Column(Integer, nullable=True, server_default='50', comment='分块重叠')
    doc_count = Column(Integer, nullable=True, server_default='0', comment='文档数量')
    status = Column(CHAR(1), nullable=True, server_default='0', comment='状态')
    dept_id = Column(BigInteger, nullable=True, comment='部门ID')
    user_id = Column(BigInteger, nullable=True, comment='用户ID')
    del_flag = Column(CHAR(1), nullable=True, server_default='0', comment='删除标志')
    create_by = Column(String(64), nullable=True, server_default="''", comment='创建者')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    update_by = Column(String(64), nullable=True, server_default="''", comment='更新者')
    update_time = Column(DateTime, nullable=True, default=datetime.now, comment='更新时间')
    remark = Column(String(500), nullable=True, comment='备注')
