## 项目背景

我是技术方。现在给一个社会工作的老师做软件开发。她的诉求是
给系统上传社会学、社会工作、心理学等相关学科的资料
让做了社会实践的同学登录系统，有四个部分（模块），一点点引导学生加深理论认识，完成论文基础骨架的搭建。

这四个模块分别是：
<p>**项目的具体措施：**</p><p>1\.**优化与扩展支撑能力训练的"结构化实践知识库"**。这是所有教学活动的基石。运用生成式人工智能与人工分析相结合的方法，对海量质性论文与学生文本进行的人机协同分析，构建以"实践判断单元"为核心的JSON数据结构，将隐性知识转化为可教学利用的素材，为学生问题生成与行动决策提供可参照的知识支撑。</p><p>2\.**打造"四区联动"的情境化行动研究学习系统**。基于数据资源构建情境化学习平台，采用"情境区—决策区—反思区—研究生成区"的界面结构（如图2所示）。"情境区"呈现复杂的真实实践案例片段，引导学生"进入"场域，识别和界定问题；"决策区"学生在关键节点做出行动选择并阐述理由，平台可提供多种"历史方案"作为参照；"反思区"支持学生撰写反思日志，系统通过结构化提问引导其进行反身性思考；"研究生成区"帮助学生梳理前期材料，逐步形成研究问题、论文框架乃至初稿段落。将行动研究全过程嵌入教学环境，引导学生完成从情境理解到研究表达的连续学习过程，形成可操作的学习路径。</p><p>并且，在"反思区"与"研究生成区"，重点开发三类智能模块：一是反身性引导模块，在学生撰写日志时，基于其文本内容，自动推送问题链，促使其从"描述经历"转向"分析自身与情境的互动"，达成"反身性反思"；二是过程追踪模块，自动关联学生多轮"行动-反思"记录，可视化其思维演变过程，强化"循环"意识；三是研究表达支架模块，基于学生输入的研究想法和过程材料，生成论文大纲、提供段落写作建议或学术语言润色，辅助完成从实践材料到研究文本的跨越。</p><p></p><p></p><p>3\.**建立基于过程性数据的动态评价与改进机制**。围绕能力链条，构建融合"系统日志、反思文本、任务表现、教师观察"的多维评价体系，实现从"总结性评分"到"诊断性反馈"的转变，并以此驱动教学方案的持续优化。</p><p></p><p>**创新点：**</p><p>本项目的创新是一场"以能力生成为中心"的系统性教学重构：</p><p>1\.**能力模型创新**：首次系统提炼出社会工作行动研究"情境进入—问题生成—行动决策—反身性反思—研究表达"的能力链条，并将"反身性"作为可教学、可训练的核心机制，为研究方法类课程提供了清晰的能力本位改革框架。</p><p>2\.**技术应用创新**：超越将人工智能视作信息检索或对话工具，将其深度设计为"智能学习支架"，精准介入学生最难突破的"反思深度"与"文本转化"环节，实现了人工智能在教学中的角色跃迁。</p><p>3\.**教学过程创新**：通过"四区联动"系统与课程重组，实现了"实践操作、反身性反思、研究表达"在时间与空间上的统一，创立了"做-思-写"一体化的行动研究教学模式。</p><p></p>|

## 我的诉求
我想给她开发这个系统，赚点外快。基础登录啊、鉴权啊我使用的是ruoyifast框架。
现在需要对核心四区联动进行整体架构考虑和代码实现。所以我想应该从哪里入手呢？先做什么？后做什么？我需要一个明确的任务规划。

## 提問12：想自己實現的同時參考ragflow
我想用ragflow，但是我同时也想学习整个rag的框架。因为做rag的业务，不懂整个rag的流程就是调用别人的api也很可悲。至于服务器，我可以申请2台。或者大一点的一台也可以。慢一点也可以。暂时先不用考虑并发的问题，有5到10个人能用就不错了。

我想用好一点的框架，但是我又不想只调用这个api，你说怎么办


## 回答12：以ragflow為終點，自己去實現核心業務代碼
你这个想法非常好——既要学懂 RAG，又要用好框架。我给你一个**"自建 + 对照学习"**的策略：

核心思路：每一层自己写，RAGFlow 当"标准答案"

你的 module_rag/（自己写每一层）
    │
    │  遇到问题或想对比效果时
    ▼
RAGFlow（部署一份当参考）
具体来说：

你自己写的 5 层 Pipeline
层	你自己实现	用的底层库	RAGFlow 对应
① 文档解析	自己写 parser	PyMuPDF / python-docx / markdown	RAGFlow 的 deepdoc 引擎
② 文本分块	自己写 chunker	langchain TextSplitter	RAGFlow 的分块策略
③ 向量化	自己调 API	智谱 Embedding-3 SDK	RAGFlow 的 embedding 模块
④ 向量存储	自己写 SQL	PgVector	RAGFlow 用的 Elasticsearch
⑤ 检索 + 重排	自己写检索逻辑	cosine similarity + LLM rerank	RAGFlow 的 retrieval
每一层你都自己写代码，知道输入是什么、输出是什么、为什么这么处理。

RAGFlow 的角色：不是黑盒 API，而是"标准答案"
用途	怎么用
学流程	部署 RAGFlow，上传同一份文档，看它的分块结果、检索结果
对比效果	你的检索结果 vs RAGFlow 的检索结果，找差距
兜底方案	扫描件 PDF / 复杂表格等你自己解析不了的，调 RAGFlow API 处理
生产保底	万一你的 Pipeline 效果不够好，可以逐步切换到 RAGFlow
代码层面：你的 module_rag 长这样

