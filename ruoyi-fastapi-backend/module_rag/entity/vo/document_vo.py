# module_rag/entity/vo/document_vo.py
from datetime import datetime

from pydantic import BaseModel, Field, field_serializer


class DocumentUploadModel(BaseModel):
    """文档上传请求"""
    kb_id: int = Field(..., description='知识库ID')


class DocumentResponseModel(BaseModel):
    """文档响应"""
    doc_id: int
    kb_id: int
    doc_name: str
    file_type: str | None = None
    file_size: int = 0
    chunk_count: int = 0
    parse_status: str = '0'
    embed_status: str = '0'
    error_msg: str | None = None
    create_time: datetime | None = None

    class Config:
        from_attributes = True

    @field_serializer('create_time')
    @classmethod
    def serialize_create_time(cls, v: datetime | None) -> str | None:
        """将 datetime 序列化为字符串"""
        return str(v) if v else None
