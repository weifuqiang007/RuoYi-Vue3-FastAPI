import asyncio

import pytest

from module_rag.service.ranking import HeuristicReranker, MixedLanguageTokenizer, bm25_scores
from module_rag.service.retrieval_service import RetrievalService


def test_mixed_language_tokenizer_supports_chinese_terms_and_english_words():
    tokens = MixedLanguageTokenizer.tokenize('反身性 Reflexivity practice')

    assert '反身' in tokens
    assert '身性' in tokens
    assert 'reflexivity' in tokens


def test_bm25_prefers_document_matching_query_terms():
    scores = bm25_scores('权力关系 反身性', ['讨论权力关系与反身性', '天气和交通'])

    assert scores[0] > scores[1]


def test_rrf_returns_real_fusion_score_and_source_scores():
    vector = [{'chunk_id': 1, 'content': 'a', 'score': 0.9, 'metadata': {}}]
    keyword = [{'chunk_id': 1, 'content': 'a', 'score': 3.2, 'metadata': {}}]

    result = RetrievalService._rrf_merge(vector, keyword)[0]

    assert result['score'] == pytest.approx(2 / 61)
    assert result['fusion_score'] == pytest.approx(2 / 61)
    assert result['vector_score'] == 0.9
    assert result['keyword_score'] == 3.2


def test_heuristic_reranker_promotes_lexically_relevant_content():
    candidates = [
        {
            'chunk_id': 1,
            'content': '反身性要求研究者审视自身的权力位置',
            'metadata': {'heading_path': ['反身性研究']},
            'vector_score': 0.7,
            'keyword_score': 1.0,
            'fusion_score': 0.02,
        },
        {
            'chunk_id': 2,
            'content': '项目进度与行政管理办法',
            'metadata': {'heading_path': ['管理']},
            'vector_score': 0.72,
            'keyword_score': 0.0,
            'fusion_score': 0.019,
        },
    ]

    ranked = asyncio.run(HeuristicReranker().rerank('反身性 权力位置', candidates, top_k=2))

    assert ranked[0]['chunk_id'] == 1
    assert ranked[0]['rerank_score'] == ranked[0]['score']
