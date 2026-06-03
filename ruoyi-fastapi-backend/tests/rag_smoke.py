import asyncio
from dotenv import load_dotenv
import os

# 手动加载 .env.test（直接运行脚本时框架不会自动加载）
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.test')
load_dotenv(env_path)

async def rag_pipeline_smoke():
    from module_rag.service.parser.txt_parser import TxtParser
    from module_rag.service.chunker.fixed_chunker import FixedChunker
    from module_rag.service.embedding_service import EmbeddingService

    # 1. 解析
    blocks = TxtParser().parse(r"G:\zhangyichi\ruoyi-fastapi-backend\tests\test_sample.txt")  # 准备一个 500+ 字的 txt
    assert len(blocks) > 0, "解析结果为空"

    # 2. 分块
    chunks = FixedChunker(500, 50).chunk(blocks[0]["text"])
    assert len(chunks) > 0, "分块结果为空"

    # 3. 向量化
    embeddings = await EmbeddingService.embed_texts([chunks[0]["content"]])
    assert len(embeddings[0]) == 1024, f"向量维度错误: {len(embeddings[0])}"

    print("✅ RAG 管道冒烟测试通过")

if __name__ == "__main__":
    asyncio.run(rag_pipeline_smoke())