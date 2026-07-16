# RAG 模块实践方案：从 RAGFlow 抄核心代码

> **目标**：在 RuoYiFast 框架上，从 RAGFlow 源码中精准摘取 RAG 核心实现，搭建 `module_rag` 模块，支撑四区联动教学系统。  
> **策略**：不运行 RAGFlow，只读它的源码，把核心逻辑移植过来。  
> **向量数据库**：MVP 阶段用 PgVector（零额外部署），知识库量大后再迁 Milvus。

---

## 一、先搞清楚：RAGFlow 哪些代码值得抄

RAGFlow 的项目结构庞杂，90% 是你不需要的（多租户、计费、Web UI、MinIO 集成……）。你真正需要的只有以下 **5个核心模块**。

### RAGFlow 项目结构定位图

```
ragflow/
├── api/                          ← 不要（RAGFlow 自己的 Web 接口）
├── web/                          ← 不要（RAGFlow 前端）
├── docker/                       ← 不要
│
├── rag/                          ← ✅ 核心！重点学习区
│   ├── nlp/                      ← ✅ 文本处理工具（分词、清洗）
│   ├── svr/                      ← ✅ 文档解析服务
│   └── utils/                    ← ✅ 工具函数
│
├── deepdoc/                      ← ✅ 核心！文档解析引擎
│   ├── parser/                   ← ✅ 各格式解析器（PDF/DOCX/PPTX）
│   └── vision/                   ← 可选（OCR/图片理解，暂时不需要）
│
├── graphrag/                     ← ✅ 可选（图谱增强检索，后期再看）
│
└── agent/                        ← 不要（RAGFlow 自己的 Agent 框架）
```

### 你需要从 RAGFlow 抄的 5 个模块

| # | RAGFlow 源码位置 | 你要抄的内容 | 移植到你项目的位置 |
|---|---|---|---|
| 1 | `deepdoc/parser/` | PDF/DOCX/TXT 解析器 | `module_rag/service/parser/` |
| 2 | `rag/nlp/` | 文本分块（Chunking）策略 | `module_rag/service/chunker/` |
| 3 | `rag/nlp/search.py` | BM25 关键词检索逻辑 | `module_rag/service/retrieval_service.py` |
| 4 | `rag/svr/task_executor.py` | 文档处理 Pipeline 的任务调度思路 | `module_rag/service/pipeline_service.py` |
| 5 | `rag/utils/` | 文本清洗、Token 计数工具 | `module_rag/utils/` |

---

## 二、整体架构：你要建设的 module_rag

```
module_rag/
├── __init__.py
│
├── controller/                          # API 层（照着 module_ai 写）
│   ├── knowledge_base_controller.py     # 知识库 CRUD
│   ├── document_controller.py           # 文档上传 + 进度查询
│   ├── chunk_controller.py              # 分块查看/编辑
│   └── retrieval_controller.py          # 检索测试 + RAG 对话
│
├── dao/                                 # 数据库访问层
│   ├── knowledge_base_dao.py
│   ├── document_dao.py
│   └── chunk_dao.py
│
├── entity/
│   ├── do/                              # SQLAlchemy ORM 模型
│   │   ├── knowledge_base_do.py
│   │   ├── document_do.py
│   │   └── chunk_do.py
│   └── vo/                              # Pydantic 请求/响应模型
│       ├── knowledge_base_vo.py
│       ├── document_vo.py
│       └── retrieval_vo.py
│
├── service/                             # 核心业务逻辑（重点）
│   ├── parser/                          # ← 从 ragflow/deepdoc/parser/ 抄
│   │   ├── __init__.py
│   │   ├── pdf_parser.py                # ← 抄 deepdoc/parser/pdf_parser.py
│   │   ├── docx_parser.py               # ← 抄 deepdoc/parser/docx_parser.py
│   │   └── txt_parser.py                # 自己写，很简单
│   │
│   ├── chunker/                         # ← 从 ragflow/rag/nlp/ 抄
│   │   ├── __init__.py
│   │   ├── fixed_chunker.py             # ← 抄 rag/nlp/tokenizer.py 的分块逻辑
│   │   └── semantic_chunker.py          # ← 抄 rag/app/naive.py 的语义分块逻辑
│   │
│   ├── knowledge_base_service.py        # 知识库 CRUD
│   ├── document_service.py              # 上传 → 解析 → 分块 → 向量化的编排
│   ├── embedding_service.py             # Embedding API 封装
│   └── retrieval_service.py             # 向量检索 + BM25 混合检索 + Rerank
│
└── utils/                               # ← 从 ragflow/rag/utils/ 抄
    ├── text_cleaner.py                  # 文本清洗
    └── token_counter.py                 # Token 计数
```

---

## 三、分模块详解：从 RAGFlow 抄什么 + 改什么

### 模块 1：文档解析（Parser）

**要解决的问题**：把 PDF/DOCX/TXT 变成可以分块的干净文本。

#### 1.1 去 RAGFlow 找这个文件

```
ragflow/deepdoc/parser/pdf_parser.py         ← 核心，必看必抄
ragflow/deepdoc/parser/docx_parser.py        ← 次要，抄核心逻辑
ragflow/deepdoc/parser/__init__.py           ← 看它怎么注册解析器
```

#### 1.2 RAGFlow PDF 解析器的核心逻辑（你要学的）

RAGFlow 的 PDF 解析不是简单地用 `pdfplumber.extract_text()`，而是做了**版面分析（Layout Analysis）**：它会识别标题、正文段落、表格、图片说明，分别处理。

**你需要从它那里抄的关键方法**：

```python
# ragflow/deepdoc/parser/pdf_parser.py 里找这几个方法：

class RAGFlowPdfParser:
    def __call__(self, filename, binary=None, from_page=0, to_page=10000, ...):
        # 这是入口，看它怎么调用底层的 pdfplumber/pymupdf
        ...

    def _layouts_rec(self, thr=0.7):
        # 版面识别的核心，判断哪些是标题哪些是正文
        # 这部分复杂，你可以简化：只保留文字提取，跳过图片识别
        ...

    def remove_tag(self, s):
        # 清洗 HTML 标签，这个直接抄
        ...
```

#### 1.3 你自己项目的简化实现思路

RAGFlow 的 PDF 解析用了视觉模型（OCR），太重了。你的方案应该是：

**第一步**：去 `ragflow/deepdoc/parser/pdf_parser.py` 读懂它的**分页提取 + 段落合并逻辑**（跳过视觉模型部分）。

**第二步**：用 PyMuPDF 实现简化版，参考 RAGFlow 的段落合并逻辑：

```python
# 你的 module_rag/service/parser/pdf_parser.py
import fitz  # PyMuPDF

class PdfParser:
    """
    参考 ragflow/deepdoc/parser/pdf_parser.py 的段落识别逻辑
    简化版：去掉视觉模型，保留文本结构识别
    """

    def parse(self, file_path: str) -> list[dict]:
        """
        返回结构：[{"text": "段落内容", "page": 1, "type": "text/title"}, ...]
        type 的判断逻辑：参考 ragflow 的 _layouts_rec 方法
        """
        doc = fitz.open(file_path)
        blocks = []

        for page_num, page in enumerate(doc):
            # RAGFlow 的核心思路：按字体大小判断标题
            # 在 ragflow/deepdoc/parser/pdf_parser.py 的 _extract_texts 方法里找
            text_dict = page.get_text("dict")
            for block in text_dict["blocks"]:
                if block["type"] == 0:  # 文字块
                    block_text = self._extract_block_text(block)
                    block_type = self._classify_block(block)  # 参考 ragflow 的分类逻辑
                    if block_text.strip():
                        blocks.append({
                            "text": block_text,
                            "page": page_num + 1,
                            "type": block_type,
                        })

        return self._merge_paragraphs(blocks)  # 合并碎片段落：这个逻辑抄 ragflow

    def _classify_block(self, block: dict) -> str:
        """
        参考 ragflow/deepdoc/parser/pdf_parser.py 的标题识别：
        字体大小 > 阈值 → title；否则 → text
        在 ragflow 里搜索 "font_size" 找到判断逻辑
        """
        max_font_size = max(
            span["size"]
            for line in block["lines"]
            for span in line["spans"]
            if span["text"].strip()
        )
        return "title" if max_font_size > 14 else "text"

    def _merge_paragraphs(self, blocks: list[dict]) -> list[dict]:
        """
        关键：把被切碎的段落合并回来
        这是 RAGFlow 的重要贡献，在 ragflow/rag/nlp/text_chunk.py 里找合并逻辑
        核心判断：如果上一个 block 没有以句号/问号/感叹号结尾，
        且下一个 block 不是标题，就合并
        """
        merged = []
        for block in blocks:
            if (merged
                    and merged[-1]["type"] == "text"
                    and block["type"] == "text"
                    and not merged[-1]["text"].rstrip().endswith(("。", "！", "？", ".", "!", "?"))):
                merged[-1]["text"] += block["text"]
            else:
                merged.append(dict(block))
        return merged
```

**关键学习点**：去 RAGFlow 源码搜索 `merge` 和 `paragraph`，理解它如何把 PDF 里被跨页切断的段落重新拼回来。这是 RAG 解析质量的关键。

---

### 模块 2：文本分块（Chunker）

**要解决的问题**：把长文章切成 500-800 字的块，让向量检索有意义。

#### 2.1 去 RAGFlow 找这个文件

```
ragflow/rag/app/naive.py                     ← ✅ 最重要！这里有完整的分块策略
ragflow/rag/nlp/tokenizer.py                 ← Token 计数（中文用字符数就行）
ragflow/rag/nlp/text_splitter.py             ← 文本切分工具函数
```

#### 2.2 RAGFlow 的分块策略（你要学的核心思想）

RAGFlow 在 `ragflow/rag/app/naive.py` 里实现了它的默认分块策略，叫 **Naive**，即"固定窗口 + 语义边界对齐"。

**关键逻辑**（去源码里搜这几个关键词）：

```python
# 在 ragflow/rag/app/naive.py 里找到 chunk() 函数
# 它的核心逻辑分 3 步：

# 步骤 1: 先按标题切出大章节（Section）
# 搜索: "if tk_num > self.chunk_token_num"
# 大于 chunk_token_num 的 Section 才需要进一步切分

# 步骤 2: 在大章节内，按句子边界切分
# 搜索: "SENTENCE_ENDS" 或 "。！？"
# RAGFlow 的贡献：不是机械地按字符数切，而是找最近的句子结束位置

# 步骤 3: 重叠（Overlap）处理
# 搜索: "overlap"
# 每个 chunk 头部保留上一个 chunk 尾部的 N 个字符，避免上下文断裂
```

#### 2.3 你自己项目的实现

