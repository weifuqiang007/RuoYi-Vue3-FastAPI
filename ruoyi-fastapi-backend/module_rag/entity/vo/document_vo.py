# module_rag/entity/vo/document_vo.py
from datetime import datetime

from pydantic import BaseModel, Field, field_serializer


class DocumentUploadModel(BaseModel):
    """文档上传请求"""
    kb_id: int = Field(..., description='知识库ID')


class DocumentMetadataUpdateModel(BaseModel):
    """文档书目元数据更新请求（F08：最小文献信息维护）"""

    doc_id: int = Field(..., description='文档ID')
    source_type: str | None = Field(None, description='文献类型（textbook/article/other）')
    title: str | None = Field(None, description='正式文献标题')
    authors: list[str] | None = Field(None, description='作者列表')
    publication_year: int | None = Field(None, description='出版/发表年份')
    edition: str | None = Field(None, description='版次')
    publisher_or_journal: str | None = Field(None, description='出版社/期刊名')
    doi_or_url: str | None = Field(None, description='DOI或URL')


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
    source_type: str | None = None
    title: str | None = None
    authors: list[str] | None = None
    publication_year: int | None = None
    edition: str | None = None
    publisher_or_journal: str | None = None
    doi_or_url: str | None = None
    create_time: datetime | None = None

    class Config:
        from_attributes = True

    @field_serializer('create_time')
    @classmethod
    def serialize_create_time(cls, v: datetime | None) -> str | None:
        """将 datetime 序列化为字符串"""
        return str(v) if v else None