# module_rag/service/embedding_service.py
# 你自己写：直接调智谱 API，知道每一步在干什么
class EmbeddingService:
    @classmethod
    async def embed_texts(cls, texts: list[str]) -> list[list[float]]:
        """你自己调 Embedding API，理解向量是怎么生成的"""
        client = AsyncOpenAI(api_key=..., base_url="https://open.bigmodel.cn/...")
        response = await client.embeddings.create(model="embedding-3", input=texts)
        return [item.embedding for item in response.data]  # 1024维的浮点数组


# module_rag/service/chunk_service.py
# 你自己写分块逻辑，理解 chunk_size 和 overlap 的意义
class ChunkService:
    @classmethod
    def split_text(cls, text: str, chunk_size=500, overlap=50) -> list[str]:
        chunks = []
        for i in range(0, len(text), chunk_size - overlap):
            chunks.append(text[i:i + chunk_size])
        return chunks


# module_rag/service/retrieval_service.py
# 你自己写检索 SQL，理解向量相似度计算
class RetrievalService:
    @classmethod
    async def search(cls, db, query_embedding, kb_ids, top_k=5):
        # 你写原生 SQL，理解 cosine similarity 是怎么算的
        sql = text("""
            SELECT content, 1 - (embedding <=> :vec::vector) AS similarity
            FROM rag_chunk WHERE kb_id = ANY(:kb_ids)
            ORDER BY embedding <=> :vec::vector LIMIT :top_k
        """)
        ...

# module_rag/service/ragflow_fallback_service.py
# 兜底：你自己写的搞不定时，用 RAGFlow 处理复杂文档
class RAGFlowFallbackService:
    """只在复杂文档（扫描件/表格）时才调用 RAGFlow"""
    @classmethod
    async def parse_complex_pdf(cls, file_path: str) -> str:
        from ragflow_sdk import RAGFlow
        client = RAGFlow(api_key=..., base_url="http://localhost:9380")
        # 只用 RAGFlow 的解析能力，不用它的全套
        ...
学习路线：边做边学，5 步走

第 1 步：部署 RAGFlow，上传一份 PDF，观察它的
         分块结果 → 向量 → 检索结果
         （知道"好的 RAG"长什么样）
              │
              ▼
第 2 步：自己写文档解析（简单 PDF/TXT 先搞通）
         对比：你提取的文本 vs RAGFlow 提取的文本
              │
              ▼
第 3 步：自己写分块 + Embedding
         对比：你的分块 vs RAGFlow 的分块
         理解：为什么 chunk_size=500？overlap 有什么用？
              │
              ▼
第 4 步：自己写向量检索
         对比：你的 top5 vs RAGFlow 的 top5
         理解：cosine similarity 分数多少算"相关"？
              │
              ▼
第 5 步：自己写 RAG 对话（检索结果拼 Prompt → 调 LLM）
         对比：你的回答 vs RAGFlow 的回答
         理解：检索质量如何影响最终回答？
服务器部署方案
一台服务器就够了：


┌──────────────────────────────────────────┐
│              你的服务器（1台）             │
│                                          │
│  ┌──────────────────────────────────┐    │
│  │  RuoYiFast 后端（已有）           │    │
│  │  + module_rag（你自建的 RAG 层）  │    │
│  │  + PgVector（PostgreSQL 扩展）    │    │
│  │  + Redis（已有）                  │    │
│  └──────────────────────────────────┘    │
│                                          │
│  ┌──────────────────────────────────┐    │
│  │  RAGFlow（Docker，学习+兜底用）   │    │
│  │  端口: 9380                      │    │
│  └──────────────────────────────────┘    │
└──────────────────────────────────────────┘
5-10 人用完全没压力，不需要考虑并发。

总结
你的目标	方案
学懂 RAG	每一层自己写，知道输入输出为什么
用好框架	RAGFlow 部署一份当标准答案 + 复杂文档兜底
生产可用	主体用你自己的 Pipeline，遇到短板用 RAGFlow 补
开发周期	约 14 天（和你自建的方案一样，但每一步都有 RAGFlow 对照）
要开始的话，第一步是：部署 RAGFlow + 创建 module_rag 骨架。你说开始我就拆任务。

---
---

# 完整开发任务规划（基于 RAGFlow 框架）

> 编写日期：2026年5月29日（修订版）
> 预计总工期：约 22 个工作日（4.5 周）
> 核心策略：**RAGFlow 作为 RAG 引擎，module_rag 作为业务适配层，读源码学原理**

---

## 策略变更说明

之前的方案是"每一层自己从零写，RAGFlow 当参考"。现在改为：

| | 旧方案 | 新方案 |
|---|---|---|
| RAG Pipeline | 自己用 PgVector + PyMuPDF 从零实现 | 直接用 RAGFlow（成熟的解析、分块、向量检索） |
| module_rag 的角色 | 完整的 RAG 实现（5层 Pipeline） | 业务适配层（调用 RAGFlow SDK + 本地数据管理） |
| 学习方式 | 边写边学，RAGFlow 当对照 | 读 RAGFlow 源码理解原理，改 prompt/分块策略适配业务 |
| 省掉的工作 | — | 文档解析、分块算法、向量存储、检索引擎 |
| 数据库 | 需要 PgVector 扩展 | 不需要，RAGFlow 自带 Elasticsearch |
| 开发周期 | RAG 模块 6天 | RAG 模块 3天（省 3天） |

