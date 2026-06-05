# module_rag/entity/vo/knowledge_base_vo.py
from datetime import datetime

from pydantic import BaseModel, Field, field_serializer


class KnowledgeBaseCreateModel(BaseModel):
    """创建知识库请求"""

    kb_name: str = Field(..., description='知识库名称')
    kb_desc: str | None = Field(None, description='知识库描述')
    embedding_model: str = Field(default='embedding-3', description='Embedding模型')
    chunk_size: int = Field(default=500, description='分块大小')
    chunk_overlap: int = Field(default=50, description='分块重叠')


class KnowledgeBaseUpdateModel(BaseModel):
    """更新知识库请求"""

    kb_id: int = Field(..., description='知识库ID')
    kb_name: str | None = Field(None, description='知识库名称')
    kb_desc: str | None = Field(None, description='知识库描述')
    chunk_size: int | None = Field(None, description='分块大小')
    chunk_overlap: int | None = Field(None, description='分块重叠')


class KnowledgeBaseResponseModel(BaseModel):
    """知识库响应"""

    kb_id: int
    kb_name: str
    kb_desc: str | None = None
    embedding_model: str = 'embedding-3'
    chunk_size: int = 500
    chunk_overlap: int = 50
    doc_count: int = 0
    status: str = '0'
    create_time: datetime | None = None

    class Config:
        from_attributes = True

    @field_serializer('create_time')
    @classmethod
    def serialize_create_time(cls, v: datetime | None) -> str | None:
        """将 datetime 序列化为字符串"""
        return str(v) if v else None