```python
# 你的 module_rag/service/chunker/fixed_chunker.py
# 参考 ragflow/rag/app/naive.py 的 chunk() 函数核心逻辑

class FixedChunker:
    """
    固定大小分块 + 句子边界对齐
    核心思路来自 ragflow/rag/app/naive.py
    """

    SENTENCE_ENDS = ("。", "！", "？", "；", ".", "!", "?", ";", "\n\n")

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str, metadata: dict = None) -> list[dict]:
        """
        分块逻辑：
        1. 先按段落（\n\n）分段 → 来自 ragflow 的 Section 思路
        2. 段落 < chunk_size：直接作为一个 chunk
        3. 段落 > chunk_size：在句子边界处切分 → ragflow 的核心贡献
        4. 相邻 chunk 之间保留 overlap 字符 → 避免语义断裂
        """
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) <= self.chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(self._make_chunk(current_chunk.strip(), metadata))
                    # overlap：把当前 chunk 尾部加到下一个 chunk 开头
                    overlap_text = current_chunk[-self.overlap:] if len(current_chunk) > self.overlap else current_chunk

                if len(para) > self.chunk_size:
                    # 大段落：在句子边界切
                    sub_chunks = self._split_at_sentence(para, metadata, overlap_text)
                    chunks.extend(sub_chunks)
                    current_chunk = sub_chunks[-1]["content"][-self.overlap:] if sub_chunks else ""
                else:
                    current_chunk = overlap_text + para + "\n\n"

        if current_chunk.strip():
            chunks.append(self._make_chunk(current_chunk.strip(), metadata))

        return chunks

    def _split_at_sentence(self, text: str, metadata: dict, prefix: str = "") -> list[dict]:
        """
        在句子边界处切分长文本
        RAGFlow 在 ragflow/rag/app/naive.py 搜索 SENTENCE_ENDS 找到类似逻辑
        """
        chunks = []
        start = 0
        current = prefix

        for i, char in enumerate(text):
            current += char
            if char in ("。", "！", "？", "；", "\n") and len(current) >= self.chunk_size:
                chunks.append(self._make_chunk(current.strip(), metadata))
                current = current[-self.overlap:]  # 保留 overlap
                start = i + 1

        if current.strip():
            chunks.append(self._make_chunk(current.strip(), metadata))

        return chunks

    def _make_chunk(self, content: str, metadata: dict) -> dict:
        return {
            "content": content,
            "token_count": len(content),  # 中文按字符数估算
            "metadata": metadata or {},
        }
```

**重要**：去 RAGFlow 里读 `ragflow/rag/app/naive.py` 的完整 `chunk()` 实现，它比这里简化版多了：
- 按标题层级保留上下文（标题会被带入 chunk 的开头）
- Token 计数用 tiktoken，你可以改用字符数
- 识别列表、表格，单独处理

这两点值得学习，在你的 `semantic_chunker.py` 里实现进阶版。

---

### 模块 3：Embedding 服务

**要解决的问题**：把文本块变成向量，存到 PgVector。

#### 3.1 RAGFlow 的 Embedding 代码位置

```
ragflow/rag/llm/embedding_model.py           ← ✅ 最重要！看它怎么封装多种 Embedding
ragflow/api/db/services/llm_service.py       ← 看它如何管理模型配置（可选）
```

#### 3.2 RAGFlow Embedding 的核心设计（你要学的）

RAGFlow 在 `embedding_model.py` 里设计了**统一 Embedding 接口**，支持多种提供商（OpenAI/智谱/本地模型）。

```python
# 在 ragflow/rag/llm/embedding_model.py 里找这个基类：
class Base:
    def encode(self, texts: list[str]) -> tuple[np.array, int]:
        # 返回 (向量数组, 使用的token数)
        ...

# 以及智谱的实现：
class ZhipuEmbed(Base):
    def encode(self, texts, batch_size=32):
        # 注意：批量处理，每次最多 batch_size 条
        # 这个批量逻辑你必须抄！避免超出 API 限制
        ...
```

**你要抄的关键点**：批量处理 + 错误重试。RAGFlow 在批量向量化时有完善的 batch + retry 逻辑，这是生产可用的关键。

#### 3.3 你的实现

```python
# module_rag/service/embedding_service.py
# 参考 ragflow/rag/llm/embedding_model.py 的 ZhipuEmbed 实现

import asyncio
from openai import AsyncOpenAI

class EmbeddingService:
    """
    Embedding 服务
    批量处理逻辑参考 ragflow/rag/llm/embedding_model.py 的 batch 处理方式
    """
    BATCH_SIZE = 25  # 智谱 API 每批最多 25 条（ragflow 源码里有这个限制）

    @classmethod
    async def embed_texts(cls, texts: list[str]) -> list[list[float]]:
        """
        批量向量化，参考 ragflow 的批处理逻辑
        在 ragflow/rag/llm/embedding_model.py 搜索 "batch_size" 找到原始实现
        """
        client = cls._get_client()
        all_embeddings = []

        # 分批处理 —— 这是 ragflow 的核心设计
        for i in range(0, len(texts), cls.BATCH_SIZE):
            batch = texts[i: i + cls.BATCH_SIZE]
            response = await client.embeddings.create(
                model="embedding-3",
                input=batch,
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

            # 防止 API 限速：ragflow 源码里有 sleep，你也加上
            if i + cls.BATCH_SIZE < len(texts):
                await asyncio.sleep(0.1)

        return all_embeddings
```

---

### 模块 4：向量检索 + 混合检索（Retrieval）

**这是 RAG 质量的核心，也是从 RAGFlow 学习收益最大的部分。**

#### 4.1 去 RAGFlow 找这个文件

```
ragflow/rag/nlp/search.py                    ← ✅ 最重要！BM25 + 向量混合检索
ragflow/rag/svr/task_executor.py             ← 看 Pipeline 调度思路
ragflow/api/db/services/knowledgebase_service.py ← 看 Retrieval 的调用方式
```

#### 4.2 RAGFlow 的混合检索策略（你要学的核心）

RAGFlow 使用 **RRF (Reciprocal Rank Fusion)** 融合向量检索和 BM25 关键词检索的结果。这是它比简单向量检索更准确的关键。

```python
# 在 ragflow/rag/nlp/search.py 里找到这个核心函数：

def search(self, req, idxnm, emb_mdl, highlight=False):
    """
    RAGFlow 的混合检索入口
    req 里包含：
      - query_vector: 查询向量（来自 embedding）
      - keyword: 关键词（来自查询分析）
      - top_k: 返回数量
    
    核心逻辑：
    1. 向量检索：用 cosine similarity 召回 Top-20
    2. 关键词检索：用 BM25 召回 Top-20（ES 的全文检索）
    3. RRF 融合：两路结果合并，用倒数排名公式计算最终分数
    """
    ...

# 搜索 "rrf" 找到融合公式：
def rrf_score(rank1, rank2, k=60):
    # RRF 公式：1/(k+rank1) + 1/(k+rank2)
    return 1 / (k + rank1) + 1 / (k + rank2)
```

**注意**：RAGFlow 的 BM25 依赖 Elasticsearch，你的项目没有 ES。你需要**降级处理**：用 PostgreSQL 的全文检索（`tsvector`/`tsquery`）替代 BM25，或者用 `rank_bm25` Python 库在内存里做 BM25。

#### 4.3 你的混合检索实现（移植 RRF 思想）

```python
# module_rag/service/retrieval_service.py
# 混合检索 = 向量检索（PgVector）+ 关键词检索（PostgreSQL全文）+ RRF 融合
# 核心思想来自 ragflow/rag/nlp/search.py

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
        # 路径1：向量检索
        vector_results = await cls._vector_search(db, query_embedding, kb_ids, top_k=20)

        # 路径2：关键词检索（PostgreSQL 全文检索替代 ES BM25）
        keyword_results = await cls._keyword_search(db, query_text, kb_ids, top_k=20)

        # RRF 融合（来自 ragflow 的核心思路）
        merged = cls._rrf_merge(vector_results, keyword_results)

        return merged[:top_k]

    @classmethod
    async def _vector_search(cls, db, query_embedding, kb_ids, top_k=20):
        """
        PgVector 向量检索
        SQL 参考 ragflow 的向量检索实现（ragflow 用 ES，这里改为 pgvector）
        """
        sql = text("""
            SELECT
                chunk_id,
                doc_id,
                kb_id,
                content,
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
        rows = result.fetchall()
        return [dict(r._mapping) for r in rows]

    @classmethod
    async def _keyword_search(cls, db, query_text, kb_ids, top_k=20):
        """
        PostgreSQL 全文检索（替代 RAGFlow 里的 ES BM25）
        原理相同：词频匹配，和向量检索互补
        """
        sql = text("""
            SELECT
                chunk_id,
                doc_id,
                kb_id,
                content,
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
        rows = result.fetchall()
        return [dict(r._mapping) for r in rows]

    @classmethod
    def _rrf_merge(cls, vector_results: list[dict], keyword_results: list[dict], k: int = 60) -> list[dict]:
        """
        RRF (Reciprocal Rank Fusion) 融合两路检索结果
        公式来自 ragflow/rag/nlp/search.py
        score = 1/(k + rank_in_vector) + 1/(k + rank_in_keyword)
        """
        scores = {}

        for rank, item in enumerate(vector_results):
            cid = item["chunk_id"]
            scores[cid] = scores.get(cid, {"item": item, "score": 0})
            scores[cid]["score"] += 1 / (k + rank + 1)

        for rank, item in enumerate(keyword_results):
            cid = item["chunk_id"]
            if cid not in scores:
                scores[cid] = {"item": item, "score": 0}
            scores[cid]["score"] += 1 / (k + rank + 1)

        sorted_items = sorted(scores.values(), key=lambda x: x["score"], reverse=True)
        return [x["item"] for x in sorted_items]
```

---

### 模块 5：文档处理 Pipeline（Pipeline Service）

**要解决的问题**：文件上传后，自动走完「解析→分块→向量化→入库」全流程。

#### 5.1 去 RAGFlow 找这个文件

```
ragflow/rag/svr/task_executor.py             ← ✅ 最重要！Pipeline 的执行者
ragflow/api/db/services/task_service.py      ← 任务管理
```

#### 5.2 RAGFlow Pipeline 的核心思想

RAGFlow 的文档处理是异步的：

```
前端上传 → 创建 Task 记录（状态: pending）→ 后台 Worker 拿任务 → 执行 → 更新状态
```

它用 Redis 队列 + 多进程 Worker 实现。你的 MVP 阶段可以简化为**同步执行**（文档量小），但要保留**状态机**的设计。

在 `ragflow/rag/svr/task_executor.py` 里，你要学习的是：

```python
# 搜索 "do_handle_task" 找到核心执行函数
# 它的处理步骤：
# 1. 从 DB 取 Task
# 2. 调用对应格式的 Parser（工厂模式，根据文件类型分发）
# 3. 调用 Chunker
# 4. 批量 Embedding
# 5. 写入向量库
# 6. 更新 Task 状态

# 注意：RAGFlow 有完善的错误恢复逻辑
# 搜索 "retry" 和 "FAILED" 找到失败处理
```

#### 5.3 你的 Pipeline Service

