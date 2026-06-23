# module_rag/entity/vo/chunk_vo.py
from datetime import datetime

from pydantic import BaseModel, Field, field_serializer


class ChunkResponseModel(BaseModel):
    """分块响应"""
    chunk_id: int
    doc_id: int
    kb_id: int
    chunk_index: int
    content: str
    token_count: int = 0
    create_time: datetime | None = None

    class Config:
        from_attributes = True

    @field_serializer('create_time')
    @classmethod
    def serialize_create_time(cls, v: datetime | None) -> str | None:
        """将 datetime 序列化为字符串"""
        return str(v) if v else None


class ChunkUpdateModel(BaseModel):
    """分块内容更新请求"""
    chunk_id: int = Field(..., description='分块ID')
    content: str = Field(..., description='修改后的分块内容')
