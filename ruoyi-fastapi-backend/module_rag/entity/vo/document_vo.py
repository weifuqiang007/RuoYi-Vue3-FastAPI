# module_rag/entity/vo/document_vo.py
from pydantic import BaseModel, Field


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
    create_time: str | None = None

    class Config:
        from_attributes = True