**你需要自己写的核心代码**：
1. module_rag 适配层（对接 RAGFlow SDK，管理本地元数据）
2. 四区联动的业务逻辑（这是 RAGFlow 帮不了你的）
3. 反身性 AI 提问引擎（整个系统的核心创新）
4. 前端页面

**RAGFlow 帮你搞定的事**：
- 文档解析（PDF/DOCX/TXT/MD，含 OCR）
- 文本分块（支持 naive/paper/book/laws 等多种策略）
- 向量化和存储（Elasticsearch）
- 向量检索 + 混合检索（向量 + 关键词 BM25）
- 对话管理（Chat Assistant，可自定义 Prompt）

---

## 整体依赖关系图

```
阶段0: 部署 RAGFlow + 学习源码结构
  │
  ├──→ 阶段1: module_rag 适配层（对接 RAGFlow SDK）
  │      │
  │      ├──→ 阶段2: 情境区 + 决策区
  │      │       │
  │      │       └──→ 阶段3: 反思区（核心创新）
  │      │               │
  │      │               └──→ 阶段4: 研究生成区
  │      │
  │      └──→ 阶段5: 前端页面（与后端同步）
  │
  └──→ 阶段6: 权限、菜单、测试收尾
```

---

## 阶段 0：部署 RAGFlow + 学习源码（2天）

**目标**：把 RAGFlow 跑起来，用一份社会工作 PDF 跑通整个 Pipeline，同时读源码理解原理。

### 0.1 部署 RAGFlow（Docker）（1天）

RAGFlow 的基础设施：

```
┌──────────────────────────────────────────────────┐
│               你的服务器（1台）                    │
│                                                    │
│  ┌──────────────────────────────────────────────┐ │
│  │  RuoYi-FastAPI 后端（已有）                    │ │
│  │  + PostgreSQL（已有）                          │ │
│  │  + Redis（已有）                               │ │
│  │  + module_rag（适配层，阶段1开发）              │ │
│  │  + module_learning（四区联动，阶段2-4开发）     │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
│  ┌──────────────────────────────────────────────┐ │
│  │  RAGFlow（Docker）                             │ │
│  │  ├── RAGFlow Server（端口 9380）               │ │
│  │  ├── Elasticsearch（向量存储+全文检索）         │ │
│  │  ├── MySQL（RAGFlow 元数据）                   │ │
│  │  ├── Redis（缓存，可复用现有的）                │ │
│  │  └── MinIO（文件存储）                         │ │
│  └──────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

部署步骤：

```bash
# 1. 克隆 RAGFlow
git clone https://github.com/infiniflow/ragflow.git
cd ragflow/docker

# 2. 配置 .env（设置端口、密码等）

# 3. 启动（需要 Docker >= 24.0，RAM >= 16GB）
docker compose -f docker-compose.yml up -d

# 4. 配置 LLM 和 Embedding 模型
#    登录 http://localhost:9380 后台
#    在"模型管理"中添加：智谱 Embedding-3（用于向量化）、DeepSeek-V3（用于对话）
```

> **系统要求**：CPU >= 4核，RAM >= 16GB，Disk >= 50GB。你的场景 5-10 人用，完全够。

### 0.2 用 RAGFlow 跑通第一个 Pipeline + 读源码（1天）

#### 实操：上传一份社会工作教材 PDF

1. 登录 RAGFlow 后台（http://localhost:9380）
2. 创建知识库（Dataset），选择分块策略：
   - `chunk_method="naive"`（通用分块）
   - `chunk_token_num=512`
3. 上传 PDF 文档
4. 触发解析 → 观察分块结果
5. 创建 Chat Assistant → 测试检索和对话
6. 用 API 测试检索：
   ```python
   from ragflow_sdk import RAGFlow
   rag = RAGFlow(api_key="your-key", base_url="http://localhost:9380")
   results = rag.retrieve(question="什么是赋权理论？", dataset_ids=["dataset_id"])
   for chunk in results:
       print(chunk.content, chunk.similarity)
   ```

#### 读源码：理解 RAGFlow 的 Pipeline

按这个顺序读，每层花 20-30 分钟：

| RAG 层 | RAGFlow 源码位置 | 你需要理解的问题 |
|--------|-----------------|----------------|
| 文档解析 | `deepdoc/` + `rag/app/naive.py` | PDF 文本是怎么提取的？为什么需要 layout recognition？ |
| 文本分块 | `rag/app/naive.py` 中的 chunk 逻辑 | chunk_token_num=512 意味着什么？分块边界怎么定？ |
| 向量化 | `rag/embd/` | Embedding API 是怎么调用的？向量维度为什么是 1024？ |
| 向量存储 | RAGFlow 用 Elasticsearch | 和 PgVector 有什么区别？为什么用 ES？ |
| 检索 | `rag/retrieval.py` | cosine similarity 怎么算？什么是混合检索（向量+BM25）？ |
| 对话 | Chat Assistant 模块 | 检索结果怎么拼进 Prompt？流式输出怎么实现？ |

> **不需要全部读懂**，重点是理解每一层的输入→输出→为什么这么处理。遇到不懂的就跳过，后面实际用到了再回来读。

### 阶段 0 完成标志

- [x] RAGFlow Docker 全部启动，后台能访问
- [x] 上传了一份社会工作 PDF，能看到分块结果
- [x] 用 SDK 测试了检索，能看到 similarity 分数和 chunk 内容
- [x] 创建了 Chat Assistant，能基于知识库回答问题
- [x] 粗略读了 `rag/app/naive.py` 和 `rag/retrieval.py` 的核心逻辑

---

## 阶段 1：module_rag 适配层（3天）

**目标**：在 RuoYi-FastAPI 中创建 `module_rag/` 模块，作为业务代码与 RAGFlow 之间的桥梁。四区联动只需调用 `module_rag` 的接口，不需要关心 RAGFlow 的细节。

### 架构：module_rag 的定位

```
四区联动（module_learning）
    │
    │  调用 module_rag 的接口
    ▼