```python
# module_rag/service/document_service.py
# Pipeline 编排逻辑，参考 ragflow/rag/svr/task_executor.py 的 do_handle_task

import asyncio
from pathlib import Path
from .parser.pdf_parser import PdfParser
from .parser.docx_parser import DocxParser
from .chunker.fixed_chunker import FixedChunker
from .embedding_service import EmbeddingService

class DocumentService:

    PARSERS = {
        "pdf": PdfParser,
        "docx": DocxParser,
        "txt": TxtParser,
        "md": TxtParser,
    }

    @classmethod
    async def process_document(cls, db: AsyncSession, doc_id: int):
        """
        文档处理主流程
        状态机设计参考 ragflow/rag/svr/task_executor.py

        状态流转：
        0(待处理) → 1(解析中) → 2(分块中) → 3(向量化中) → 4(完成) / 9(失败)
        """
        doc = await DocumentDao.get_by_id(db, doc_id)

        try:
            # Step 1: 解析文档
            await DocumentDao.update_status(db, doc_id, parse_status="1")  # 解析中
            parser_cls = cls.PARSERS.get(doc.file_type)
            if not parser_cls:
                raise ValueError(f"不支持的文件类型: {doc.file_type}")

            parser = parser_cls()
            blocks = parser.parse(doc.file_path)

            # Step 2: 文本分块
            kb = await KnowledgeBaseDao.get_by_id(db, doc.kb_id)
            chunker = FixedChunker(
                chunk_size=kb.chunk_size,
                overlap=kb.chunk_overlap,
            )

            all_chunks = []
            for block in blocks:
                chunks = chunker.chunk(
                    text=block["text"],
                    metadata={"page": block.get("page"), "type": block.get("type")}
                )
                all_chunks.extend(chunks)

            # Step 3: 保存分块记录（先不含向量）
            await DocumentDao.update_status(db, doc_id, parse_status="2", embed_status="1")
            chunk_ids = await ChunkDao.bulk_insert(db, doc_id, doc.kb_id, all_chunks)

            # Step 4: 批量向量化（参考 ragflow 的 batch embedding 逻辑）
            texts = [c["content"] for c in all_chunks]
            embeddings = await EmbeddingService.embed_texts(texts)

            # Step 5: 更新向量字段
            await ChunkDao.bulk_update_embeddings(db, chunk_ids, embeddings)
            await DocumentDao.update_status(
                db, doc_id,
                parse_status="2",
                embed_status="2",
                chunk_count=len(all_chunks)
            )

        except Exception as e:
            await DocumentDao.update_status(
                db, doc_id,
                embed_status="3",  # 失败
                error_msg=str(e)[:500]
            )
            raise
```

---

## 四、数据库建表（直接执行）

```sql
-- 第一步：启用 pgvector 扩展（必须先做）
CREATE EXTENSION IF NOT EXISTS vector;

-- 知识库表
CREATE TABLE rag_knowledge_base (
    kb_id          BIGSERIAL PRIMARY KEY,
    kb_name        VARCHAR(100) NOT NULL,
    kb_desc        VARCHAR(500),
    embedding_model VARCHAR(100) DEFAULT 'embedding-3',
    chunk_size      INTEGER DEFAULT 500,
    chunk_overlap   INTEGER DEFAULT 50,
    doc_count       INTEGER DEFAULT 0,
    status         CHAR(1) DEFAULT '0',
    dept_id        BIGINT,
    user_id        BIGINT,
    del_flag       CHAR(1) DEFAULT '0',
    create_by      VARCHAR(64) DEFAULT '',
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_by      VARCHAR(64) DEFAULT '',
    update_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    remark         VARCHAR(500)
);
COMMENT ON TABLE rag_knowledge_base IS 'RAG知识库表';

-- 文档表
CREATE TABLE rag_document (
    doc_id         BIGSERIAL PRIMARY KEY,
    kb_id          BIGINT NOT NULL REFERENCES rag_knowledge_base(kb_id),
    doc_name       VARCHAR(255) NOT NULL,
    file_path      VARCHAR(500) NOT NULL,
    file_type      VARCHAR(20),
    file_size      BIGINT DEFAULT 0,
    chunk_count    INTEGER DEFAULT 0,
    parse_status   CHAR(1) DEFAULT '0',
    embed_status   CHAR(1) DEFAULT '0',
    error_msg      VARCHAR(500),
    user_id        BIGINT,
    dept_id        BIGINT,
    del_flag       CHAR(1) DEFAULT '0',
    create_by      VARCHAR(64) DEFAULT '',
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_by      VARCHAR(64) DEFAULT '',
    update_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE rag_document IS 'RAG文档表';

-- 分块表（含向量字段）
CREATE TABLE rag_chunk (
    chunk_id       BIGSERIAL PRIMARY KEY,
    doc_id         BIGINT NOT NULL REFERENCES rag_document(doc_id),
    kb_id          BIGINT NOT NULL REFERENCES rag_knowledge_base(kb_id),
    chunk_index    INTEGER NOT NULL,
    content        TEXT NOT NULL,
    token_count    INTEGER DEFAULT 0,
    embedding      vector(1024),      -- pgvector 向量字段（智谱 embedding-3 是 1024 维）
    metadata       JSONB,
    del_flag       CHAR(1) DEFAULT '0',
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE rag_chunk IS 'RAG文档分块表';

-- 向量检索必须的 IVFFlat 索引（参考 ragflow 的 Milvus 索引策略）
-- 说明：ivfflat 是近似索引，lists 参数 = 预期数据量/1000（约）
CREATE INDEX idx_rag_chunk_embedding ON rag_chunk USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
-- 普通索引
CREATE INDEX idx_rag_chunk_kb_id ON rag_chunk(kb_id);
CREATE INDEX idx_rag_chunk_doc_id ON rag_chunk(doc_id);
-- 全文检索索引（支持混合检索里的关键词路由）
CREATE INDEX idx_rag_chunk_content_fts ON rag_chunk USING gin(to_tsvector('simple', content));
```

---

## 五、依赖安装

在 `requirements-pg.txt` 里追加：

```txt
# RAG 核心依赖
pgvector>=0.2.4              # Python pgvector 驱动
PyMuPDF>=1.23.0              # PDF 解析（ragflow 的 deepdoc 也用它）
python-docx>=1.1.0           # DOCX 解析
python-pptx>=0.6.21          # PPTX 解析（可选）
langchain-text-splitters>=0.2.0  # 文本分块（langchain 子包，比整个 langchain 轻）

# 可选：BM25 关键词检索（如果不想用 PostgreSQL 全文检索）
rank-bm25>=0.2.2
```



---

## 六、分步操作计划

### Phase 0：环境准备（1天）

**Step 0.1** 安装依赖

```bash
# 在 RuoYiFast 项目根目录
pip install pgvector PyMuPDF python-docx langchain-text-splitters -r requirements-pg.txt
```

**Step 0.2** 启用 PgVector

```bash
# 连接到你的 PostgreSQL
psql -U your_user -d your_db -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 验证
psql -U your_user -d your_db -c "SELECT * FROM pg_extension WHERE extname='vector';"
```

**Step 0.3** 执行建表 SQL

把第四节的 SQL 保存为 `sql/rag_tables.sql`，然后执行：

```bash
psql -U your_user -d your_db -f sql/rag_tables.sql
```

**Step 0.4** 配置 API Key

在 `.env.test`（或你项目的配置文件）里添加：

```env
ZHIPU_API_KEY=your_zhipu_api_key_here
ZHIPU_EMBED_MODEL=embedding-3
ZHIPU_EMBED_DIM=1024
```

---

### Phase 1：读 RAGFlow 源码（1天，学习阶段）

**这是这份方案的核心环节，不能跳过。**

按以下顺序打开 RAGFlow 源码阅读，每个文件重点看标注的函数：

**Day 1 上午：文档解析**

```
打开文件：ragflow/deepdoc/parser/pdf_parser.py
重点函数：
  - __call__() —— 了解入口参数结构
  - _extract_texts() 或等价函数 —— 理解页面文字提取逻辑
  - merge() 或 _merge_paragraphs() —— 段落合并是重点！
记笔记：它用了哪些 pdfplumber/fitz 的 API？

打开文件：ragflow/deepdoc/parser/docx_parser.py
重点函数：
  - __call__() —— 理解 docx 结构（段落/表格）的遍历方式
```

**Day 1 下午：分块 + Pipeline**

```
打开文件：ragflow/rag/app/naive.py
重点函数：
  - chunk() —— 整个文件最重要的函数
  - 搜索 "SENTENCE_ENDS" —— 句子边界识别
  - 搜索 "overlap" —— 重叠逻辑

打开文件：ragflow/rag/svr/task_executor.py
重点函数：
  - do_handle_task() 或 handle_task() —— Pipeline 的状态机流转
  - 搜索 "FAILED" —— 错误处理逻辑
```

**Day 2 上午：检索**

```
打开文件：ragflow/rag/nlp/search.py
重点函数：
  - search() —— 混合检索主入口
  - 搜索 "rrf" —— 找到 RRF 融合公式（可能叫 reciprocal_rank_fusion）
  - 搜索 "knn" 或 "vector" —— 向量检索部分
  - 搜索 "highlight" —— 关键词高亮（可选）
```

---

### Phase 2：搭建 module_rag 骨架（半天）

```bash
# 在 RuoYiFast 项目根目录执行
mkdir -p module_rag/{controller,dao,entity/{do,vo},service/{parser,chunker},utils}

# 创建 __init__.py
find module_rag -type d -exec touch {}/__init__.py \;
```

---

### Phase 3：实现 Parser 层（2天）

**任务**：参照 RAGFlow 的 `deepdoc/parser/` 实现你的解析器。

操作顺序：

1. 把你在 Phase 1 阅读的笔记整理出来
2. 在 `module_rag/service/parser/pdf_parser.py` 里写你的实现
3. 关键点：把 RAGFlow 里的 `_merge_paragraphs` 逻辑完整移植（这里质量差异最大）
4. 写单元测试：找一份 PDF，打印分块结果，肉眼检查是否合理

验收标准：

```python
# 在 Python 交互环境里测试
from module_rag.service.parser.pdf_parser import PdfParser

parser = PdfParser()
blocks = parser.parse("test.pdf")
for b in blocks[:5]:
    print(b["type"], b["text"][:50])

# 预期输出：
# title  第一章 社会工作概述
# text   社会工作是以利他主义为指导，以科学的知识为基础...
# text   在实践中，社会工作者需要...
```

---

### Phase 4：实现 Chunker 层（1天）

参照 RAGFlow 的 `rag/app/naive.py` 实现：

验收标准：

```python
from module_rag.service.chunker.fixed_chunker import FixedChunker

chunker = FixedChunker(chunk_size=500, overlap=50)
chunks = chunker.chunk("这是一段很长的测试文本...（你的实际文本）")

for i, c in enumerate(chunks):
    print(f"Chunk {i}: {len(c['content'])} 字")
    print(f"  开头: {c['content'][:30]}")
    print(f"  结尾: {c['content'][-30:]}")
    print()
```

---

### Phase 5：实现 Embedding Service（半天）

参照 RAGFlow 的 `rag/llm/embedding_model.py` 实现批量处理：

验收标准：

```python
import asyncio
from module_rag.service.embedding_service import EmbeddingService

texts = ["社会工作的基本原则", "服务对象的自决权", "伦理决策框架"]
embeddings = asyncio.run(EmbeddingService.embed_texts(texts))

print(f"向量数量: {len(embeddings)}")
print(f"向量维度: {len(embeddings[0])}")
# 预期: 向量数量: 3, 向量维度: 1024
```

---

### Phase 6：实现 Pipeline Service（2天）

把 Parser → Chunker → Embedding → 存库 串联起来。

验收标准：上传一个 PDF 文件，在 `rag_chunk` 表里查到向量化完成的分块记录：

