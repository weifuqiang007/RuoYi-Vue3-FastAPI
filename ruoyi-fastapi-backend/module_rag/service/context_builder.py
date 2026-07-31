"""统一的 RAG 检索与引用上下文构建器。"""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from module_rag.service.embedding_service import EmbeddingService
from module_rag.service.retrieval_service import RetrievalService


@dataclass(slots=True)
class RagContext:
    """供生成模型使用的上下文及结构化引用。"""

    text: str
    citations: list[dict]
    results: list[dict]


class RagContextBuilder:
    """收敛各业务模块重复的向量化、检索、截断和引用格式逻辑。"""

    @classmethod
    async def build(
        cls,
        db: AsyncSession,
        query_text: str,
        kb_ids: list[int],
        *,
        top_k: int = 5,
        max_chars_per_chunk: int = 500,
        score_threshold: float | None = None,
    ) -> RagContext:
        """检索知识并构建带稳定编号的引用上下文。"""
        if not (query_text or '').strip() or not kb_ids:
            return RagContext(text='', citations=[], results=[])

        query_embedding = await EmbeddingService.embed_single(query_text)
        results = await RetrievalService.hybrid_search(
            db=db,
            query_text=query_text,
            query_embedding=query_embedding,
            kb_ids=kb_ids,
            top_k=top_k,
            score_threshold=score_threshold,
        )
        return cls.from_results(results, max_chars_per_chunk=max_chars_per_chunk)

    @staticmethod
    def from_results(results: list[dict], *, max_chars_per_chunk: int = 500) -> RagContext:
        """将检索结果转换为模型上下文和前端可消费的 citation 列表。"""
        sections: list[str] = []
        citations: list[dict] = []

        for index, result in enumerate(results, start=1):
            metadata = result.get('metadata') or {}
            heading_path = metadata.get('heading_path') or []
            source_parts = [metadata.get('doc_name') or f"文档{result.get('doc_id')}"]
            if metadata.get('page'):
                source_parts.append(f"第{metadata['page']}页")
            if heading_path:
                source_parts.append(' > '.join(heading_path))
            source = ' · '.join(source_parts)
            content = (result.get('content') or '')[:max_chars_per_chunk]
            sections.append(f'[{index}] 来源：{source}\n{content}')
            citations.append({
                'id': index,
                'chunk_id': result.get('chunk_id'),
                'doc_id': result.get('doc_id'),
                'kb_id': result.get('kb_id'),
                'doc_name': metadata.get('doc_name'),
                'page': metadata.get('page'),
                'heading_path': heading_path,
                'score': result.get('score'),
            })

        if not sections:
            return RagContext(text='', citations=[], results=results)
        instruction = '请仅将下列资料作为知识依据；引用其中的事实或观点时，在对应论断后标注 [编号]。'
        return RagContext(text=f"{instruction}\n\n" + '\n\n'.join(sections), citations=citations, results=results)