module_rag（适配层）
    │
    │  内部调用 RAGFlow SDK
    ▼
RAGFlow Server（Docker）
    │
    ├── Elasticsearch（向量存储）
    ├── DeepDoc（文档解析）
    └── Embedding API（智谱）
```

`module_rag` 做两件事：
1. **管理本地元数据**：在 PostgreSQL 中记录知识库和文档的业务信息（名称、描述、所属部门、权限）
2. **封装 RAGFlow SDK 调用**：文档上传、解析、检索、对话等操作转发给 RAGFlow

### 1.1 创建骨架 + 安装依赖（0.5天）

#### 安装依赖

在 `requirements.txt` 中添加：
```
ragflow-sdk>=0.25.0
```

执行 `pip install ragflow-sdk`。

> 不再需要 pgvector、PyMuPDF、langchain、zhipuai 这些包了。RAGFlow 内部已经包含了这些能力。

#### 创建目录结构

```
module_rag/
├── __init__.py
├── config.py                        # RAGFlow 连接配置
├── controller/
│   ├── __init__.py
│   ├── knowledge_base_controller.py # 知识库管理（5个API）
│   ├── document_controller.py       # 文档管理（4个API）
│   └── retrieval_controller.py      # 检索 + RAG对话（2个API）
├── dao/
│   ├── __init__.py
│   └── knowledge_base_dao.py        # 本地元数据管理（仅1张表）
├── entity/
│   ├── __init__.py
│   ├── do/
│   │   └── knowledge_base_do.py     # 本地知识库元数据表 ORM
│   └── vo/
│       ├── knowledge_base_vo.py     # 知识库请求/响应模型
│       └── retrieval_vo.py          # 检索请求/响应模型
└── service/
    ├── __init__.py
    ├── ragflow_client.py            # RAGFlow SDK 封装（核心）
    ├── knowledge_base_service.py    # 知识库管理（本地表 + RAGFlow 同步）
    ├── document_service.py          # 文档管理（转发给 RAGFlow）
    └── retrieval_service.py         # 检索 + 对话（转发给 RAGFlow）
```

> 比之前的方案少了很多文件。不需要 chunk_dao、chunk_do、embedding_task_do 等，因为分块、向量化这些 RAGFlow 帮你做了。

### 1.2 本地数据表 + RAGFlow 连接配置（0.5天）

#### 本地只需 1 张表：rag_knowledge_base

```sql
CREATE TABLE rag_knowledge_base (
    kb_id            BIGSERIAL PRIMARY KEY,
    ragflow_dataset_id VARCHAR(64),       -- RAGFlow 中的 dataset ID（关联键）
    kb_name          VARCHAR(100) NOT NULL,
    kb_desc          VARCHAR(500),
    embedding_model  VARCHAR(100) DEFAULT 'BAAI/bge-large-zh-v1.5@BAAI',
    chunk_method     VARCHAR(30) DEFAULT 'naive',
    doc_count        INTEGER DEFAULT 0,
    status           CHAR(1) DEFAULT '0',
    dept_id          BIGINT,              -- 所属部门（数据隔离）
    user_id          BIGINT,              -- 创建者
    del_flag         CHAR(1) DEFAULT '0',
    create_by        VARCHAR(64) DEFAULT '',
    create_time      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_by        VARCHAR(64) DEFAULT '',
    update_time      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    remark           VARCHAR(500)
);
```

> **不再需要** rag_document、rag_chunk、rag_embedding_task 这三张表。文档信息、分块数据、向量化任务都由 RAGFlow 内部管理。

#### RAGFlow 连接配置

在 `.env.dev` 中添加：
```
RAGFLOW_API_KEY=your_ragflow_api_key
RAGFLOW_BASE_URL=http://localhost:9380
```

编写 `module_rag/config.py`：
```python
from config.env import DataBaseConfig

RAGFLOW_API_KEY = DataBaseConfig.RAGFLOW_API_KEY   # 在 config/env.py 中新增
RAGFLOW_BASE_URL = DataBaseConfig.RAGFLOW_BASE_URL
```

### 1.3 核心服务：ragflow_client.py（0.5天）

封装 RAGFlow SDK 的所有调用：

```python
from ragflow_sdk import RAGFlow