```sql
SELECT chunk_id, chunk_index, token_count, LEFT(content, 50)
FROM rag_chunk
WHERE doc_id = 1
ORDER BY chunk_index;
```

---

### Phase 7：实现 Retrieval Service（2天）

参照 RAGFlow 的 `rag/nlp/search.py` 实现混合检索：

验收标准：

```python
import asyncio

query = "社会工作者如何处理服务对象的阻抗行为"
results = asyncio.run(retrieval_service.hybrid_search(
    db=db,
    query_text=query,
    query_embedding=embedding,
    kb_ids=[1],
    top_k=5,
))

for r in results:
    print(f"相似度: {r.get('score', 0):.3f}")
    print(f"内容: {r['content'][:100]}")
    print()
```

---

### Phase 8：集成到四区联动（持续进行）

RAG 模块完成后，四区联动各模块的 AI 调用统一通过 `RetrievalService` 获取知识库支撑：

```python
# 在 module_learning/service/ai_engine.py 里的调用方式
from module_rag.service.retrieval_service import RetrievalService
from module_rag.service.embedding_service import EmbeddingService

class ScenarioAiEngine:
    @classmethod
    async def analyze_scenario(cls, db, scenario_text: str, kb_ids: list[int]):
        # 1. 向量化查询
        query_embedding = await EmbeddingService.embed_single(scenario_text)

        # 2. 混合检索（这一行替代了所有 RAGFlow 的复杂性）
        retrieved_chunks = await RetrievalService.hybrid_search(
            db=db,
            query_text=scenario_text,
            query_embedding=query_embedding,
            kb_ids=kb_ids,
            top_k=5,
        )

        # 3. 拼接知识到 Prompt
        knowledge_context = "\n\n".join([
            f"【知识片段{i+1}】\n{chunk['content']}"
            for i, chunk in enumerate(retrieved_chunks)
        ])

        # 4. 调用 LLM（复用若依框架的 AI 模块）
        system_prompt = SCENARIO_PROMPT.format(retrieved_knowledge=knowledge_context)
        # ... 后续调用 AiChatService
```

---

## 七、你要从 RAGFlow 里抄的代码清单（汇总）

| 文件（RAGFlow 源码） | 你要抄/学的具体内容 | 移植到你项目的文件 | 难度 |
|---|---|---|---|
| `deepdoc/parser/pdf_parser.py` | `_merge_paragraphs()` 段落合并逻辑 | `module_rag/service/parser/pdf_parser.py` | ★★★ |
| `deepdoc/parser/pdf_parser.py` | `_classify_block()` 标题/正文分类 | `module_rag/service/parser/pdf_parser.py` | ★★ |
| `deepdoc/parser/docx_parser.py` | 段落/表格遍历逻辑 | `module_rag/service/parser/docx_parser.py` | ★★ |
| `rag/app/naive.py` 的 `chunk()` | 句子边界切分 + overlap 逻辑 | `module_rag/service/chunker/fixed_chunker.py` | ★★★ |
| `rag/app/naive.py` 的 `chunk()` | 标题带入 chunk 开头的上下文保留 | `module_rag/service/chunker/fixed_chunker.py` | ★★★ |
| `rag/llm/embedding_model.py` 的 `ZhipuEmbed` | 批量 + 限速 + 重试逻辑 | `module_rag/service/embedding_service.py` | ★★ |
| `rag/nlp/search.py` 的 `search()` | RRF 融合公式（倒数排名融合） | `module_rag/service/retrieval_service.py` | ★★★ |
| `rag/svr/task_executor.py` 的 `do_handle_task()` | 状态机流转 + 错误恢复逻辑 | `module_rag/service/document_service.py` | ★★ |

---

## 八、常见坑和避免方法

### 坑 1：pgvector 索引必须在数据入库后才能有效

```sql
-- ❌ 错误：建表时 lists=100，但数据不足 100 条时查询报错
-- ✅ 正确：先插数据，再建索引；或者设置更小的 lists
CREATE INDEX ... USING ivfflat ... WITH (lists = 10);  -- 小数据量用 lists=10
```

### 坑 2：向量化前必须确认维度匹配

```python
# 智谱 embedding-3 是 1024 维
# 建表时 vector(1024) 必须和模型维度一致
# 如果换了模型维度变了，要重建整张 rag_chunk 表（代价极大）
# 所以一开始就把维度确认清楚！
```

### 坑 3：RAGFlow 的 PDF 解析依赖 pdfplumber 和 fitz（PyMuPDF），两者并存

RAGFlow 在不同情况下用不同库，你只需要用 `fitz`（PyMuPDF）就够了，不要两个都装。

### 坑 4：PgVector 的 IVFFlat 索引需要先执行 `SET ivfflat.probes`

```python
# 在查询前设置探针数，影响召回率 vs 速度的平衡
# RAGFlow 里的向量库（Milvus）有类似参数
await db.execute(text("SET ivfflat.probes = 10"))
```

### 坑 5：批量 Embedding 要注意文本长度限制

智谱 embedding-3 单次最大输入 2000 个 token。如果分块 500 字符，通常没问题。但如果 chunk 超长，要在 `embedding_service.py` 里截断。

---

## 九、完成 RAG 模块后的下一步

RAG 模块完成后，四区联动的开发顺序：

```
module_rag（本文档）
    ↓
module_learning/scenario/      （情境区：文本输入 + AI 识别关键事件）
    ↓
module_learning/decision/      （决策区：结构化决策记录 + 伦理分析）
    ↓
module_learning/reflection/    （反思区：三层递进提问 + 深度评估）
    ↓
module_learning/research/      （研究生成区：研究问题 + 论文框架）
```

每个区的 AI 调用，都是：

1. 调用 `RetrievalService.hybrid_search()` 拿相关知识
2. 把知识片段注入 Prompt
3. 调用 `AiChatService._build_agent()` 生成回答

---

*文档版本 v1.0 | 生成日期 2026-06-01*

---

## 十、精确分步实现路径（Step-by-Step 操作指南）

> **前提说明**：以下路径基于你的项目 `g:\zhangyichi\ruoyi-fastapi-backend` 的实际结构。
> 你已经有 RAGFlow 源码在 `utils/ragflowmodels/ragflow/`。
> 项目使用 PostgreSQL（已在 `.env.test` 中配置 `DB_TYPE = 'postgresql'`）。
> 模块注册采用 `common/router.py` 的自动注册机制，只要在 `module_rag/controller/` 下创建 `APIRouterPro` 即可被自动扫描。

---

### Step 1：安装 Python 依赖包

**操作位置**：项目根目录 `g:\zhangyichi\ruoyi-fastapi-backend`

**命令**：

```bash
pip install pgvector PyMuPDF python-docx chardet
```

**说明**：

| 包名 | 用途 | 对应 RAGFlow 源码位置 |
|---|---|---|
| `pgvector` | Python 端 pgvector 驱动，用于在 SQLAlchemy 中操作向量字段 | 无（RAGFlow 用 Milvus，你用 PgVector 替代） |
| `PyMuPDF` (fitz) | PDF 文档解析，提取文字和字体信息 | `ragflow/deepdoc/parser/pdf_parser.py` 中使用了 `pdfplumber`，你用更轻量的 PyMuPDF |
| `python-docx` | DOCX 文档解析，提取段落和表格 | `ragflow/deepdoc/parser/docx_parser.py` 的 `from docx import Document` |
| `chardet` | 文件编码检测，处理上传文档的编码问题 | `ragflow/rag/nlp/__init__.py` 中 `find_codec()` 函数 |

**验证**：

```bash
python -c "import pgvector; import fitz; import docx; import chardet; print('所有依赖安装成功')"
```

**注意**：你的 `requirements-pg.txt` 里已经有 `asyncpg`、`psycopg2-binary`、`SQLAlchemy[asyncio]`，这些不需要重装。但没有 `pgvector` 包，必须安装。

---

### Step 2：在 PostgreSQL 中启用 pgvector 扩展并建表

**操作位置**：SQL 客户端（Navicat / DBeaver / psql）

**Step 2.1**：连接到你的 PostgreSQL 数据库（`115.220.6.150:15432`，库名 `ruoyi-fastapi`）

**Step 2.2**：执行以下 SQL（启用 pgvector 扩展）：

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

**Step 2.3**：验证扩展已安装：

```sql
SELECT * FROM pg_extension WHERE extname = 'vector';
```

**Step 2.4**：创建 RAG 三张核心表：

```sql
-- ==========================================
-- RAG 知识库表
-- ==========================================
CREATE TABLE rag_knowledge_base (
    kb_id          BIGSERIAL PRIMARY KEY,
    kb_name        VARCHAR(100) NOT NULL,
    kb_desc        VARCHAR(500),
    embedding_model VARCHAR(100) DEFAULT 'embedding-3',
    chunk_size      INTEGER DEFAULT 500,
    chunk_overlap   INTEGER DEFAULT 50,
    doc_count       INTEGER DEFAULT 0,
    status         CHAR(1) DEFAULT '0',
    dept_id        BIGINT,
    user_id        BIGINT,
    del_flag       CHAR(1) DEFAULT '0',
    create_by      VARCHAR(64) DEFAULT '',
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_by      VARCHAR(64) DEFAULT '',
    update_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    remark         VARCHAR(500)
);
COMMENT ON TABLE rag_knowledge_base IS 'RAG知识库表';

-- ==========================================
-- RAG 文档表
-- ==========================================
CREATE TABLE rag_document (
    doc_id         BIGSERIAL PRIMARY KEY,
    kb_id          BIGINT NOT NULL REFERENCES rag_knowledge_base(kb_id),
    doc_name       VARCHAR(255) NOT NULL,
    file_path      VARCHAR(500) NOT NULL,
    file_type      VARCHAR(20),
    file_size      BIGINT DEFAULT 0,
    chunk_count    INTEGER DEFAULT 0,
    parse_status   CHAR(1) DEFAULT '0',   -- 0=待处理 1=解析中 2=解析完成 9=失败
    embed_status   CHAR(1) DEFAULT '0',   -- 0=待处理 1=向量化中 2=完成 9=失败
    error_msg      VARCHAR(500),
    user_id        BIGINT,
    dept_id        BIGINT,
    del_flag       CHAR(1) DEFAULT '0',
    create_by      VARCHAR(64) DEFAULT '',
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_by      VARCHAR(64) DEFAULT '',
    update_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE rag_document IS 'RAG文档表';

-- ==========================================
-- RAG 分块表（含向量字段）
-- ==========================================
CREATE TABLE rag_chunk (
    chunk_id       BIGSERIAL PRIMARY KEY,
    doc_id         BIGINT NOT NULL REFERENCES rag_document(doc_id),
    kb_id          BIGINT NOT NULL REFERENCES rag_knowledge_base(kb_id),
    chunk_index    INTEGER NOT NULL,
    content        TEXT NOT NULL,
    token_count    INTEGER DEFAULT 0,
    embedding      vector(1024),      -- 智谱 embedding-3 是 1024 维
    metadata       JSONB,
    del_flag       CHAR(1) DEFAULT '0',
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE rag_chunk IS 'RAG文档分块表';

-- ==========================================
-- 索引（数据量小的时候先建，数据量上来后再调整 lists 参数）
-- ==========================================
-- 向量检索索引
CREATE INDEX idx_rag_chunk_embedding ON rag_chunk USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10);
-- 普通索引
CREATE INDEX idx_rag_chunk_kb_id ON rag_chunk(kb_id);
CREATE INDEX idx_rag_chunk_doc_id ON rag_chunk(doc_id);
-- 全文检索索引（混合检索的关键词路由需要）
CREATE INDEX idx_rag_chunk_content_fts ON rag_chunk USING gin(to_tsvector('simple', content));
```

