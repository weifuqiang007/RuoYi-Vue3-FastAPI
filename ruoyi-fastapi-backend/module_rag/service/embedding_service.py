# module_rag/service/embedding_service.py
"""Embedding 服务
参考 ragflow/rag/llm/embedding_model.py 的 ZhipuEmbed 类
核心：批量处理 + 限速 + 重试
"""
import asyncio
import os
from openai import AsyncOpenAI

class EmbeddingService:
    """
    Embedding 服务
    批量处理逻辑参考 ragflow/rag/llm/embedding_model.py 的 batch 处理方式
    使用智谱 API（兼容 OpenAI SDK）
    """
    BATCH_SIZE = 25  #智普API 每批次最多25条

    #todo 未来换成硅集流动的模型。需要改动的地方有输入、输出的格式。如果有可能，需要改成一个公共的方法类
    @classmethod
    def _get_client(cls) -> AsyncOpenAI:
        return AsyncOpenAI(
            api_key=os.getenv('ZHIPU_API_KEY',''),
            base_url='https://open.bigmodel.cn/api/paas/v4'
        )

    @classmethod
    async def embed_texts(cls, texts: list[str]) -> list[list[float]]:
        """
        批量向量化
        参考 ragflow embedding_model.py 的批量 + 限速逻辑
        """
        client = cls._get_client()
        all_embeddings = []

        for i in range(0, len(texts), cls.BATCH_SIZE):
            batch = texts[i: i+ cls.BATCH_SIZE]

            for retry in range(3):
                try:
                    response = await client.embeddings.create(
                        model='embedding-3',
                        input=batch,
                        dimensions=1024,  # 指定输出 1024 维（pgvector 索引最大支持 2000 维，2048 超限）
                    )
                    batch_embeddings = [item.embedding for  item in response.data]
                    all_embeddings.extend(batch_embeddings)
                    break
                except Exception as e:
                    if retry ==2 :
                        raise
                    await asyncio.sleep(1 * (retry + 1))
            if i + cls.BATCH_SIZE < len(texts):
                await asyncio.sleep(0.1)

        return all_embeddings

    @classmethod
    async def embed_single(cls, text: str) -> list[float]:
        """单条文本向量化"""
        results = await cls.embed_texts([text])
        return results[0]
