"""知识对话（社会工作教学与研究助手）数据实体。

面向高校社会工作专业教师/研究人员的知识问答，核心闭环：
提问 → 授权知识库检索 → 流式回答（理论论断附引用）→ 查看原文 → 继续追问。
本模块只保存「会话、消息、引用快照」三类数据，检索与生成复用 module_rag 与 model 工厂。
"""

from datetime import datetime

from sqlalchemy import CHAR, BigInteger, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from config.database import Base


class KbChatSession(Base):
    """知识对话会话表 —— 记录会话归属与所选知识库范围，多轮问答围绕同一会话展开"""

    __tablename__ = 'kb_chat_session'
    __table_args__ = {'comment': '知识对话会话表'}

    session_id = Column(String(64), primary_key=True, nullable=False, comment='会话ID，UUID十六进制字符串')
    user_id = Column(BigInteger, nullable=False, index=True, comment='会话归属用户ID，关联sys_user.user_id')
    title = Column(String(200), server_default='', comment='会话标题，默认取首条问题前20个字符')
    kb_ids = Column(JSONB, comment='知识库ID列表，JSON数组如[1,2]，决定本轮可检索的知识库范围')
    last_answer_mode = Column(
        String(20), comment='最近一次已接受请求的回答模式（professional/public），旧会话为NULL按professional'
    )
    del_flag = Column(CHAR(1), server_default='0', comment='删除标志（0存在 2删除）')
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='最后更新时间')


class KbChatMessage(Base):
    """知识对话消息表 —— 会话内的用户问题与助手回答，含生成状态与引用校验状态"""

    __tablename__ = 'kb_chat_message'
    __table_args__ = {'comment': '知识对话消息表'}

    message_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='消息主键ID')
    session_id = Column(String(64), nullable=False, index=True, comment='会话ID，关联kb_chat_session.session_id')
    role = Column(String(20), nullable=False, comment='角色（user 用户 assistant 助手）')
    content = Column(Text, comment='消息内容')
    status = Column(
        String(20),
        server_default='completed',
        comment='状态（generating 生成中 completed 已完成 failed 失败 cancelled 已取消）',
    )
    answer_type = Column(
        String(20), comment='回答类型（grounded 有依据 insufficient 依据不足 clarification 澄清）'
    )
    citation_status = Column(
        String(20),
        comment='引用状态（pending 待确认 valid 有效 needs_review 需核验 not_applicable 不适用）',
    )
    client_request_id = Column(String(64), comment='前端幂等请求ID，防止重复提交重复生成')
    request_kb_ids = Column(JSONB, comment='本轮请求的知识库ID列表，JSON数组如[1,2]，用于幂等冲突检测')
    retry_of_message_id = Column(BigInteger, comment='重试来源的助手消息ID，非重试为NULL')
    model_name = Column(String(100), comment='生成本条回答的模型名称')
    retrieval_status = Column(
        String(20),
        comment='检索状态（matched 有命中 no_match 零命中 failed 检索失败 not_attempted 未检索）',
    )
    answer_mode = Column(
        String(20),
        server_default='professional',
        comment='回答模式（professional 专业研讨 public 日常求助）',
    )
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')


class KbChatCitation(Base):
    """知识对话引用表 —— 助手回答正文中[编号]对应的原文证据快照，引用打开时二次鉴权"""

    __tablename__ = 'kb_chat_citation'
    __table_args__ = {'comment': '知识对话引用表'}

    citation_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='引用主键ID')
    message_id = Column(BigInteger, nullable=False, index=True, comment='消息ID，关联kb_chat_message.message_id')
    citation_no = Column(Integer, nullable=False, comment='消息内引用编号，如1/2/3')
    doc_id = Column(BigInteger, comment='文档ID，关联rag_document.doc_id')
    chunk_id = Column(BigInteger, comment='分块ID，关联rag_chunk.chunk_id')
    kb_id = Column(BigInteger, comment='知识库ID，关联rag_knowledge_base.kb_id')
    title = Column(String(255), comment='文献标题（教材/文章正式名称）')
    source_type = Column(String(20), comment='文献类型（textbook 教材 article 文章 other 其他）')
    authors = Column(JSONB, comment='作者列表，JSON数组如["张三"]')
    heading_path = Column(JSONB, comment='章节路径，JSON数组如["第三章","第二节"]')
    page_label = Column(String(50), comment='页码标签，如"PDF 第 3 页"')
    locator_type = Column(String(20), comment='定位类型（section 章节 page 页码 none 未记录）')
    excerpt = Column(Text, comment='本次实际提供给模型的原文片段，打开引用时经鉴权后返回')
    evidence_type = Column(
        String(20), comment='依据类别（direct 直接依据 background 背景参考）'
    )
    supports = Column(
        JSONB, comment='正文支持关系，JSON数组如[{"statement":"...","relation":"background"}]'
    )
    application_note = Column(Text, comment='适用限制说明，如“该片段提供理解视角，不直接证明某项具体应对方法”')
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')