**注意**：`ivfflat` 索引的 `lists=10` 适合数据量 < 10000 条的情况。数据量上来后需要重建索引增大 lists。

---

### Step 3：创建 module_rag 目录骨架

**操作位置**：项目根目录 `g:\zhangyichi\ruoyi-fastapi-backend`

**命令**：

```bash
# 在项目根目录下执行
mkdir -p module_rag/controller
mkdir -p module_rag/dao
mkdir -p module_rag/entity/do
mkdir -p module_rag/entity/vo
mkdir -p module_rag/service/parser
mkdir -p module_rag/service/chunker
mkdir -p module_rag/utils
```

**创建所有 `__init__.py` 文件**：

```bash
touch module_rag/__init__.py
touch module_rag/controller/__init__.py
touch module_rag/dao/__init__.py
touch module_rag/entity/__init__.py
touch module_rag/entity/do/__init__.py
touch module_rag/entity/vo/__init__.py
touch module_rag/service/__init__.py
touch module_rag/service/parser/__init__.py
touch module_rag/service/chunker/__init__.py
touch module_rag/utils/__init__.py
```

**验证**：执行后目录结构应该是：

```
module_rag/
├── __init__.py
├── controller/
│   └── __init__.py
├── dao/
│   └── __init__.py
├── entity/
│   ├── __init__.py
│   ├── do/
│   │   └── __init__.py
│   └── vo/
│       └── __init__.py
├── service/
│   ├── __init__.py
│   ├── parser/
│   │   └── __init__.py
│   └── chunker/
│       └── __init__.py
└── utils/
    └── __init__.py
```

---

### Step 4：编写 Entity 层（数据库 ORM 模型 + Pydantic 模型）

**操作位置**：`module_rag/entity/` 目录

---

#### Step 4.1：编写 ORM 模型 — `module_rag/entity/do/knowledge_base_do.py`

**参考**：`module_ai/entity/do/ai_model_do.py`（你现有的 ORM 写法）

**RAGFlow 对应**：RAGFlow 用的是 Peewee ORM（`api/db/db_models.py`），你不需要看它的 ORM。你的项目用 SQLAlchemy，照着你 `ai_model_do.py` 的写法来。

**要写的内容**：

```python
# module_rag/entity/do/knowledge_base_do.py
from datetime import datetime
from sqlalchemy import CHAR, BigInteger, Column, DateTime, Integer, String, Text
from config.database import Base
from config.env import DataBaseConfig
from utils.common_util import SqlalchemyUtil


class RagKnowledgeBase(Base):
    """RAG知识库表"""
    __tablename__ = 'rag_knowledge_base'
    __table_args__ = {'comment': 'RAG知识库表'}

    kb_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='知识库主键')
    kb_name = Column(String(100), nullable=False, comment='知识库名称')
    kb_desc = Column(String(500), nullable=True, comment='知识库描述')
    embedding_model = Column(String(100), nullable=True, server_default='embedding-3', comment='Embedding模型')
    chunk_size = Column(Integer, nullable=True, server_default='500', comment='分块大小')
    chunk_overlap = Column(Integer, nullable=True, server_default='50', comment='分块重叠')
    doc_count = Column(Integer, nullable=True, server_default='0', comment='文档数量')
    status = Column(CHAR(1), nullable=True, server_default='0', comment='状态')
    dept_id = Column(BigInteger, nullable=True, comment='部门ID')
    user_id = Column(BigInteger, nullable=True, comment='用户ID')
    del_flag = Column(CHAR(1), nullable=True, server_default='0', comment='删除标志')
    create_by = Column(String(64), nullable=True, server_default="''", comment='创建者')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    update_by = Column(String(64), nullable=True, server_default="''", comment='更新者')
    update_time = Column(DateTime, nullable=True, default=datetime.now, comment='更新时间')
    remark = Column(String(500), nullable=True, comment='备注')
```

---

#### Step 4.2：编写 ORM 模型 — `module_rag/entity/do/document_do.py`

**要写的内容**：

```python
# module_rag/entity/do/document_do.py
from datetime import datetime
from sqlalchemy import CHAR, BigInteger, Column, DateTime, Integer, String
from config.database import Base


class RagDocument(Base):
    """RAG文档表"""
    __tablename__ = 'rag_document'
    __table_args__ = {'comment': 'RAG文档表'}

    doc_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='文档主键')
    kb_id = Column(BigInteger, nullable=False, comment='知识库ID')
    doc_name = Column(String(255), nullable=False, comment='文档名称')
    file_path = Column(String(500), nullable=False, comment='文件路径')
    file_type = Column(String(20), nullable=True, comment='文件类型')
    file_size = Column(BigInteger, nullable=True, server_default='0', comment='文件大小')
    chunk_count = Column(Integer, nullable=True, server_default='0', comment='分块数量')
    parse_status = Column(CHAR(1), nullable=True, server_default='0', comment='解析状态')
    embed_status = Column(CHAR(1), nullable=True, server_default='0', comment='向量化状态')
    error_msg = Column(String(500), nullable=True, comment='错误信息')
    user_id = Column(BigInteger, nullable=True, comment='用户ID')
    dept_id = Column(BigInteger, nullable=True, comment='部门ID')
    del_flag = Column(CHAR(1), nullable=True, server_default='0', comment='删除标志')
    create_by = Column(String(64), nullable=True, server_default="''", comment='创建者')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    update_by = Column(String(64), nullable=True, server_default="''", comment='更新者')
    update_time = Column(DateTime, nullable=True, default=datetime.now, comment='更新时间')
```

---

#### Step 4.3：编写 ORM 模型 — `module_rag/entity/do/chunk_do.py`

**注意**：这个文件有 `embedding` 字段，需要用 pgvector 提供的特殊列类型。

**要写的内容**：

```python
# module_rag/entity/do/chunk_do.py
from datetime import datetime
from sqlalchemy import CHAR, BigInteger, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from config.database import Base


class RagChunk(Base):
    """RAG文档分块表"""
    __tablename__ = 'rag_chunk'
    __table_args__ = {'comment': 'RAG文档分块表'}

    chunk_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='分块主键')
    doc_id = Column(BigInteger, nullable=False, comment='文档ID')
    kb_id = Column(BigInteger, nullable=False, comment='知识库ID')
    chunk_index = Column(Integer, nullable=False, comment='分块序号')
    content = Column(Text, nullable=False, comment='分块内容')
    token_count = Column(Integer, nullable=True, server_default='0', comment='Token数量')
    embedding = Column(Vector(1024), nullable=True, comment='文本向量')  # pgvector 向量字段
    metadata = Column(JSONB, nullable=True, comment='元数据')
    del_flag = Column(CHAR(1), nullable=True, server_default='0', comment='删除标志')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
```

---

#### Step 4.4：编写 Pydantic 请求/响应模型 — `module_rag/entity/vo/knowledge_base_vo.py`

**参考**：`module_ai/entity/vo/ai_model_vo.py`（你现有的 Pydantic 写法）

```python
# module_rag/entity/vo/knowledge_base_vo.py
from pydantic import BaseModel, Field


class KnowledgeBaseCreateModel(BaseModel):
    """创建知识库请求"""
    kb_name: str = Field(..., description='知识库名称')
    kb_desc: str | None = Field(None, description='知识库描述')
    embedding_model: str = Field(default='embedding-3', description='Embedding模型')
    chunk_size: int = Field(default=500, description='分块大小')
    chunk_overlap: int = Field(default=50, description='分块重叠')


class KnowledgeBaseUpdateModel(BaseModel):
    """更新知识库请求"""
    kb_id: int = Field(..., description='知识库ID')
    kb_name: str | None = Field(None, description='知识库名称')
    kb_desc: str | None = Field(None, description='知识库描述')
    chunk_size: int | None = Field(None, description='分块大小')
    chunk_overlap: int | None = Field(None, description='分块重叠')


class KnowledgeBaseResponseModel(BaseModel):
    """知识库响应"""
    kb_id: int
    kb_name: str
    kb_desc: str | None = None
    embedding_model: str = 'embedding-3'
    chunk_size: int = 500
    chunk_overlap: int = 50
    doc_count: int = 0
    status: str = '0'
    create_time: str | None = None

    class Config:
        from_attributes = True
```

---

#### Step 4.5：编写 Pydantic 模型 — `module_rag/entity/vo/document_vo.py`

```python
# module_rag/entity/vo/document_vo.py
from pydantic import BaseModel, Field


class DocumentUploadModel(BaseModel):
    """文档上传请求"""
    kb_id: int = Field(..., description='知识库ID')


class DocumentResponseModel(BaseModel):
    """文档响应"""
    doc_id: int
    kb_id: int
    doc_name: str
    file_type: str | None = None
    file_size: int = 0
    chunk_count: int = 0
    parse_status: str = '0'
    embed_status: str = '0'
    error_msg: str | None = None
    create_time: str | None = None

    class Config:
        from_attributes = True
```

---

#### Step 4.6：编写 Pydantic 模型 — `module_rag/entity/vo/retrieval_vo.py`

```python
# module_rag/entity/vo/retrieval_vo.py
from pydantic import BaseModel, Field


class RetrievalRequestModel(BaseModel):
    """检索请求"""
    query: str = Field(..., description='检索查询文本')
    kb_ids: list[int] = Field(..., description='知识库ID列表')
    top_k: int = Field(default=5, description='返回数量')


class ChunkResponseModel(BaseModel):
    """分块响应"""
    chunk_id: int
    doc_id: int
    kb_id: int
    content: str
    token_count: int = 0
    score: float | None = None
    metadata: dict | None = None

    class Config:
        from_attributes = True
```

---

### Step 5：编写 DAO 层（数据库访问层）

**操作位置**：`module_rag/dao/` 目录

**参考**：`module_ai/dao/ai_model_dao.py` 的写法

---

#### Step 5.1：`module_rag/dao/knowledge_base_dao.py`

```python
# module_rag/dao/knowledge_base_dao.py
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from module_rag.entity.do.knowledge_base_do import RagKnowledgeBase


class KnowledgeBaseDao:

    @classmethod
    async def get_by_id(cls, db: AsyncSession, kb_id: int) -> RagKnowledgeBase | None:
        result = await db.execute(
            select(RagKnowledgeBase).where(RagKnowledgeBase.kb_id == kb_id, RagKnowledgeBase.del_flag == '0')
        )
        return result.scalars().first()

    @classmethod
    async def get_list(cls, db: AsyncSession) -> list[RagKnowledgeBase]:
        result = await db.execute(
            select(RagKnowledgeBase).where(RagKnowledgeBase.del_flag == '0').order_by(RagKnowledgeBase.create_time.desc())
        )
        return list(result.scalars().all())

    @classmethod
    async def create(cls, db: AsyncSession, kb: RagKnowledgeBase) -> RagKnowledgeBase:
        db.add(kb)
        await db.flush()
        return kb

    @classmethod
    async def update_by_id(cls, db: AsyncSession, kb_id: int, **kwargs):
        await db.execute(
            update(RagKnowledgeBase).where(RagKnowledgeBase.kb_id == kb_id).values(**kwargs)
        )

    @classmethod
    async def delete_by_id(cls, db: AsyncSession, kb_id: int):
        await db.execute(
            update(RagKnowledgeBase).where(RagKnowledgeBase.kb_id == kb_id).values(del_flag='2')
        )
```

