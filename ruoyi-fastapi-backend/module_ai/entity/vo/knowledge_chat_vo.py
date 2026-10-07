"""知识对话（社会工作教学与研究助手）接口模型。

所有字段使用驼峰别名（alias_generator=to_camel），数据库大整数ID在前端以字符串传输。
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class KbChatSessionCreateModel(BaseModel):
    """创建知识对话会话请求"""

    model_config = ConfigDict(alias_generator=to_camel)

    kb_ids: list[str] = Field(default_factory=list, description='知识库ID列表，如["12","18"]')


class KbChatSessionModel(BaseModel):
    """知识对话会话响应"""

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    session_id: str = Field(description='会话ID')
    title: str | None = Field(default=None, description='会话标题')
    kb_ids: list[int] | None = Field(default=None, description='知识库ID列表')
    last_answer_mode: str | None = Field(default=None, description='最近一次已接受请求的回答模式（professional/public）')
    created_at: datetime | None = Field(default=None, description='创建时间')
    updated_at: datetime | None = Field(default=None, description='最后更新时间')


class KbChatSessionPageQueryModel(BaseModel):
    """知识对话会话分页查询"""

    model_config = ConfigDict(alias_generator=to_camel)

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=20, description='每页记录数')


class KbChatCitationModel(BaseModel):
    """知识对话引用模型"""

    model_config = ConfigDict(alias_generator=to_camel)

    citation_no: int = Field(description='消息内引用编号')
    doc_id: int | None = Field(default=None, description='文档ID')
    chunk_id: int | None = Field(default=None, description='分块ID')
    kb_id: int | None = Field(default=None, description='知识库ID')
    title: str | None = Field(default=None, description='文献标题')
    source_type: str | None = Field(default=None, description='文献类型（textbook/article/other）')
    authors: list[str] | None = Field(default=None, description='作者列表')
    heading_path: list[str] | None = Field(default=None, description='章节路径')
    page_label: str | None = Field(default=None, description='页码标签')
    locator_type: str | None = Field(default=None, description='定位类型（section/page/none）')
    excerpt: str | None = Field(default=None, description='原文片段，仅鉴权通过后返回')
    evidence_type: str | None = Field(default=None, description='依据类别（direct 直接依据 background 背景参考）')
    supports: list[dict] | None = Field(default=None, description='正文支持关系，如[{"statement":"...","relation":"background"}]')
    application_note: str | None = Field(default=None, description='适用限制说明')
    availability: Literal['available', 'unavailable'] = Field(
        default='available', description='可用性（available 可访问 unavailable 已不可访问）'
    )


class KbChatMessageModel(BaseModel):
    """知识对话消息响应"""

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    message_id: int | None = Field(default=None, description='消息ID')
    session_id: str | None = Field(default=None, description='会话ID')
    role: str | None = Field(default=None, description='角色（user/assistant）')
    content: str | None = Field(default=None, description='消息内容')
    status: str | None = Field(default=None, description='状态（generating/completed/failed/cancelled）')
    answer_type: str | None = Field(default=None, description='回答类型（grounded/general/insufficient/clarification）')
    citation_status: str | None = Field(default=None, description='引用状态（pending/valid/needs_review/not_applicable）')
    retrieval_status: str | None = Field(default=None, description='检索状态（matched/no_match/failed/not_attempted）')
    answer_mode: str | None = Field(default=None, description='回答模式（professional/public）')
    citations: list[KbChatCitationModel] | None = Field(default=None, description='引用列表')
    created_at: datetime | None = Field(default=None, description='创建时间')


class KbChatStreamRequestModel(BaseModel):
    """知识对话流式发送请求"""

    model_config = ConfigDict(alias_generator=to_camel)

    session_id: str | None = Field(default=None, description='会话ID，为空则新建会话')
    content: str = Field(description='用户消息内容')
    kb_ids: list[str] = Field(default_factory=list, description='本轮知识库ID列表')
    answer_mode: Literal['professional', 'public'] = Field(
        default='professional', description='回答模式（professional 专业研讨 public 日常求助）'
    )
    client_request_id: str = Field(description='前端幂等请求ID，同一请求重复提交只生成一次')
    retry_of_message_id: int | None = Field(default=None, description='重试来源的助手消息ID')
