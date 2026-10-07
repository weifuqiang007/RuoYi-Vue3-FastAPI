"""可替换的 Embedding 服务。"""

import asyncio
import os
from typing import Protocol

from openai import AsyncOpenAI


class EmbeddingProvider(Protocol):
    """向量模型提供方协议。"""

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """将等长文本列表转换为等长向量列表。"""


class OpenAICompatibleEmbeddingProvider:
    """适配智谱、硅基流动、OpenAI 等 OpenAI-compatible embeddings API。"""

    MAX_RETRIES = 3

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        dimensions: int | None = None,
        batch_size: int = 25,
    ) -> None:
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.dimensions = dimensions
        self.batch_size = batch_size

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        all_embeddings: list[list[float]] = []
        for index in range(0, len(texts), self.batch_size):
            batch = texts[index:index + self.batch_size]
            for retry in range(self.MAX_RETRIES):
                try:
                    # dimensions 仅在提供方支持时传入（如智谱 embedding-3）；
                    # 硅基流动 bge-m3 等固定维度模型不接受该参数。
                    kwargs: dict = {'model': self.model, 'input': batch}
                    if self.dimensions:
                        kwargs['dimensions'] = self.dimensions
                    response = await self.client.embeddings.create(**kwargs)
                    ordered = sorted(response.data, key=lambda item: item.index)
                    all_embeddings.extend(item.embedding for item in ordered)
                    break
                except Exception:
                    if retry == self.MAX_RETRIES - 1:
                        raise
                    await asyncio.sleep(retry + 1)
            if index + self.batch_size < len(texts):
                await asyncio.sleep(0.1)
        return all_embeddings


class EmbeddingService:
    """Embedding 门面；框架调用稳定，具体厂商通过环境或依赖注入替换。"""

    _provider: EmbeddingProvider | None = None

    @classmethod
    def configure_provider(cls, provider: EmbeddingProvider | None) -> None:
        """注入向量提供方；传 None 恢复按环境变量延迟构建。"""
        cls._provider = provider

    @classmethod
    def _get_provider(cls) -> EmbeddingProvider:
        if cls._provider is None:
            dims_raw = os.getenv('RAG_EMBEDDING_DIMENSIONS', '').strip()
            cls._provider = OpenAICompatibleEmbeddingProvider(
                api_key=os.getenv('RAG_EMBEDDING_API_KEY') or os.getenv('ZHIPU_API_KEY', ''),
                base_url=os.getenv(
                    'RAG_EMBEDDING_BASE_URL',
                    'https://open.bigmodel.cn/api/paas/v4',
                ),
                model=os.getenv('RAG_EMBEDDING_MODEL', 'embedding-3'),
                dimensions=int(dims_raw) if dims_raw else None,
                batch_size=int(os.getenv('RAG_EMBEDDING_BATCH_SIZE', '25')),
            )
        return cls._provider

    @classmethod
    async def embed_texts(cls, texts: list[str]) -> list[list[float]]:
        """批量向量化，并校验输入输出数量，避免向量错位写入分块。"""
        if not texts:
            return []
        if any(not (text or '').strip() for text in texts):
            raise ValueError('向量化文本不能为空')
        embeddings = await cls._get_provider().embed_texts(texts)
        if len(embeddings) != len(texts):
            raise RuntimeError(f'Embedding 返回数量异常：期望 {len(texts)}，实际 {len(embeddings)}')
        return embeddings

    @classmethod
    async def embed_single(cls, text: str) -> list[float]:
        """单条文本向量化。"""
        return (await cls.embed_texts([text]))[0]
