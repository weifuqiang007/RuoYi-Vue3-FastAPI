# module_rag/entity/vo/knowledge_base_vo.py
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_serializer


class KbScope(str, Enum):
    """知识库可见范围（见设计方案 §1.1）"""

    PUBLIC = 'public'      # 公共：admin 创建，全员可见
    SCHOOL = 'school'      # 学校级：教师创建，同校师生可见
    CLASS = 'class'        # 班级级：教师创建，本班学生 + 同校教师可见
    PERSONAL = 'personal'  # 个人级：学生创建，仅本人/归属老师/admin 可见


class KnowledgeBaseCreateModel(BaseModel):
    """创建知识库请求"""

    kb_name: str = Field(..., description='知识库名称')
    kb_desc: str | None = Field(None, description='知识库描述')
    embedding_model: str = Field(default='embedding-3', description='Embedding模型')
    chunk_size: int = Field(default=500, description='分块大小')
    chunk_overlap: int = Field(default=50, description='分块重叠')
    kb_scope: KbScope = Field(default=KbScope.PERSONAL, description='可见范围')
    scope_dept_id: int | None = Field(None, description='作用域部门ID（school/class 时必填）')


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
    kb_scope: KbScope = KbScope.PERSONAL
    scope_dept_id: int | None = None
    owner_user_id: int | None = None
    create_time: datetime | None = None

    class Config:
        from_attributes = True

    @field_serializer('create_time')
    @classmethod
    def serialize_create_time(cls, v: datetime | None) -> str | None:
        """将 datetime 序列化为字符串"""
        return str(v) if v else None
