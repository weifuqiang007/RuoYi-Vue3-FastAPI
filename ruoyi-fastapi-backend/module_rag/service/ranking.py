"""RAG 排序组件：分词、BM25、融合和可替换的精排器。"""

import math
import os
import re
from collections import Counter
from typing import Protocol

import cohere

from utils.log_util import logger


class MixedLanguageTokenizer:
    """面向中英混合文本的轻量分词器，无外部词典依赖。"""

    _segment_re = re.compile(r'[\u3400-\u9fff]+|[a-zA-Z0-9][a-zA-Z0-9_.-]*')

    @classmethod
    def tokenize(cls, text: str) -> list[str]:
        """英文按词、中文按单字和二元组切分，兼顾术语召回与短查询。"""
        tokens: list[str] = []
        for segment in cls._segment_re.findall((text or '').casefold()):
            if cls._is_chinese_segment(segment):
                tokens.extend(segment)
                tokens.extend(segment[index:index + 2] for index in range(len(segment) - 1))
            else:
                tokens.append(segment)
        return tokens

    @staticmethod
    def _is_chinese_segment(segment: str) -> bool:
        return bool(segment) and all('\u3400' <= char <= '\u9fff' for char in segment)


def bm25_scores(query: str, documents: list[str], *, k1: float = 1.5, b: float = 0.75) -> list[float]:
    """对候选集计算 BM25 分数；适用于数据库粗召回后的轻量词法精排。"""
    if not documents:
        return []
    query_terms = list(dict.fromkeys(MixedLanguageTokenizer.tokenize(query)))
    tokenized_documents = [MixedLanguageTokenizer.tokenize(document) for document in documents]
    if not query_terms:
        return [0.0] * len(documents)

    average_length = sum(len(tokens) for tokens in tokenized_documents) / len(tokenized_documents) or 1.0
    document_frequency = {
        term: sum(1 for tokens in tokenized_documents if term in set(tokens))
        for term in query_terms
    }
    scores: list[float] = []
    total_documents = len(documents)

    for tokens in tokenized_documents:
        frequencies = Counter(tokens)
        document_length = len(tokens)
        score = 0.0
        for term in query_terms:
            frequency = frequencies[term]
            if not frequency:
                continue
            frequency_in_documents = document_frequency[term]
            inverse_document_frequency = math.log(
                1 + (total_documents - frequency_in_documents + 0.5) / (frequency_in_documents + 0.5)
            )
            denominator = frequency + k1 * (1 - b + b * document_length / average_length)
            score += inverse_document_frequency * frequency * (k1 + 1) / denominator
        scores.append(score)
    return scores


class Reranker(Protocol):
    """精排器扩展点；领域模块只依赖协议，不依赖具体厂商。"""

    async def rerank(self, query: str, candidates: list[dict], top_k: int) -> list[dict]:
        """返回按相关性降序排列的候选结果。"""


class HeuristicReranker:
    """默认本地精排器，融合向量、词法、RRF、标题命中和块类型。"""

    async def rerank(self, query: str, candidates: list[dict], top_k: int) -> list[dict]:
        if not candidates:
            return []

        query_terms = set(MixedLanguageTokenizer.tokenize(query))
        max_fusion = max((float(item.get('fusion_score') or 0.0) for item in candidates), default=0.0) or 1.0
        max_keyword = max((float(item.get('keyword_score') or 0.0) for item in candidates), default=0.0) or 1.0
        ranked: list[dict] = []

        for candidate in candidates:
            metadata = candidate.get('metadata') or {}
            content_terms = set(MixedLanguageTokenizer.tokenize(candidate.get('content') or ''))
            heading_text = ' '.join(metadata.get('heading_path') or [])
            heading_terms = set(MixedLanguageTokenizer.tokenize(heading_text))
            lexical_coverage = len(query_terms & content_terms) / max(len(query_terms), 1)
            heading_coverage = len(query_terms & heading_terms) / max(len(query_terms), 1)
            vector_score = max(0.0, min(1.0, float(candidate.get('vector_score') or 0.0)))
            keyword_score = float(candidate.get('keyword_score') or 0.0) / max_keyword
            fusion_score = float(candidate.get('fusion_score') or 0.0) / max_fusion

            score = (
                0.50 * vector_score
                + 0.25 * lexical_coverage
                + 0.10 * keyword_score
                + 0.10 * fusion_score
                + 0.05 * heading_coverage
            )
            if metadata.get('block_type') == 'reference':
                score *= 0.8

            result = dict(candidate)
            result['score'] = round(score, 6)
            result['rerank_score'] = result['score']
            ranked.append(result)

        ranked.sort(key=lambda item: item['score'], reverse=True)
        return ranked[:top_k]


class CohereReranker:
    """Cohere cross-encoder 精排适配器；未配置时不参与默认路径。"""

    def __init__(self, api_key: str, model: str = 'rerank-v3.5') -> None:
        self.api_key = api_key
        self.model = model

    async def rerank(self, query: str, candidates: list[dict], top_k: int) -> list[dict]:
        client = cohere.AsyncClientV2(api_key=self.api_key)
        response = await client.rerank(
            model=self.model,
            query=query,
            documents=[candidate.get('content') or '' for candidate in candidates],
            top_n=min(top_k, len(candidates)),
        )
        ranked: list[dict] = []
        for result in response.results:
            candidate = dict(candidates[result.index])
            candidate['score'] = float(result.relevance_score)
            candidate['rerank_score'] = candidate['score']
            ranked.append(candidate)
        return ranked


def build_reranker() -> Reranker:
    """按环境变量构建精排器，厂商不可用时自动降级到本地实现。"""
    provider = os.getenv('RAG_RERANKER_PROVIDER', 'heuristic').strip().lower()
    if provider == 'cohere':
        api_key = os.getenv('RAG_RERANKER_API_KEY') or os.getenv('COHERE_API_KEY', '')
        if api_key:
            return CohereReranker(
                api_key=api_key,
                model=os.getenv('RAG_RERANKER_MODEL', 'rerank-v3.5'),
            )
        logger.warning('RAG_RERANKER_PROVIDER=cohere 但未配置 API Key，已降级到本地精排器')
    return HeuristicReranker()