class RagflowClient:
    _instance = None

    @classmethod
    def get_client(cls) -> RAGFlow:
        if cls._instance is None:
            cls._instance = RAGFlow(
                api_key=RAGFLOW_API_KEY,
                base_url=RAGFLOW_BASE_URL,
            )
        return cls._instance

    @classmethod
    async def create_dataset(cls, name, chunk_method="naive", parser_config=None):
        client = cls.get_client()
        return client.create_dataset(
            name=name,
            chunk_method=chunk_method,
            parser_config=parser_config or {
                "chunk_token_num": 512,
                "delimiter": "\\n!?;。；！？",
                "layout_recognize": "DeepDOC",
                "auto_keywords": 3,
            }
        )

    @classmethod
    async def upload_and_parse(cls, dataset_id, file_path, display_name):
        client = cls.get_client()
        dataset = client.list_datasets(id=dataset_id)[0]
        docs = dataset.upload_documents([
            {"display_name": display_name, "blob": open(file_path, "rb").read()}
        ])
        dataset.async_parse_documents([doc.id for doc in docs])
        return docs

    @classmethod
    async def retrieve(cls, question, dataset_ids, top_k=5, similarity_threshold=0.2):
        client = cls.get_client()
        return client.retrieve(
            question=question,
            dataset_ids=dataset_ids,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
        )

    @classmethod
    async def create_chat_assistant(cls, name, dataset_ids, system_prompt):
        client = cls.get_client()
        return client.create_chat(
            name=name,
            dataset_ids=dataset_ids,
            prompt_config={
                "system": system_prompt,
                "empty_response": "抱歉，未在知识库中找到相关信息。",
                "quote": True,
            },
        )

    @classmethod
    async def chat(cls, chat_id, session_id, question, stream=True):
        client = cls.get_client()
        chat = client.list_chats(id=chat_id)[0]
        # 获取或创建 session
        sessions = chat.list_sessions()
        if session_id:
            session = [s for s in sessions if s.id == session_id]
            session = session[0] if session else chat.create_session()
        else:
            session = chat.create_session()
        return session.ask(question, stream=stream)
```

### 1.4 知识库管理 + 文档管理 Controller（0.5天）

#### knowledge_base_service.py

创建知识库时，同时做两件事：
1. 在本地 `rag_knowledge_base` 表创建记录
2. 调用 RAGFlow SDK 创建 dataset

```python
class KnowledgeBaseService:
    @classmethod
    async def create_kb(cls, db, kb_data, user_id):
        # 1. 调用 RAGFlow 创建 dataset
        dataset = await RagflowClient.create_dataset(
            name=kb_data.kb_name,
            chunk_method=kb_data.chunk_method,
        )
        # 2. 本地创建记录
        kb = RagKnowledgeBase(
            ragflow_dataset_id=dataset.id,
            kb_name=kb_data.kb_name,
            user_id=user_id,
            ...
        )
        db.add(kb)
        await db.commit()
        return kb
```

#### document_service.py

上传文档时：
1. 先用若依的 `UploadUtil` 存储文件
2. 调用 RAGFlow SDK 上传到对应 dataset 并触发解析
3. RAGFlow 内部自动完成：解析 → 分块 → 向量化（你不需要管）

#### Controller

参照 `module_ai/controller/` 的写法，实现知识库和文档的 API。

### 1.5 检索 + RAG 对话（1天）

#### retrieval_service.py

提供两个核心方法供四区联动调用：

```python
class RetrievalService:
    @classmethod
    async def search(cls, question: str, kb_ids: list[int], top_k=5):
        """纯检索：返回相关分块，供四区联动在拼 Prompt 时使用"""
        # 1. 查本地表，把 kb_ids 映射为 ragflow_dataset_ids
        dataset_ids = await cls._get_dataset_ids(kb_ids)
        # 2. 调 RAGFlow 检索
        chunks = await RagflowClient.retrieve(question, dataset_ids, top_k)
        return [{"content": c.content, "similarity": c.similarity} for c in chunks]

    @classmethod
    async def chat(cls, question: str, kb_ids: list[int],
                   system_prompt: str, stream=True):
        """RAG 对话：检索 + 拼 Prompt + 调 LLM，流式返回"""
        dataset_ids = await cls._get_dataset_ids(kb_ids)
        # 方案 A：用 RAGFlow 的 Chat Assistant（自带检索+对话）
        chat = await RagflowClient.create_chat_assistant(
            name=f"temp_{uuid4()}", dataset_ids=dataset_ids, system_prompt=system_prompt
        )
        return await RagflowClient.chat(chat.id, None, question, stream)
