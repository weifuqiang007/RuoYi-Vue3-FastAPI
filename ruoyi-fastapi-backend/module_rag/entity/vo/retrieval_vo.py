# module_rag/entity/vo/retrieval_vo.py
from pydantic import BaseModel, Field


class RetrievalRequestModel(BaseModel):
    """检索请求"""
    query: str = Field(..., description='检索查询文本')
    kb_ids: list[int] = Field(..., description='知识库ID列表')
    top_k: int = Field(default=5, description='返回数量')


class ChunkResponseModel(BaseModel):
    """分块响应"""
    chunk_id: int
    doc_id: int
    kb_id: int
    content: str
    token_count: int = 0
    score: float | None = None
    metadata: dict | None = None

    class Config:
        from_attributes = True