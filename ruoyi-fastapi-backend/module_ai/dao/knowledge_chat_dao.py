"""知识对话数据库操作层。"""

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from module_ai.entity.do.knowledge_chat_do import KbChatCitation, KbChatMessage, KbChatSession


class KnowledgeChatDao:
    """知识对话会话/消息/引用的数据库访问"""

    # ── 会话 ──────────────────────────────────────────────
    @classmethod
    async def get_session(cls, db: AsyncSession, session_id: str) -> KbChatSession | None:
        """按会话ID取未删除会话。"""
        result = await db.execute(
            select(KbChatSession).where(
                KbChatSession.session_id == session_id,
                KbChatSession.del_flag == '0',
            )
        )
        return result.scalars().first()

    @classmethod
    async def create_session(cls, db: AsyncSession, session: KbChatSession) -> KbChatSession:
        """新增会话并刷新主键。"""
        db.add(session)
        await db.flush()
        return session

    @classmethod
    async def list_sessions(
        cls, db: AsyncSession, user_id: int, page_num: int, page_size: int
    ) -> tuple[list[KbChatSession], int]:
        """分页列出当前用户的未删除会话，按最后更新时间倒序。"""
        cond = select(KbChatSession).where(
            KbChatSession.user_id == user_id,
            KbChatSession.del_flag == '0',
        )
        total = (await db.execute(select(func.count('*')).select_from(cond.subquery()))).scalar() or 0
        result = await db.execute(
            cond.order_by(KbChatSession.update_time.desc())
            .offset((page_num - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    @classmethod
    async def update_session(cls, db: AsyncSession, session_id: str, **kwargs) -> None:
        """按会话ID更新字段（UPDATE 语句，不依赖 ORM 对象生命周期）。"""
        await db.execute(update(KbChatSession).where(KbChatSession.session_id == session_id).values(**kwargs))

    # ── 消息 ──────────────────────────────────────────────
    @classmethod
    async def add_message(cls, db: AsyncSession, message: KbChatMessage) -> KbChatMessage:
        """新增消息并刷新主键。"""
        db.add(message)
        await db.flush()
        return message

    @classmethod
    async def get_message(cls, db: AsyncSession, message_id: int) -> KbChatMessage | None:
        """按消息ID取消息。"""
        result = await db.execute(select(KbChatMessage).where(KbChatMessage.message_id == message_id))
        return result.scalars().first()

    @classmethod
    async def update_message(cls, db: AsyncSession, message_id: int, **kwargs) -> None:
        """按消息ID更新字段（UPDATE 语句，不依赖 ORM 对象生命周期）。"""
        await db.execute(update(KbChatMessage).where(KbChatMessage.message_id == message_id).values(**kwargs))

    @classmethod
    async def get_message_by_client_request_id(
        cls, db: AsyncSession, session_id: str, client_request_id: str
    ) -> KbChatMessage | None:
        """按会话+幂等请求ID查用户消息，用于防重复提交。"""
        result = await db.execute(
            select(KbChatMessage).where(
                KbChatMessage.session_id == session_id,
                KbChatMessage.role == 'user',
                KbChatMessage.client_request_id == client_request_id,
            )
        )
        return result.scalars().first()

    @classmethod
    async def list_messages(
        cls, db: AsyncSession, session_id: str, page_num: int, page_size: int
    ) -> tuple[list[KbChatMessage], int]:
        """按时间正序分页取会话消息。"""
        cond = select(KbChatMessage).where(KbChatMessage.session_id == session_id)
        total = (await db.execute(select(func.count('*')).select_from(cond.subquery()))).scalar() or 0
        result = await db.execute(
            cond.order_by(KbChatMessage.message_id.asc())
            .offset((page_num - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    @classmethod
    async def get_recent_messages(cls, db: AsyncSession, session_id: str, limit: int = 12) -> list[KbChatMessage]:
        """取会话最近若干条消息（用于构建追问上下文）。"""
        result = await db.execute(
            select(KbChatMessage)
            .where(KbChatMessage.session_id == session_id)
            .order_by(KbChatMessage.message_id.desc())
            .limit(limit)
        )
        return list(reversed(result.scalars().all()))

    # ── 引用 ──────────────────────────────────────────────
    @classmethod
    async def add_citations(cls, db: AsyncSession, citations: list[KbChatCitation]) -> None:
        """批量新增引用。"""
        db.add_all(citations)
        await db.flush()

    @classmethod
    async def list_citations(cls, db: AsyncSession, message_id: int) -> list[KbChatCitation]:
        """按编号正序取消息的引用列表。"""
        result = await db.execute(
            select(KbChatCitation)
            .where(KbChatCitation.message_id == message_id)
            .order_by(KbChatCitation.citation_no.asc())
        )
        return list(result.scalars().all())

    @classmethod
    async def get_citation(cls, db: AsyncSession, message_id: int, citation_no: int) -> KbChatCitation | None:
        """取单条引用。"""
        result = await db.execute(
            select(KbChatCitation).where(
                KbChatCitation.message_id == message_id,
                KbChatCitation.citation_no == citation_no,
            )
        )
        return result.scalars().first()