```

> **方案选择**：四区联动的 AI 对话有两种实现路径：
> - **路径 A（推荐前期用）**：直接用 RAGFlow 的 Chat Assistant，它自动处理检索+对话，你只需自定义 system_prompt
> - **路径 B（后期切）**：用 `retrieval_service.search()` 只拿检索结果，然后自己用 `AiChatService._build_agent()` 拼 Prompt 调 LLM。这样可以完全控制 Prompt，适合反思区的深度评估等复杂场景

#### retrieval_controller.py

实现 2 个 API：
- `POST /rag/retrieval/search` — 纯检索测试
- `POST /rag/retrieval/chat` — RAG 对话（SSE 流式）

**验证**：上传一份社会工作教材 PDF，用"什么是赋权理论？"测试。对比直接在 RAGFlow 后台测试的结果。

### 阶段 1 完成标志

- [x] `pip install ragflow-sdk` 成功，SDK 能连上 RAGFlow Server
- [x] 能通过 module_rag 的 API 创建知识库（本地表 + RAGFlow 同步）
- [x] 能通过 module_rag 的 API 上传文档并触发解析
- [x] 能通过 module_rag 的 API 检索知识库
- [x] 能通过 module_rag 的 API 进行 RAG 对话
- [x] RuoYi 项目能正常启动，不报错

---

## 阶段 2：情境区 + 决策区（4天）

**目标**：实现情境区和决策区。这是反思区的前序输入。

> 这部分与之前的方案基本一致，因为四区联动的业务逻辑 RAGFlow 帮不了你，必须自己写。区别在于 AI 对话部分：现在调用 `module_rag` 的检索接口，不再需要自己写向量检索 SQL。

### 2.1 创建 module_learning 骨架 + 学习记录状态机（1天）

#### 目录结构

```
module_learning/
├── __init__.py
├── controller/
│   ├── __init__.py
│   ├── task_controller.py           # 教学任务管理
│   ├── record_controller.py         # 学习记录管理
│   ├── scenario_controller.py       # 情境区
│   ├── decision_controller.py       # 决策区
│   └── reflection_controller.py     # 反思区（阶段3）
├── dao/
│   ├── __init__.py
│   ├── task_dao.py
│   ├── record_dao.py
│   ├── scenario_dao.py
│   ├── decision_dao.py
│   └── reflection_dao.py
├── entity/
│   ├── __init__.py
│   ├── do/
│   │   ├── __init__.py
│   │   ├── task_do.py
│   │   ├── record_do.py
│   │   ├── scenario_do.py
│   │   └── decision_do.py
│   └── vo/
│       ├── __init__.py
│       ├── task_vo.py
│       ├── record_vo.py
│       ├── scenario_vo.py
│       └── decision_vo.py
└── service/
    ├── __init__.py
    ├── task_service.py
    ├── record_service.py            # 学习记录状态机
    ├── scenario_service.py          # 情境区业务
    ├── decision_service.py          # 决策区业务
    └── ai_engine.py                 # AI 引擎
