"""可插拔的混合检索服务。

执行链：向量粗召回 + 中英词法粗召回 → RRF 融合 → rerank → 阈值过滤。
业务模块只依赖本服务，不感知具体检索或模型厂商。
"""

import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from module_rag.service.ranking import (
    HeuristicReranker,
    MixedLanguageTokenizer,
    Reranker,
    bm25_scores,
    build_reranker,
)
from utils.log_util import logger


class RetrievalService:
    """RAG 检索门面，允许测试或部署时替换精排器。"""

    MIN_DATABASE_TOKEN_LENGTH = 2
    _reranker: Reranker | None = None

    @classmethod
    def configure_reranker(cls, reranker: Reranker | None) -> None:
        """注入精排器；传 None 会在下次检索时按环境配置重新构建。"""
        cls._reranker = reranker

    @classmethod
    async def hybrid_search(
        cls,
        db: AsyncSession,
        query_text: str,
        query_embedding: list[float],
        kb_ids: list[int],
        top_k: int = 5,
        score_threshold: float | None = None,
    ) -> list[dict]:
        """执行混合检索，并返回可解释的各阶段分数及溯源元数据。"""
        query_text = (query_text or '').strip()
        kb_ids = list(dict.fromkeys(kb_ids or []))
        if not query_text or not query_embedding or not kb_ids or top_k <= 0:
            return []

        candidate_k = max(
            top_k,
            int(os.getenv('RAG_RETRIEVAL_CANDIDATE_K', '20')),
        )
        probes = max(1, int(os.getenv('RAG_IVFFLAT_PROBES', '10')))
        await db.execute(text(f'SET LOCAL ivfflat.probes = {probes}'))

        vector_results = await cls._vector_search(db, query_embedding, kb_ids, top_k=candidate_k)
        keyword_results = await cls._keyword_search(db, query_text, kb_ids, top_k=candidate_k)
        candidates = cls._rrf_merge(vector_results, keyword_results)

        reranker = cls._reranker or build_reranker()
        cls._reranker = reranker
        try:
            ranked = await reranker.rerank(query_text, candidates, candidate_k)
        except Exception:
            logger.exception('RAG 外部精排器调用失败，已降级到本地精排器')
            ranked = await HeuristicReranker().rerank(query_text, candidates, candidate_k)

        effective_threshold = (
            score_threshold
            if score_threshold is not None
            else float(os.getenv('RAG_SCORE_THRESHOLD', '0.15'))
        )
        return [
            result for result in ranked
            if float(result.get('score') or 0.0) >= effective_threshold
        ][:top_k]

    @classmethod
    async def _vector_search(
        cls,
        db: AsyncSession,
        query_embedding: list[float],
        kb_ids: list[int],
        top_k: int = 20,
    ) -> list[dict]:
        """使用 PgVector 做向量粗召回，并补齐文档级溯源字段。"""
        sql = text("""
            SELECT
                c.chunk_id, c.doc_id, c.kb_id, c.content,
                c.metadata, d.doc_name,
                1 - (c.embedding <=> CAST(:query_vec AS vector)) AS score
            FROM rag_chunk AS c
            JOIN rag_document AS d ON d.doc_id = c.doc_id AND d.del_flag = '0'
            WHERE c.kb_id = ANY(:kb_ids)
              AND c.del_flag = '0'
              AND c.embedding IS NOT NULL
            ORDER BY c.embedding <=> CAST(:query_vec AS vector)
            LIMIT :top_k
        """)
        result = await db.execute(sql, {
            'query_vec': str(query_embedding),
            'kb_ids': kb_ids,
            'top_k': top_k,
        })
        return [cls._normalize_result(dict(row._mapping)) for row in result.fetchall()]

    @classmethod
    async def _keyword_search(
        cls,
        db: AsyncSession,
        query_text: str,
        kb_ids: list[int],
        top_k: int = 20,
    ) -> list[dict]:
        """用 ILIKE 粗召回候选，再用中英混合 BM25 排序，替代失效的 simple 分词。"""
        tokens = cls._keyword_query_tokens(query_text)
        if not tokens:
            return []

        parameters: dict = {'kb_ids': kb_ids, 'candidate_limit': max(top_k * 10, 100)}
        conditions: list[str] = []
        for index, token in enumerate(tokens):
            parameter_name = f'keyword_{index}'
            parameters[parameter_name] = f'%{token}%'
            conditions.append(f'c.content ILIKE :{parameter_name}')

        sql = text(f"""
            SELECT
                c.chunk_id, c.doc_id, c.kb_id, c.content,
                c.metadata, d.doc_name
            FROM rag_chunk AS c
            JOIN rag_document AS d ON d.doc_id = c.doc_id AND d.del_flag = '0'
            WHERE c.kb_id = ANY(:kb_ids)
              AND c.del_flag = '0'
              AND ({' OR '.join(conditions)})
            LIMIT :candidate_limit
        """)
        result = await db.execute(sql, parameters)
        candidates = [cls._normalize_result(dict(row._mapping)) for row in result.fetchall()]
        scores = bm25_scores(query_text, [candidate['content'] for candidate in candidates])
        for candidate, score in zip(candidates, scores, strict=True):
            candidate['score'] = score
        candidates.sort(key=lambda item: item['score'], reverse=True)
        return candidates[:top_k]

    @classmethod
    def _keyword_query_tokens(cls, query_text: str, limit: int = 12) -> list[str]:
        """选择适合数据库粗召回的词，优先中文二元组和完整英文词。"""
        all_tokens = MixedLanguageTokenizer.tokenize(query_text)
        preferred = [
            token for token in all_tokens
            if len(token) >= cls.MIN_DATABASE_TOKEN_LENGTH
        ]
        selected = preferred or all_tokens
        return list(dict.fromkeys(selected))[:limit]

    @classmethod
    def _rrf_merge(
        cls,
        vector_results: list[dict],
        keyword_results: list[dict],
        k: int = 60,
    ) -> list[dict]:
        """RRF 融合两路排名，并保留可解释的原始分与真实融合分。"""
        merged: dict[int, dict] = {}

        for rank, item in enumerate(vector_results):
            chunk_id = item['chunk_id']
            candidate = merged.setdefault(chunk_id, dict(item))
            candidate['vector_score'] = float(item.get('score') or 0.0)
            candidate.setdefault('keyword_score', 0.0)
            candidate['fusion_score'] = float(candidate.get('fusion_score') or 0.0) + 1.0 / (k + rank + 1)

        for rank, item in enumerate(keyword_results):
            chunk_id = item['chunk_id']
            candidate = merged.setdefault(chunk_id, dict(item))
            candidate.setdefault('vector_score', 0.0)
            candidate['keyword_score'] = float(item.get('score') or 0.0)
            candidate['fusion_score'] = float(candidate.get('fusion_score') or 0.0) + 1.0 / (k + rank + 1)

        ranked = sorted(merged.values(), key=lambda item: item['fusion_score'], reverse=True)
        for candidate in ranked:
            candidate['score'] = candidate['fusion_score']
        return ranked

    @staticmethod
    def _normalize_result(item: dict) -> dict:
        """把 SQL 结果统一成稳定结构，并将文档名并入 metadata。"""
        metadata = dict(item.get('metadata') or {})
        if item.get('doc_name'):
            metadata.setdefault('doc_name', item['doc_name'])
        item['metadata'] = metadata
        item.pop('doc_name', None)
        return item
