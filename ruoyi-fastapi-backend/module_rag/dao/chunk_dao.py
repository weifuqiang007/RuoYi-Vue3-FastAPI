# module_rag/dao/chunk_dao.py
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only
from module_rag.entity.do.chunk_do import RagChunk


class ChunkDao:

    @classmethod
    async def bulk_insert(cls, db: AsyncSession, doc_id: int, kb_id: int, chunks: list[dict]) -> list[int]:
        """单次 flush 批量插入分块记录，并返回 chunk_id 列表。"""
        rag_chunks = [
            RagChunk(
                doc_id=doc_id,
                kb_id=kb_id,
                chunk_index=i,
                content=chunk['content'],
                token_count=chunk.get('token_count', len(chunk['content'])),
                chunk_metadata=chunk.get('metadata')
            )
            for i, chunk in enumerate(chunks)
        ]
        db.add_all(rag_chunks)
        await db.flush()
        return [chunk.chunk_id for chunk in rag_chunks]


    @classmethod
    async def bulk_update_embeddings(cls, db: AsyncSession, chunk_ids: list[int], embeddings: list[list[float]]):
        """批量更新向量字段"""
        for chunk_id, embedding in zip(chunk_ids, embeddings):
            await db.execute(
                update(RagChunk).where(RagChunk.chunk_id == chunk_id).values(embedding=embedding)
            )


    @classmethod
    async def get_by_doc_id(cls, db: AsyncSession, doc_id: int) -> list[RagChunk]:
        result = await db.execute(
            select(RagChunk).where(RagChunk.doc_id == doc_id, RagChunk.del_flag == '0').order_by(RagChunk.chunk_index)
        )
        return list(result.scalars().all())

    @classmethod
    async def get_page_by_doc_id(
        cls, db: AsyncSession, doc_id: int, page_num: int = 1, page_size: int = 20
    ) -> tuple[int, list[RagChunk]]:
        """
        分页查询某文档的分块。

        性能关键：用 load_only 只查展示用列，**排除 embedding 向量列**
        （1024 维向量约 4KB/条，大文档全量拉取会导致接口超时）。
        """
        base_filter = (RagChunk.doc_id == doc_id, RagChunk.del_flag == '0')

        total = (
            await db.execute(select(func.count(RagChunk.chunk_id)).where(*base_filter))
        ).scalar() or 0

        result = await db.execute(
            select(RagChunk)
            .options(load_only(
                RagChunk.chunk_id, RagChunk.doc_id, RagChunk.kb_id,
                RagChunk.chunk_index, RagChunk.content, RagChunk.token_count, RagChunk.create_time,
            ))
            .where(*base_filter)
            .order_by(RagChunk.chunk_index)
            .offset((page_num - 1) * page_size)
            .limit(page_size)
        )
        return total, list(result.scalars().all())

    @classmethod
    async def get_by_id(cls, db: AsyncSession, chunk_id: int) -> RagChunk | None:
        result = await db.execute(
            select(RagChunk).where(RagChunk.chunk_id == chunk_id, RagChunk.del_flag == '0')
        )
        return result.scalars().first()

    @classmethod
    async def update_content(cls, db: AsyncSession, chunk_id: int, content: str, token_count: int, embedding):
        """更新分块内容、token 数、向量（向量需调用方重新生成后传入）"""
        await db.execute(
            update(RagChunk)
            .where(RagChunk.chunk_id == chunk_id)
            .values(content=content, token_count=token_count, embedding=embedding)
        )

    @classmethod
    async def delete_by_doc_id(cls, db: AsyncSession, doc_id: int):
        """逻辑删除某文档下的全部分块（重新解析/重试前调用，保证幂等）"""
        await db.execute(
            update(RagChunk).where(RagChunk.doc_id == doc_id, RagChunk.del_flag == '0').values(del_flag='2')
        )