```

#### 建表

```sql
-- 教学任务表
CREATE TABLE edu_task (
    task_id      BIGSERIAL PRIMARY KEY,
    task_name    VARCHAR(200) NOT NULL,
    task_desc    TEXT,
    kb_ids       JSONB,                -- 关联的知识库ID列表（JSON数组）
    teacher_id   BIGINT NOT NULL REFERENCES sys_user(user_id),
    status       CHAR(1) DEFAULT '0',  -- 0未开始 1进行中 2已结束
    del_flag     CHAR(1) DEFAULT '0',
    create_by    VARCHAR(64) DEFAULT '',
    create_time  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_by    VARCHAR(64) DEFAULT '',
    update_time  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 学习记录主表（四区联动的核心状态）
CREATE TABLE edu_learning_record (
    record_id    BIGSERIAL PRIMARY KEY,
    task_id      BIGINT NOT NULL REFERENCES edu_task(task_id),
    student_id   BIGINT NOT NULL REFERENCES sys_user(user_id),
    current_zone VARCHAR(20) DEFAULT 'scenario',  -- scenario/decision/reflection/research
    status       CHAR(1) DEFAULT '0',
    del_flag     CHAR(1) DEFAULT '0',
    create_time  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 状态机逻辑

```python
ZONE_ORDER = ['scenario', 'decision', 'reflection', 'research']

class RecordService:
    @classmethod
    async def advance_zone(cls, db, record_id):
        record = await RecordDao.get_by_id(db, record_id)
        current_idx = ZONE_ORDER.index(record.current_zone)
        if current_idx < len(ZONE_ORDER) - 1:
            record.current_zone = ZONE_ORDER[current_idx + 1]
            await db.commit()
        return record
```

### 2.2 情境区后端（1.5天）

#### 建表

```sql
CREATE TABLE edu_scenario_data (
    scenario_id    BIGSERIAL PRIMARY KEY,
    record_id      BIGINT NOT NULL REFERENCES edu_learning_record(record_id),
    task_id        BIGINT NOT NULL,
    scenario_text  TEXT,
    ai_analysis    TEXT,
    status         CHAR(1) DEFAULT '0',
    del_flag       CHAR(1) DEFAULT '0',
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE edu_scenario_dialogue (
    dialogue_id    BIGSERIAL PRIMARY KEY,
    scenario_id    BIGINT NOT NULL REFERENCES edu_scenario_data(scenario_id),
    role           VARCHAR(20) NOT NULL,
    content        TEXT NOT NULL,
    token_count    INTEGER,
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 情境区 AI 对话

用 RAGFlow Chat Assistant 实现（路径 A）：

```python
class ScenarioService:
    @classmethod
    async def chat_with_scenario(cls, db, scenario_id, question, kb_ids):
        # 1. 检索相关社会工作知识
        retrieved = await RetrievalService.search(question, kb_ids, top_k=5)

        # 2. 创建专用的 Chat Assistant（或用已有的）
        system_prompt = """你是社会工作教育者，正在引导学生分析实践情境。
基于以下专业知识：{knowledge}
请帮助学生识别情境中的关键问题、相关理论和可能的介入方向。"""

        # 3. 调 RAG 对话
        response = await RetrievalService.chat(question, kb_ids, system_prompt)
        return response
```

### 2.3 决策区后端（1.5天）

#### 建表

```sql
CREATE TABLE edu_decision_data (
    decision_id      BIGSERIAL PRIMARY KEY,
    record_id        BIGINT NOT NULL REFERENCES edu_learning_record(record_id),
    scenario_id      BIGINT NOT NULL REFERENCES edu_scenario_data(scenario_id),
    student_choice   TEXT,
    student_reason   TEXT,
    ai_feedback      TEXT,
    status           CHAR(1) DEFAULT '0',
    del_flag         CHAR(1) DEFAULT '0',
    create_time      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE edu_decision_dialogue (
    dialogue_id    BIGSERIAL PRIMARY KEY,
    decision_id    BIGINT NOT NULL REFERENCES edu_decision_data(decision_id),
    role           VARCHAR(20) NOT NULL,
    content        TEXT NOT NULL,
    token_count    INTEGER,
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 决策区业务逻辑

- 学生做出行动选择并阐述理由
- AI 用 RAG 检索社会工作伦理规范，对决策给出反馈
- 提供"历史方案参照"：检索知识库中类似案例

### 阶段 2 完成标志

- [x] 教师能创建教学任务并关联知识库
- [x] 学生能进入任务，阅读情境，与 AI 对话
- [x] 学生能做出决策选择，AI 给出基于知识库的反馈
- [x] 学习记录状态机正确流转

---

## 阶段 3：反思区（5天）—— 核心创新模块

**目标**：实现反身性引导——AI 分析学生反思文本深度，通过三层递进提问推动反思深化。

> 这是整个系统最有技术含量的部分。RAGFlow 帮你做了知识检索，但**深度评估算法、三层递进提问策略、Prompt 设计**必须你自己来。

### 3.1 反思区数据表 + ORM（1天）

建表（参考 `architecture_reflexivity.md`）：

```sql
CREATE TABLE edu_reflection_data (
    reflection_id  BIGSERIAL PRIMARY KEY,
    record_id      BIGINT NOT NULL REFERENCES edu_learning_record(record_id),
    scenario_id    BIGINT NOT NULL REFERENCES edu_scenario_data(scenario_id),
    student_id     BIGINT NOT NULL REFERENCES sys_user(user_id),
    content        TEXT,
    depth_level    VARCHAR(20) DEFAULT 'descriptive',
    depth_score    DECIMAL(3,2) DEFAULT 0.00,
    linked_theories JSONB,
    version        INTEGER DEFAULT 1,
    status         CHAR(1) DEFAULT '0',
    del_flag       CHAR(1) DEFAULT '0',
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE edu_reflection_dialogue (
    dialogue_id    BIGSERIAL PRIMARY KEY,
    reflection_id  BIGINT NOT NULL REFERENCES edu_reflection_data(reflection_id),
    role           VARCHAR(20) NOT NULL,
    content        TEXT NOT NULL,
    question_level VARCHAR(20),
    depth_score_before DECIMAL(3,2),
    depth_score_after  DECIMAL(3,2),
    linked_theories JSONB,
    token_count    INTEGER,
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE edu_reflection_depth_history (
    history_id     BIGSERIAL PRIMARY KEY,
    reflection_id  BIGINT NOT NULL REFERENCES edu_reflection_data(reflection_id),
    depth_score    DECIMAL(3,2) NOT NULL,
    depth_level    VARCHAR(20) NOT NULL,
    trigger_type   VARCHAR(30),
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

编写对应的 ORM 模型和 VO 模型。

### 3.2 反思深度评估 + AI 提问引擎（2.5天）

#### 核心决策：用路径 B（自控 Prompt）

反思区的 AI 不能简单用 RAGFlow Chat Assistant，因为：
- 需要精确控制 Prompt（深度评估 + 三层递进提问）
- 需要解析 AI 返回的 JSON（depth_score + questions + theories）
- 需要结合情境区、决策区的历史数据

所以反思区用 `RetrievalService.search()` 拿检索结果，然后自己用 `AiChatService._build_agent()` 调 LLM。

#### 实现 ai_engine.py

```python
from module_rag.service.retrieval_service import RetrievalService

class ReflectionAiEngine:
    @classmethod
    async def evaluate_and_question(cls, db, reflection_text, scenario, decisions, history, kb_ids):
        # 1. RAG 检索：用反思文本检索相关理论
        retrieved = await RetrievalService.search(
            question=reflection_text,
            kb_ids=kb_ids,
            top_k=5,
        )
        retrieved_text = "\n".join([r["content"] for r in retrieved])

        # 2. 构建深度评估 + 提问的 Prompt
        system_prompt = REFLECTION_SYSTEM_PROMPT.format(
            scenario_summary=scenario,
            decision_summary=decisions,
            reflection_history=history,
            retrieved_knowledge=retrieved_text,
        )

        # 3. 调 LLM（复用若依的 AiChatService）
        agent = AiChatService._build_agent(
            model_config=model_config,
            temperature=0.3,
            system_prompt=system_prompt,
        )
        result = await agent.arun(reflection_text, stream=False)

        # 4. 解析返回的 JSON
        return json.loads(result.content)
        # 返回格式：{"depth_score": 0.65, "depth_level": "analytical",
        #           "questions": [...], "theories": [...]}
```

#### 深度评估的 Prompt 设计

参考 `architecture_reflexivity.md` 中的 REFLECTION_SYSTEM_PROMPT：
- **描述性（0.2-0.4）**：仅复述事件 → 生成分析性追问
- **分析性（0.5-0.7）**：分析原因互动 → 生成反身性追问
- **反身性（0.8-1.0）**：审视自身立场 → 生成理论连接追问

**这一步需要反复调 Prompt**：找 3-5 份真实的社工反思文本（让学姐提供），测试 AI 评估是否准确。

### 3.3 反思区 Service + Controller（1.5天）

#### 实现 reflection_service.py

- 创建反思记录（关联情境区和决策区的数据）
- 更新反思内容
- 调用 AI 引擎获取深度评估和追问
- 记录深度演变历史
- 确认反思完成，流转到研究区

#### 实现 reflection_controller.py

7 个 API：
- `POST /learning/reflection/create`
- `PUT /learning/reflection/update`
- `POST /learning/reflection/questions`
- `GET /learning/reflection/depth/{id}`
- `GET /learning/reflection/depth-history/{id}`
- `PUT /learning/reflection/confirm`
- `GET /learning/reflection/detail/{id}`

### 阶段 3 完成标志

- [x] 学生能撰写反思日志
- [x] AI 能自动评估反思深度（分数 + 等级）
- [x] AI 能根据深度层次生成 2-3 个递进追问
- [x] 反思深度演变历史有记录
- [x] RAG 检索能关联相关社会工作理论
- [x] 反思确认后能流转到研究区

---

## 阶段 4：研究生成区（3天）

**目标**：帮助学生梳理前三区材料，形成研究问题、论文框架、初稿段落。

### 4.1 研究区数据表 + 后端（2天）

#### 建表

```sql
CREATE TABLE edu_research_data (
    research_id      BIGSERIAL PRIMARY KEY,
    record_id        BIGINT NOT NULL REFERENCES edu_learning_record(record_id),
    reflection_id    BIGINT NOT NULL REFERENCES edu_reflection_data(reflection_id),
    research_question TEXT,
    outline           JSONB,
    draft_paragraphs  JSONB,
    ai_suggestions    JSONB,
    status            CHAR(1) DEFAULT '0',
    del_flag          CHAR(1) DEFAULT '0',
    create_time       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 核心业务逻辑

1. **研究问题生成**：AI 基于前三区所有材料 + RAG 检索，提炼研究问题
2. **论文框架生成**：基于研究问题 + RAG 检索的理论，生成论文大纲
3. **段落写作辅助**：AI 提供段落写作建议或学术语言润色
4. **每一步都调用** `RetrievalService.search()` 检索相关理论

### 4.2 研究区 Controller + 端到端测试（1天）

实现研究区 API，完成四区联动端到端流转测试。

### 阶段 4 完成标志

- [x] 学生能查看前三区材料汇总
- [x] AI 能生成研究问题、论文大纲、段落建议
- [x] 四区联动端到端完整

---

## 阶段 5：前端页面（8天）—— 与后端同步开发

> 前端可以在阶段 2 开始后同步推进。

### 5.1 RAG 知识库管理页面（2天）

- 知识库列表页（增删改查）
- 文档上传页（拖拽上传、显示解析状态）
- 检索测试页（输入问题，查看 RAGFlow 检索结果和 AI 回答）

### 5.2 情境区 + 决策区页面（2天）

- 情境区：案例展示 + AI 对话界面
- 决策区：选项展示 + 理由输入 + AI 反馈

### 5.3 反思区页面（2天）—— 前端核心

- 左侧：反思日志编辑器（富文本）
- 右侧上：AI 提问引导栏（按层次折叠）
- 右侧下：理论关联面板
- 顶部：反思深度指示器 + 深度演变曲线图（ECharts）

### 5.4 研究生成区页面（2天）

- 材料汇总面板 + 研究问题编辑 + 论文大纲 + 段落辅助

### 阶段 5 完成标志

- [x] 四区联动在页面上能完整走通
- [x] AI 对话流畅，流式输出正常

---

## 阶段 6：权限、菜单、收尾（2天）

### 6.1 权限与菜单配置（1天）

- 在 `sys_menu` 表中插入 RAG 管理和四区联动的菜单项
- 注册权限标识
- 配置角色权限矩阵（管理员/教师/学生）
- 验证 DataScope 数据隔离

### 6.2 测试 + 修 Bug（1天）

- 教师视角完整走通
- 学生视角完整走通
- 边界测试

### 阶段 6 完成标志

- [x] 角色权限隔离正确
- [x] 四区联动端到端完整可用

---

## 总工期汇总

| 阶段 | 内容 | 天数 | 累计 |
|------|------|------|------|
| 阶段 0 | 部署 RAGFlow + 学习源码 | 2天 | 2天 |
| 阶段 1 | module_rag 适配层 | 3天 | 5天 |
| 阶段 2 | 情境区 + 决策区 | 4天 | 9天 |
| 阶段 3 | 反思区（核心创新） | 5天 | 14天 |
| 阶段 4 | 研究生成区 | 3天 | 17天 |
| 阶段 5 | 前端页面 | 8天 | 25天 |
| 阶段 6 | 权限 + 测试收尾 | 2天 | 27天 |
| **总计** | | **27天（约5.5周）** | |

> 前端（阶段5）和后端阶段2-4同步，实际墙钟时间约 **4-5周**。比旧方案省了约 5 天（RAG 不用从零实现了）。

---

## 明天开始的第一件事

**阶段 0 的 0.1**：部署 RAGFlow。

具体操作：
1. 确保服务器有 Docker >= 24.0，RAM >= 16GB
2. `git clone https://github.com/infiniflow/ragflow.git && cd ragflow/docker`
3. 修改 `.env` 配置（端口、密码等）
4. `docker compose up -d`
5. 访问 `http://localhost:9380`，注册账号
6. 在"模型管理"中配置智谱 Embedding 和 DeepSeek 对话模型

部署成功后，上传一份社会工作 PDF 跑通解析→分块→检索→对话的全流程。然后读 `rag/app/naive.py` 和 `rag/retrieval.py` 的源码。
