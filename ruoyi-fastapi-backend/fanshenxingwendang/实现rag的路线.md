## 提問1：想自己實現的同時參考ragflow
我想用ragflow，但是我同时也想学习整个rag的框架。因为做rag的业务，不懂整个rag的流程就是调用别人的api也很可悲。至于服务器，我可以申请2台。或者大一点的一台也可以。慢一点也可以。暂时先不用考虑并发的问题，有5到10个人能用就不错了。

我想用好一点的框架，但是我又不想只调用这个api，你说怎么办


## 回答1：以ragflow為終點，自己去實現核心業務代碼
# 结合RAGFlow学习并自建RAG框架实施方案
## 一、整体思路
核心方案：**自建RAG全链路代码 + RAGFlow作为参照标准+能力兜底**
既吃透RAG完整技术流程，又借助成熟框架弥补自研短板，适配5-10人小规模使用场景，无需优先考虑高并发。

整体逻辑：自主实现RAG各核心模块，遇到问题、效果对标、处理复杂文档时，调用本地部署的RAGFlow。

## 二、RAG分层实现规划
完整RAG链路分为5大层，分别明确自研实现方式、依赖底层库、对应RAGFlow能力：

| 层级 | 自研实现内容 | 依赖底层库 | RAGFlow对应模块 |
| ---- | ------------ | ---------- | --------------- |
| ① 文档解析 | 自研文档解析器 | PyMuPDF、python-docx、markdown | deepdoc文档解析引擎 |
| ② 文本分块 | 自研文本分块逻辑 | Langchain TextSplitter | 内置分块策略模块 |
| ③ 向量化 | 对接Embedding接口生成向量 | 智谱Embedding-3 SDK | Embedding向量模块 |
| ④ 向量存储 | 基于PgVector实现向量入库 | PostgreSQL+PgVector扩展 | Elasticsearch向量存储 |
| ⑤ 检索&重排 | 自研相似度检索、LLM重排逻辑 | 余弦相似度计算、LLM重排能力 | 检索排序模块 |

> 说明：每一层均手写代码，理清**输入、输出、设计原理**，彻底吃透RAG全流程。

## 三、RAGFlow定位与使用场景
RAGFlow不作为纯调用API的黑盒，主要承担三大角色：
1. **学习参照**：部署后上传同一份文档，对比分块、向量、检索结果，明确优质RAG效果标准
2. **效果对比**：将自研链路结果与RAGFlow输出对标，定位自研逻辑缺陷
3. **能力兜底**：扫描件PDF、复杂表格等自研难以解析的文档，调用RAGFlow接口处理
4. **生产备选**：自研链路效果不佳时，可平滑切换至RAGFlow保障业务正常

## 四、核心代码示例（自研模块）
### 1. 向量服务 embedding_service.py
```python
# module_rag/service/embedding_service.py
class EmbeddingService:
    @classmethod
    async def embed_texts(cls, texts: list[str]) -> list[list[float]]:
        """自主调用Embedding接口，理解向量生成逻辑"""
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key="你的密钥", base_url="https://open.bigmodel.cn/...")
        response = await client.embeddings.create(model="embedding-3", input=texts)
        return [item.embedding for item in response.data]
```

### 2. 文本分块服务 chunk_service.py
```python
# module_rag/service/chunk_service.py
class ChunkService:
    @classmethod
    def split_text(cls, text: str, chunk_size=500, overlap=50) -> list[str]:
        """自主实现分块，理解块大小、重叠区间的作用"""
        chunks = []
        step = chunk_size - overlap
        for i in range(0, len(text), step):
            chunks.append(text[i:i + chunk_size])
        return chunks
```

### 3. 向量检索服务 retrieval_service.py
```python
# module_rag/service/retrieval_service.py
from sqlalchemy import text

class RetrievalService:
    @classmethod
    async def search(cls, db, query_embedding, kb_ids, top_k=5):
        """原生SQL实现向量检索，理解余弦相似度计算逻辑"""
        sql = text("""
            SELECT content, 1 - (embedding <=> :vec::vector) AS similarity
            FROM rag_chunk WHERE kb_id = ANY(:kb_ids)
            ORDER BY embedding <=> :vec::vector LIMIT :top_k
        """)
        # 执行SQL并返回结果
        result = await db.execute(sql, vec=query_embedding, kb_ids=kb_ids, top_k=top_k)
        return result.fetchall()
```

### 4. RAGFlow兜底服务 ragflow_fallback_service.py
```python
# module_rag/service/ragflow_fallback_service.py
class RAGFlowFallbackService:
    """仅复杂文档（扫描件/表格）场景调用RAGFlow"""
    @classmethod
    async def parse_complex_pdf(cls, file_path: str) -> str:
        from ragflow_sdk import RAGFlow
        # 连接本地部署的RAGFlow
        client = RAGFlow(api_key="你的密钥", base_url="http://localhost:9380")
        # 调用文档解析能力
        # 业务逻辑省略
        return ""
```

## 五、分步学习&落地路线（5步执行）
1. **第一步：部署RAGFlow**
   上传测试PDF，观察官方链路的**分块结果、向量数据、检索结果**，建立优质RAG效果认知。

2. **第二步：自研文档解析**
   优先实现TXT、普通PDF解析，将解析文本与RAGFlow输出做对比，优化解析逻辑。

3. **第三步：自研分块+向量化**
   实现文本分块与Embedding调用，对比双方分块效果，吃透`chunk_size`、`overlap`核心参数意义。

4. **第四步：自研向量检索**
   基于PgVector完成检索逻辑，对比双方TopK检索结果，明确相似度分数判定标准。

5. **第五步：自研RAG对话链路**
   检索结果拼接Prompt、调用LLM生成回答，对比回答质量，理解检索效果对最终答案的影响。

## 六、服务器部署方案
**单台服务器即可满足需求**（支持5-10人使用，无需考虑并发）
```
┌─────────────────────────────────────────────┐
│               统一业务服务器                  │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │  原有后端（RuoYiFast）                │    │
│  │  + 自研RAG模块 module_rag             │    │
│  │  + PostgreSQL(PgVector向量扩展)       │    │
│  │  + Redis缓存                         │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │  Docker部署 RAGFlow（端口：9380）     │    │
│  │  用途：学习参照 + 复杂文档兜底        │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

## 七、方案总结
| 目标 | 对应实现方案 |
| ---- | ------------ |
| 吃透RAG全流程 | 逐层手写代码，掌握每个环节原理与逻辑 |
| 借助成熟框架 | 本地部署RAGFlow，用作效果参照与能力兜底 |
| 保障业务可用 | 主体使用自研RAG链路，短板场景切换RAGFlow |
| 预估周期 | 整体开发落地约14天 |

## 八、启动前置任务
1. 部署RAGFlow服务
2. 搭建自研`module_rag`项目基础骨架