---

#### Step 5.2：`module_rag/dao/document_dao.py`

```python
# module_rag/dao/document_dao.py
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from module_rag.entity.do.document_do import RagDocument


class DocumentDao:

    @classmethod
    async def get_by_id(cls, db: AsyncSession, doc_id: int) -> RagDocument | None:
        result = await db.execute(
            select(RagDocument).where(RagDocument.doc_id == doc_id, RagDocument.del_flag == '0')
        )
        return result.scalars().first()

    @classmethod
    async def get_by_kb_id(cls, db: AsyncSession, kb_id: int) -> list[RagDocument]:
        result = await db.execute(
            select(RagDocument).where(RagDocument.kb_id == kb_id, RagDocument.del_flag == '0')
        )
        return list(result.scalars().all())

    @classmethod
    async def create(cls, db: AsyncSession, doc: RagDocument) -> RagDocument:
        db.add(doc)
        await db.flush()
        return doc

    @classmethod
    async def update_status(cls, db: AsyncSession, doc_id: int, **kwargs):
        await db.execute(
            update(RagDocument).where(RagDocument.doc_id == doc_id).values(**kwargs)
        )
```

---

#### Step 5.3：`module_rag/dao/chunk_dao.py`

```python
# module_rag/dao/chunk_dao.py
from sqlalchemy import select, update, text
from sqlalchemy.ext.asyncio import AsyncSession
from module_rag.entity.do.chunk_do import RagChunk


class ChunkDao:

    @classmethod
    async def bulk_insert(cls, db: AsyncSession, doc_id: int, kb_id: int, chunks: list[dict]) -> list[int]:
        """批量插入分块记录，返回 chunk_id 列表"""
        chunk_ids = []
        for i, chunk in enumerate(chunks):
            rag_chunk = RagChunk(
                doc_id=doc_id,
                kb_id=kb_id,
                chunk_index=i,
                content=chunk['content'],
                token_count=chunk.get('token_count', len(chunk['content'])),
                metadata=chunk.get('metadata'),
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
            select(RagChunk).where(RagChunk.doc_id == doc_id, RagChunk.del_flag == '0')
            .order_by(RagChunk.chunk_index)
        )
        return list(result.scalars().all())
```

---

### Step 6：编写 Utils 工具层（从 RAGFlow 抄）

**操作位置**：`module_rag/utils/` 目录

---

#### Step 6.1：`module_rag/utils/text_cleaner.py`

**抄自 RAGFlow 源码**：`utils/ragflowmodels/ragflow/rag/nlp/__init__.py` 中的 `find_codec()` 函数

```python
# module_rag/utils/text_cleaner.py
"""文本清洗工具
参考 ragflow/rag/nlp/__init__.py 的 find_codec() 和编码检测逻辑
"""
import re
import chardet


def find_codec(blob: bytes) -> str:
    """
    检测二进制数据的编码格式
    直接抄自 ragflow/rag/nlp/__init__.py 的 find_codec() 函数（第54-72行）
    """
    detected = chardet.detect(blob[:1024])
    if detected['confidence'] > 0.5:
        if detected['encoding'] == "ascii":
            return "utf-8"

    common_codecs = [
        'utf-8', 'gb2312', 'gbk', 'utf_16', 'ascii', 'big5',
        'gb18030', 'latin_1', 'utf_16_be', 'utf_16_le',
    ]
    for c in common_codecs:
        try:
            blob[:1024].decode(c)
            return c
        except Exception:
            pass
    return "utf-8"


def clean_text(text: str) -> str:
    """清洗文本：去除多余空白、特殊字符"""
    # 去除 HTML 标签
    text = re.sub(r'<[^>]+>', '', text)
    # 去除多余空白
    text = re.sub(r'\s+', ' ', text)
    # 去除首尾空白
    return text.strip()


def is_chinese(text: str) -> bool:
    """
    判断文本是否主要是中文
    直接抄自 ragflow/rag/nlp/__init__.py 的 is_chinese() 函数（第256-265行）
    """
    if not text:
        return False
    chinese = sum(1 for ch in text if '一' <= ch <= '鿿')
    return chinese / len(text) > 0.2
```

---

#### Step 6.2：`module_rag/utils/token_counter.py`

```python
# module_rag/utils/token_counter.py
"""Token 计数工具
参考 ragflow/common/token_utils.py 的 num_tokens_from_string()
MVP 阶段用字符数近似，后续可接入 tiktoken
"""


def count_tokens(text: str) -> int:
    """
    估算 Token 数量
    中文约 1 字 ≈ 1.5 token，英文约 4 字符 ≈ 1 token
    MVP 阶段简化为字符数
    """
    if not text:
        return 0
    return len(text)


def truncate_text(text: str, max_tokens: int) -> str:
    """截断文本到最大 token 数"""
    if count_tokens(text) <= max_tokens:
        return text
    return text[:max_tokens]
```

---

### Step 7：编写 Parser 层（文档解析 — 从 RAGFlow 抄核心逻辑）

**操作位置**：`module_rag/service/parser/` 目录

**RAGFlow 源码参考**：
- `utils/ragflowmodels/ragflow/deepdoc/parser/pdf_parser.py` → 你的 `pdf_parser.py`
- `utils/ragflowmodels/ragflow/deepdoc/parser/docx_parser.py` → 你的 `docx_parser.py`

---

#### Step 7.1：`module_rag/service/parser/pdf_parser.py`

**抄什么**：RAGFlow 的 PDF 解析用了 OCR + 视觉模型，太重了。你只抄它的**段落合并逻辑**和**字体大小判断标题**的思想。

**核心参考**：`ragflow/deepdoc/parser/pdf_parser.py` 中按字体大小判断标题的思路。RAGFlow 用了复杂的版面分析，你用 PyMuPDF 的 `page.get_text("dict")` 直接获取字体信息。

```python
# module_rag/service/parser/pdf_parser.py
"""PDF 文档解析器
参考 ragflow/deepdoc/parser/pdf_parser.py 的段落识别逻辑
简化版：去掉视觉模型，保留文本结构识别
"""
import fitz  # PyMuPDF


class PdfParser:
    """
    PDF 解析器
    核心思路参考 ragflow/deepdoc/parser/pdf_parser.py：
    1. 按字体大小判断标题 vs 正文
    2. 跨页段落合并
    """

    def parse(self, file_path: str) -> list[dict]:
        """
        解析 PDF 文件
        返回: [{"text": "段落内容", "page": 1, "type": "text/title"}, ...]
        """
        doc = fitz.open(file_path)
        blocks = []

        for page_num, page in enumerate(doc):
            text_dict = page.get_text("dict")
            for block in text_dict["blocks"]:
                if block["type"] != 0:  # 只处理文字块
                    continue
                block_text = self._extract_block_text(block)
                if not block_text.strip():
                    continue
                block_type = self._classify_block(block)
                blocks.append({
                    "text": block_text,
                    "page": page_num + 1,
                    "type": block_type,
                })

        doc.close()
        return self._merge_paragraphs(blocks)

    def _extract_block_text(self, block: dict) -> str:
        """提取 block 中的所有文字"""
        lines_text = []
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                lines_text.append(span.get("text", ""))
        return "".join(lines_text)

    def _classify_block(self, block: dict) -> str:
        """
        参考 ragflow/deepdoc/parser/pdf_parser.py 的标题识别：
        字体大小 > 阈值 → title；否则 → text
        """
        font_sizes = []
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                if span.get("text", "").strip():
                    font_sizes.append(span.get("size", 12))

        if not font_sizes:
            return "text"

        max_font_size = max(font_sizes)
        # RAGFlow 的判断逻辑：大于正文字体的认为是标题
        return "title" if max_font_size > 14 else "text"

    def _merge_paragraphs(self, blocks: list[dict]) -> list[dict]:
        """
        关键：把被切碎的段落合并回来
        参考 ragflow/rag/nlp/__init__.py 的 naive_merge() 函数逻辑（第1070-1126行）
        核心判断：上一个 block 没有以句号等结尾，且下一个 block 不是标题 → 合并
        """
        if not blocks:
            return []

        merged = [dict(blocks[0])]
        for block in blocks[1:]:
            last = merged[-1]
            should_merge = (
                last["type"] == "text"
                and block["type"] == "text"
                and not last["text"].rstrip().endswith(("。", "！", "？", ".", "!", "?", "；", ";"))
            )
            if should_merge:
                merged[-1]["text"] += block["text"]
            else:
                merged.append(dict(block))

        return merged
```

---

#### Step 7.2：`module_rag/service/parser/docx_parser.py`

**抄什么**：`ragflow/deepdoc/parser/docx_parser.py` 的 `RAGFlowDocxParser` 类的段落/表格遍历逻辑。

```python
# module_rag/service/parser/docx_parser.py
"""DOCX 文档解析器
参考 ragflow/deepdoc/parser/docx_parser.py 的 RAGFlowDocxParser 类
提取段落文字和表格内容
"""
from docx import Document


class DocxParser:

    def parse(self, file_path: str) -> list[dict]:
        """
        解析 DOCX 文件
        返回: [{"text": "内容", "page": 0, "type": "text/title/table"}, ...]
        """
        doc = Document(file_path)
        blocks = []

        for element in doc.element.body:
            tag = element.tag.split('}')[-1] if '}' in element.tag else element.tag

            if tag == 'p':
                # 段落处理 — 参考 ragflow docx_parser 的段落遍历方式
                para_text = ''.join(node.text or '' for node in element.iter() if node.text)
                if not para_text.strip():
                    continue

                # 判断是否标题（参考 ragflow 的 docx_question_level 函数）
                para_style = ''
                for p in doc.paragraphs:
                    if p._element is element:
                        para_style = p.style.name if p.style else ''
                        break

                block_type = 'title' if 'Heading' in para_style or 'heading' in para_style else 'text'
                blocks.append({
                    "text": para_text.strip(),
                    "page": 0,
                    "type": block_type,
                })

            elif tag == 'tbl':
                # 表格处理 — 参考 ragflow 的 __extract_table_content 方法
                table_text = self._extract_table(element, doc)
                if table_text.strip():
                    blocks.append({
                        "text": table_text,
                        "page": 0,
                        "type": "table",
                    })

        return blocks

    def _extract_table(self, tbl_element, doc) -> str:
        """提取表格文本 — 参考 ragflow 的 __extract_table_content"""
        for table in doc.tables:
            if table._element is tbl_element:
                rows = []
                for row in table.rows:
                    rows.append(' | '.join(cell.text.strip() for cell in row.cells))
                return '\n'.join(rows)
        return ""
```

---

#### Step 7.3：`module_rag/service/parser/txt_parser.py`（自己写，很简单）

