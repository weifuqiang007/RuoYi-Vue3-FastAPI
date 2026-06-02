# module_rag/dao/chunk_dao.py
from sqlalchemy import select, update, text
from sqlalchemy.ext.asyncio import AsyncSession
from module_rag.entity.do.chunk_do import RagChunk


class ChunkDao:

    @classmethod
    async def bulk_insert(cls, db: AsyncSession, doc_id: int, kb_id: int, chunks: list[dict]) -> list[int]:
        """批量插入分块记录，返回 chunk_id 列表,这里面有没有批量插入的方法？逐条插入是不是有点太浪费资源了？"""
        chunk_ids = []
        for i , chunk in enumerate(chunks):
            rag_chunk = RagChunk(
                doc_id=doc_id,
                kb_id=kb_id,
                chunk_index=i,
                content=chunk['content'],
                token_count=chunk.get('token_count', len(chunk['content'])),
                chunk_metadata=chunk.get('metadata')
            )
            db.add(rag_chunk)
            await db.flush()
            chunk_ids.append(rag_chunk.chunk_id)
        return chunk_ids


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
