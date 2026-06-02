# module_rag/service/retrieval_service.py
"""混合检索服务
参考 ragflow/rag/nlp/search.py 的 Dealer 类
核心：向量检索 + 关键词检索 + RRF 融合
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class RetrievalService:

    @classmethod
    async def hybrid_search(
        cls,
        db: AsyncSession,
        query_text: str,
        query_embedding: list[float],
        kb_ids: list[int],
        top_k: int = 5,
    ) -> list[dict]:
        """
        混合检索：向量 + 关键词，用 RRF 融合
        参考 ragflow/rag/nlp/search.py 的 search() 实现
        """
        # 设置向量检索探针数
        await db.execute(text("SET ivfflat.probes = 10"))

        # 路径1：向量检索
        vector_results = await cls._vector_search(db, query_embedding, kb_ids, top_k=20)

        # 路径2：关键词检索（PostgreSQL 全文检索替代 RAGFlow 里的 ES BM25）
        keyword_results = await cls._keyword_search(db, query_text, kb_ids, top_k=20)

        # RRF 融合（来自 ragflow 的核心思路）
        merged = cls._rrf_merge(vector_results, keyword_results)

        return merged[:top_k]

    @classmethod
    async def _vector_search(cls, db, query_embedding, kb_ids, top_k=20):
        """PgVector 向量检索"""
        sql = text("""
            SELECT
                chunk_id, doc_id, kb_id, content,
                metadata,
                1 - (embedding <=> :query_vec::vector) AS score
            FROM rag_chunk
            WHERE kb_id = ANY(:kb_ids)
              AND del_flag = '0'
              AND embedding IS NOT NULL
            ORDER BY embedding <=> :query_vec::vector
            LIMIT :top_k
        """)
        result = await db.execute(sql, {
            "query_vec": str(query_embedding),
            "kb_ids": kb_ids,
            "top_k": top_k,
        })
        return [dict(row._mapping) for row in result.fetchall()]

    @classmethod
    async def _keyword_search(cls, db, query_text, kb_ids, top_k=20):
        """PostgreSQL 全文检索"""
        sql = text("""
            SELECT
                chunk_id, doc_id, kb_id, content,
                metadata,
                ts_rank(to_tsvector('simple', content), plainto_tsquery('simple', :query)) AS score
            FROM rag_chunk
            WHERE kb_id = ANY(:kb_ids)
              AND del_flag = '0'
              AND to_tsvector('simple', content) @@ plainto_tsquery('simple', :query)
            ORDER BY score DESC
            LIMIT :top_k
        """)
        result = await db.execute(sql, {
            "query": query_text,
            "kb_ids": kb_ids,
            "top_k": top_k,
        })
        return [dict(row._mapping) for row in result.fetchall()]

    @classmethod
    def _rrf_merge(cls, vector_results: list[dict], keyword_results: list[dict], k: int = 60) -> list[dict]:
        """
        RRF (Reciprocal Rank Fusion) 融合
        公式来自 ragflow/rag/nlp/search.py
        score = 1/(k + rank_vector) + 1/(k + rank_keyword)
        """
        scores = {}

        for rank, item in enumerate(vector_results):
            cid = item["chunk_id"]
            scores[cid] = scores.get(cid, {"item": item, "score": 0.0})
            scores[cid]["score"] += 1.0 / (k + rank + 1)

        for rank, item in enumerate(keyword_results):
            cid = item["chunk_id"]
            if cid not in scores:
                scores[cid] = {"item": item, "score": 0.0}
            scores[cid]["score"] += 1.0 / (k + rank + 1)

        sorted_items = sorted(scores.values(), key=lambda x: x["score"], reverse=True)
        return [x["item"] for x in sorted_items]