```python
# module_rag/service/parser/txt_parser.py
"""TXT/MD 文件解析器"""
from module_rag.utils.text_cleaner import find_codec


class TxtParser:

    def parse(self, file_path: str) -> list[dict]:
        """解析 TXT/MD 文件"""
        with open(file_path, 'rb') as f:
            blob = f.read()

        codec = find_codec(blob)
        text = blob.decode(codec, errors='ignore')

        # 按空行分段
        paragraphs = text.split('\n\n')
        blocks = []
        for i, para in enumerate(paragraphs):
            para = para.strip()
            if not para:
                continue
            # Markdown 标题识别
            block_type = 'title' if para.startswith('#') else 'text'
            blocks.append({
                "text": para,
                "page": 0,
                "type": block_type,
            })

        return blocks
```

---

#### Step 7.4：`module_rag/service/parser/__init__.py`（解析器工厂）

```python
# module_rag/service/parser/__init__.py
from module_rag.service.parser.pdf_parser import PdfParser
from module_rag.service.parser.docx_parser import DocxParser
from module_rag.service.parser.txt_parser import TxtParser

# 文件类型 → 解析器映射
PARSER_MAP = {
    '.pdf': PdfParser,
    '.docx': DocxParser,
    '.doc': DocxParser,
    '.txt': TxtParser,
    '.md': TxtParser,
}


def get_parser(file_type: str):
    """根据文件类型获取对应的解析器"""
    parser_cls = PARSER_MAP.get(file_type.lower())
    if not parser_cls:
        raise ValueError(f"不支持的文件类型: {file_type}")
    return parser_cls()
```

---

### Step 8：编写 Chunker 层（文本分块 — 从 RAGFlow 抄核心逻辑）

**操作位置**：`module_rag/service/chunker/` 目录

**RAGFlow 源码参考**：`utils/ragflowmodels/ragflow/rag/nlp/__init__.py` 中的 `naive_merge()` 函数（第1070-1126行）

---

#### Step 8.1：`module_rag/service/chunker/fixed_chunker.py`

**抄什么**：RAGFlow 的 `naive_merge()` 函数的核心逻辑——固定窗口 + 句子边界对齐 + overlap。

```python
# module_rag/service/chunker/fixed_chunker.py
"""固定大小分块器
核心思路来自 ragflow/rag/nlp/__init__.py 的 naive_merge() 函数（第1070-1126行）
1. 按 token 数累积分块
2. 超过 chunk_size 时在句子边界切分
3. 相邻 chunk 之间保留 overlap
"""
import re


class FixedChunker:

    SENTENCE_ENDS = set("。！？；.!?;\n")

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str, metadata: dict = None) -> list[dict]:
        """
        分块主函数
        参考 ragflow naive_merge() 的逻辑：
        - 累积 token 直到超过 chunk_size
        - 在句子边界处切分
        - 保留 overlap
        """
        if not text or not text.strip():
            return []

        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) <= self.chunk_size:
                current_chunk += para + "\n\n"
            else:
                # 当前 chunk 已满，保存
                if current_chunk:
                    chunks.append(self._make_chunk(current_chunk.strip(), metadata))
                    # overlap：取当前 chunk 尾部
                    overlap_text = current_chunk[-self.overlap:] if len(current_chunk) > self.overlap else current_chunk

                # 如果段落本身超长，按句子边界切
                if len(para) > self.chunk_size:
                    sub_chunks = self._split_at_sentence(para, metadata, overlap_text)
                    chunks.extend(sub_chunks)
                    current_chunk = sub_chunks[-1]["content"][-self.overlap:] if sub_chunks else ""
                else:
                    current_chunk = overlap_text + para + "\n\n"

        if current_chunk.strip():
            chunks.append(self._make_chunk(current_chunk.strip(), metadata))

        return chunks

    def _split_at_sentence(self, text: str, metadata: dict, prefix: str = "") -> list[dict]:
        """
        在句子边界处切分长文本
        参考 ragflow naive_merge 中的 overlap 逻辑
        """
        chunks = []
        current = prefix

        for char in text:
            current += char
            if char in self.SENTENCE_ENDS and len(current) >= self.chunk_size:
                chunks.append(self._make_chunk(current.strip(), metadata))
                current = current[-self.overlap:]

        if current.strip():
            chunks.append(self._make_chunk(current.strip(), metadata))

        return chunks

    def _make_chunk(self, content: str, metadata: dict) -> dict:
        return {
            "content": content,
            "token_count": len(content),
            "metadata": metadata or {},
        }
```

---

### Step 9：编写 Embedding Service（向量化服务 — 从 RAGFlow 抄批量逻辑）

**操作位置**：`module_rag/service/embedding_service.py`

**RAGFlow 源码参考**：`utils/ragflowmodels/ragflow/rag/llm/embedding_model.py` 中的 `ZhipuEmbed` 类的批量处理逻辑

```python
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
    BATCH_SIZE = 25  # 智谱 API 每批最多 25 条

    @classmethod
    def _get_client(cls) -> AsyncOpenAI:
        return AsyncOpenAI(
            api_key=os.getenv('ZHIPU_API_KEY', ''),
            base_url='https://open.bigmodel.cn/api/paas/v4',
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
            batch = texts[i: i + cls.BATCH_SIZE]

            # 重试逻辑 — 参考 ragflow 的错误恢复设计
            for retry in range(3):
                try:
                    response = await client.embeddings.create(
                        model="embedding-3",
                        input=batch,
                    )
                    batch_embeddings = [item.embedding for item in response.data]
                    all_embeddings.extend(batch_embeddings)
                    break
                except Exception as e:
                    if retry == 2:
                        raise
                    await asyncio.sleep(1 * (retry + 1))

            # 防止 API 限速
            if i + cls.BATCH_SIZE < len(texts):
                await asyncio.sleep(0.1)

        return all_embeddings

    @classmethod
    async def embed_single(cls, text: str) -> list[float]:
        """单条文本向量化"""
        results = await cls.embed_texts([text])
        return results[0]
```

---

### Step 10：编写 Retrieval Service（混合检索 — 从 RAGFlow 抄 RRF 融合）

**操作位置**：`module_rag/service/retrieval_service.py`

**RAGFlow 源码参考**：`utils/ragflowmodels/ragflow/rag/nlp/search.py` 中的 `Dealer` 类的混合检索逻辑

```python
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
```

---

### Step 11：编写 Document Service（Pipeline 编排 — 从 RAGFlow 抄状态机思路）

**操作位置**：`module_rag/service/document_service.py`

**RAGFlow 源码参考**：`utils/ragflowmodels/ragflow/rag/svr/task_executor.py` 的 `TaskManager` 状态机流转

```python
# module_rag/service/document_service.py
"""文档处理 Pipeline
参考 ragflow/rag/svr/task_executor.py 的 TaskManager 状态机设计
上传 → 解析 → 分块 → 向量化 → 完成
"""
from sqlalchemy.ext.asyncio import AsyncSession
from module_rag.dao.document_dao import DocumentDao
from module_rag.dao.chunk_dao import ChunkDao
from module_rag.dao.knowledge_base_dao import KnowledgeBaseDao
from module_rag.service.parser import get_parser
from module_rag.service.chunker.fixed_chunker import FixedChunker
from module_rag.service.embedding_service import EmbeddingService


class DocumentService:

    @classmethod
    async def process_document(cls, db: AsyncSession, doc_id: int):
        """
        文档处理主流程
        状态机设计参考 ragflow/rag/svr/task_executor.py 的 do_handle_task

        状态流转：
        parse_status: 0(待处理) → 1(解析中) → 2(完成) / 9(失败)
        embed_status: 0(待处理) → 1(向量化中) → 2(完成) / 9(失败)
        """
        doc = await DocumentDao.get_by_id(db, doc_id)
        if not doc:
            raise ValueError(f"文档不存在: {doc_id}")

        try:
            # ===== Step 1: 解析文档 =====
            await DocumentDao.update_status(db, doc_id, parse_status="1")
            parser = get_parser(doc.file_type)
            blocks = parser.parse(doc.file_path)

            # ===== Step 2: 文本分块 =====
            kb = await KnowledgeBaseDao.get_by_id(db, doc.kb_id)
            chunker = FixedChunker(
                chunk_size=kb.chunk_size if kb else 500,
                overlap=kb.chunk_overlap if kb else 50,
            )
            all_chunks = []
            for block in blocks:
                chunks = chunker.chunk(
                    text=block["text"],
                    metadata={"page": block.get("page"), "type": block.get("type")}
                )
                all_chunks.extend(chunks)

            # ===== Step 3: 保存分块记录 =====
            await DocumentDao.update_status(db, doc_id, parse_status="2", embed_status="1")
            chunk_ids = await ChunkDao.bulk_insert(db, doc_id, doc.kb_id, all_chunks)

            # ===== Step 4: 批量向量化 =====
            texts = [c["content"] for c in all_chunks]
            embeddings = await EmbeddingService.embed_texts(texts)

            # ===== Step 5: 更新向量 =====
            await ChunkDao.bulk_update_embeddings(db, chunk_ids, embeddings)
            await DocumentDao.update_status(
                db, doc_id,
                embed_status="2",
                chunk_count=len(all_chunks)
            )

        except Exception as e:
            await DocumentDao.update_status(
                db, doc_id,
                embed_status="9",
                error_msg=str(e)[:500]
            )
            raise
```

---

### Step 12：编写 Knowledge Base Service（知识库 CRUD）

**操作位置**：`module_rag/service/knowledge_base_service.py`

```python
# module_rag/service/knowledge_base_service.py
"""知识库管理服务"""
from sqlalchemy.ext.asyncio import AsyncSession
from module_rag.dao.knowledge_base_dao import KnowledgeBaseDao
from module_rag.entity.do.knowledge_base_do import RagKnowledgeBase
from module_rag.entity.vo.knowledge_base_vo import KnowledgeBaseCreateModel, KnowledgeBaseUpdateModel


class KnowledgeBaseService:

    @classmethod
    async def create(cls, db: AsyncSession, data: KnowledgeBaseCreateModel, user_id: int) -> RagKnowledgeBase:
        kb = RagKnowledgeBase(
            kb_name=data.kb_name,
            kb_desc=data.kb_desc,
            embedding_model=data.embedding_model,
            chunk_size=data.chunk_size,
            chunk_overlap=data.chunk_overlap,
            user_id=user_id,
        )
        return await KnowledgeBaseDao.create(db, kb)

    @classmethod
    async def get_list(cls, db: AsyncSession) -> list[RagKnowledgeBase]:
        return await KnowledgeBaseDao.get_list(db)

    @classmethod
    async def get_by_id(cls, db: AsyncSession, kb_id: int) -> RagKnowledgeBase | None:
        return await KnowledgeBaseDao.get_by_id(db, kb_id)

    @classmethod
    async def update(cls, db: AsyncSession, data: KnowledgeBaseUpdateModel):
        update_data = {k: v for k, v in data.model_dump().items() if v is not None and k != 'kb_id'}
        await KnowledgeBaseDao.update_by_id(db, data.kb_id, **update_data)

    @classmethod
    async def delete(cls, db: AsyncSession, kb_id: int):
        await KnowledgeBaseDao.delete_by_id(db, kb_id)
```

---

### Step 13：编写 Controller 层（API 接口）

**操作位置**：`module_rag/controller/` 目录

**参考**：`module_ai/controller/ai_chat_controller.py` 的写法（`APIRouterPro` + `PreAuthDependency`）

---

#### Step 13.1：`module_rag/controller/knowledge_base_controller.py`

```python
# module_rag/controller/knowledge_base_controller.py
from typing import Annotated
from fastapi import Body, Path
from sqlalchemy.ext.asyncio import AsyncSession
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_rag.entity.vo.knowledge_base_vo import KnowledgeBaseCreateModel, KnowledgeBaseUpdateModel
from module_rag.service.knowledge_base_service import KnowledgeBaseService
from utils.response_util import ResponseUtil

knowledge_base_controller = APIRouterPro(
    prefix='/rag/kb', order_num=20, tags=['RAG管理-知识库'], dependencies=[PreAuthDependency()]
)


@knowledge_base_controller.post('', summary='创建知识库')
async def create_kb(
    data: KnowledgeBaseCreateModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: CurrentUserModel = CurrentUserDependency(),
):
    kb = await KnowledgeBaseService.create(query_db, data, current_user.user.user_id)
    return ResponseUtil.success(data={"kb_id": kb.kb_id})


@knowledge_base_controller.get('/list', summary='获取知识库列表')
async def get_kb_list(
    query_db: Annotated[AsyncSession, DBSessionDependency()],
):
    kb_list = await KnowledgeBaseService.get_list(query_db)
    return ResponseUtil.success(data=[{
        "kb_id": kb.kb_id,
        "kb_name": kb.kb_name,
        "kb_desc": kb.kb_desc,
        "doc_count": kb.doc_count,
        "create_time": str(kb.create_time),
    } for kb in kb_list])
```

---

#### Step 13.2：`module_rag/controller/document_controller.py`

```python
# module_rag/controller/document_controller.py
import os
from typing import Annotated
from fastapi import File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from config.env import UploadConfig
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_rag.dao.document_dao import DocumentDao
from module_rag.entity.do.document_do import RagDocument
from module_rag.service.document_service import DocumentService
from utils.response_util import ResponseUtil

document_controller = APIRouterPro(
    prefix='/rag/document', order_num=21, tags=['RAG管理-文档'], dependencies=[PreAuthDependency()]
)


@document_controller.post('/upload/{kb_id}', summary='上传文档到知识库')
async def upload_document(
    kb_id: int,
    file: UploadFile = File(...),
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
    current_user: CurrentUserModel = CurrentUserDependency(),
):
    # 保存文件
    upload_dir = os.path.join(UploadConfig.UPLOAD_PATH, 'rag')
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, 'wb') as f:
        content = await file.read()
        f.write(content)

    # 获取文件类型
    file_type = os.path.splitext(file.filename)[1].lower()

    # 创建文档记录
    doc = RagDocument(
        kb_id=kb_id,
        doc_name=file.filename,
        file_path=file_path,
        file_type=file_type,
        file_size=len(content),
        user_id=current_user.user.user_id,
    )
    doc = await DocumentDao.create(query_db, doc)

    # 触发异步处理（MVP 阶段同步执行）
    await DocumentService.process_document(query_db, doc.doc_id)
    await query_db.commit()

    return ResponseUtil.success(data={"doc_id": doc.doc_id})


@document_controller.get('/list/{kb_id}', summary='获取知识库下的文档列表')
async def get_doc_list(
    kb_id: int,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
):
    docs = await DocumentDao.get_by_kb_id(query_db, kb_id)
    return ResponseUtil.success(data=[{
        "doc_id": d.doc_id,
        "doc_name": d.doc_name,
        "file_type": d.file_type,
        "parse_status": d.parse_status,
        "embed_status": d.embed_status,
        "chunk_count": d.chunk_count,
    } for d in docs])
```

---

#### Step 13.3：`module_rag/controller/retrieval_controller.py`

```python
# module_rag/controller/retrieval_controller.py
from typing import Annotated
from fastapi import Body
from sqlalchemy.ext.asyncio import AsyncSession
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import PreAuthDependency
from common.router import APIRouterPro
from module_rag.entity.vo.retrieval_vo import RetrievalRequestModel
from module_rag.service.embedding_service import EmbeddingService
from module_rag.service.retrieval_service import RetrievalService
from utils.response_util import ResponseUtil

retrieval_controller = APIRouterPro(
    prefix='/rag/retrieval', order_num=22, tags=['RAG管理-检索'], dependencies=[PreAuthDependency()]
)


@retrieval_controller.post('/search', summary='混合检索')
async def search(
    data: RetrievalRequestModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
):
    # 1. 向量化查询
    query_embedding = await EmbeddingService.embed_single(data.query)

    # 2. 混合检索
    results = await RetrievalService.hybrid_search(
        db=query_db,
        query_text=data.query,
        query_embedding=query_embedding,
        kb_ids=data.kb_ids,
        top_k=data.top_k,
    )

    return ResponseUtil.success(data=[{
        "chunk_id": r["chunk_id"],
        "doc_id": r["doc_id"],
        "content": r["content"][:200],
        "score": float(r.get("score", 0)),
    } for r in results])
```

---

### Step 14：配置环境变量

**操作位置**：`.env.test` 文件末尾追加

```env
# -------- RAG 配置 --------
# 智谱 API Key（用于 Embedding）
ZHIPU_API_KEY=your_zhipu_api_key_here
# Embedding 模型名称
ZHIPU_EMBED_MODEL=embedding-3
# Embedding 向量维度（embedding-3 是 1024 维）
ZHIPU_EMBED_DIM=1024
```

---

### Step 15：验证模块可被自动注册

**操作位置**：项目根目录，启动应用

你的项目使用 `common/router.py` 的自动注册机制，它会自动扫描所有 `module_*/controller/*.py` 文件中定义的 `APIRouterPro` 实例。

**验证方法**：

```bash
# 启动应用
python app.py
```

然后访问 Swagger 文档页面，检查是否出现 `RAG管理-知识库`、`RAG管理-文档`、`RAG管理-检索` 这三个 tag 的接口。

---

### Step 16：端到端测试

**测试流程**：

```
1. 创建知识库 → POST /rag/kb
2. 上传文档 → POST /rag/document/upload/{kb_id}（上传一个 PDF）
3. 查看文档列表 → GET /rag/document/list/{kb_id}（确认 parse_status=2, embed_status=2）
4. 检索测试 → POST /rag/retrieval/search
```

**验证 SQL**：

```sql
-- 查看分块结果
SELECT chunk_id, chunk_index, token_count, LEFT(content, 50) as preview
FROM rag_chunk
WHERE doc_id = 1
ORDER BY chunk_index;
```

---

## 十一、文件创建顺序总结

按以下顺序逐个创建文件，每创建完一个就确认无语法错误再继续：

| 顺序 | 文件路径 | 说明 | 抄自 RAGFlow 的什么 |
|---|---|---|---|
| 1 | 安装依赖 `pip install pgvector PyMuPDF python-docx chardet` | 基础依赖 | - |
| 2 | PostgreSQL 执行建表 SQL | 3 张表 + 索引 | - |
| 3 | `module_rag/` 整个目录骨架 | 11 个 `__init__.py` | - |
| 4 | `module_rag/entity/do/knowledge_base_do.py` | 知识库 ORM | - |
| 5 | `module_rag/entity/do/document_do.py` | 文档 ORM | - |
| 6 | `module_rag/entity/do/chunk_do.py` | 分块 ORM（含 Vector 字段） | - |
| 7 | `module_rag/entity/vo/knowledge_base_vo.py` | 知识库 Pydantic | - |
| 8 | `module_rag/entity/vo/document_vo.py` | 文档 Pydantic | - |
| 9 | `module_rag/entity/vo/retrieval_vo.py` | 检索 Pydantic | - |
| 10 | `module_rag/utils/text_cleaner.py` | 编码检测 + 文本清洗 | `rag/nlp/__init__.py` 的 `find_codec()` + `is_chinese()` |
| 11 | `module_rag/utils/token_counter.py` | Token 计数 | `common/token_utils.py` 的 `num_tokens_from_string()` |
| 12 | `module_rag/service/parser/pdf_parser.py` | PDF 解析 | `deepdoc/parser/pdf_parser.py` 的字体大小判断标题 + 段落合并 |
| 13 | `module_rag/service/parser/docx_parser.py` | DOCX 解析 | `deepdoc/parser/docx_parser.py` 的段落/表格遍历 |
| 14 | `module_rag/service/parser/txt_parser.py` | TXT/MD 解析 | 自己写 |
| 15 | `module_rag/service/parser/__init__.py` | 解析器工厂 | - |
| 16 | `module_rag/service/chunker/fixed_chunker.py` | 固定分块 + overlap | `rag/nlp/__init__.py` 的 `naive_merge()` |
| 17 | `module_rag/service/embedding_service.py` | Embedding 批量处理 | `rag/llm/embedding_model.py` 的 `ZhipuEmbed` |
| 18 | `module_rag/service/retrieval_service.py` | 向量 + BM25 + RRF | `rag/nlp/search.py` 的 `Dealer` 类 |
| 19 | `module_rag/service/document_service.py` | Pipeline 编排 | `rag/svr/task_executor.py` 的状态机 |
| 20 | `module_rag/service/knowledge_base_service.py` | 知识库 CRUD | - |
| 21 | `module_rag/dao/knowledge_base_dao.py` | 知识库 DAO | - |
| 22 | `module_rag/dao/document_dao.py` | 文档 DAO | - |
| 23 | `module_rag/dao/chunk_dao.py` | 分块 DAO（含向量更新） | - |
| 24 | `module_rag/controller/knowledge_base_controller.py` | 知识库 API | - |
| 25 | `module_rag/controller/document_controller.py` | 文档上传 API | - |
| 26 | `module_rag/controller/retrieval_controller.py` | 检索 API | - |
| 27 | `.env.test` 追加 RAG 配置 | 环境变量 | - |
| 28 | 启动验证 + 端到端测试 | - | - |

---

## 十二、RAGFlow 源码阅读顺序（配合实现）

在实现每个模块时，按以下顺序打开 RAGFlow 源码对照阅读：

| 实现步骤 | 打开的 RAGFlow 文件 | 重点看的内容 |
|---|---|---|
| Step 7（Parser） | `utils/ragflowmodels/ragflow/deepdoc/parser/pdf_parser.py` | `RAGFlowPdfParser.__init__` → 看它怎么用 pdfplumber |
| Step 7（Parser） | `utils/ragflowmodels/ragflow/deepdoc/parser/docx_parser.py` | `RAGFlowDocxParser.__extract_table_content` → 看表格提取 |
| Step 8（Chunker） | `utils/ragflowmodels/ragflow/rag/nlp/__init__.py` 第1070-1126行 | `naive_merge()` → 这是你要抄的核心函数 |
| Step 9（Embedding） | `utils/ragflowmodels/ragflow/rag/llm/embedding_model.py` | 搜索 `class.*Embed` → 看批量 encode 的 batch_size 和 retry |
| Step 10（Retrieval） | `utils/ragflowmodels/ragflow/rag/nlp/search.py` | `Dealer` 类 → 看向量检索和 RRF 融合 |
| Step 11（Pipeline） | `utils/ragflowmodels/ragflow/rag/svr/task_executor.py` | `TaskManager` → 看状态机和错误恢复 |

---

*文档版本 v2.0 | 更新日期 2026-06-01 | 追加分步实现路径*
