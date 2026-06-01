# RuoYiFast RAG 模块架构方案

| 项目信息 | |
|---|---|
| 文档版本 | v1.0 |
| 编写日期 | 2026年5月28日 |
| 基础框架 | RuoYi-Vue3-FastAPI |
| 模块定位 | 四区联动之知识库基础设施（RAG） |

---

## 一、项目现状总结

| 已有 | 缺失 |
|------|------|
| FastAPI + SQLAlchemy(async) + Redis 框架完整 | 无向量数据库支持 |
| `module_ai/` 对话模块（基于 agno 框架，SSE 流式） | 无文档解析/分块 Pipeline |
| 教育角色体系 ORM（Student/Teacher/Audit） | 无知识库管理模块 |
| JWT 认证 + RBAC 权限 + 数据隔离（DataScope） | 无 RAG 检索服务 |
| 文件上传基础设施（`UploadUtil` + `UploadConfig`） | 四区联动代码为零 |
| 反身性文档（`architecture_reflexivity.md`）定义了完整需求 | |

**结论：RAG 知识库是从零开始建设，但框架基础设施（认证、权限、AI调用、文件上传）都已就绪。**

---

## 二、RAG 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                       前端 (Vue3)                                │
│  知识库管理页 → 文件上传组件 → 文档列表 → 向量化进度 → 检索测试  │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/SSE
┌────────────────────────────▼────────────────────────────────────┐
│                   module_rag (新建模块)                          │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌───────────────┐  │
│  │controller │  │  service │  │   dao     │  │   entity      │  │
│  │  7个API   │  │  5个服务  │  │  4个DAO   │  │ do/vo 各6个   │  │
│  └──────────┘  └──────────┘  └───────────┘  └───────────────┘  │
│                                                                  │
│  文档上传 → 解析 → 分块 → Embedding → 存入 PgVector             │
│  用户提问 → 向量检索 → 重排序 → 拼接 Prompt → 调用 LLM          │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                     │
   ┌────▼────┐        ┌─────▼─────┐        ┌──────▼──────┐
   │PostgreSQL│        │  Redis    │        │  LLM API    │
   │+PgVector │        │  缓存/锁  │        │(复用AiUtil) │
   └─────────┘        └───────────┘        └─────────────┘
```

---

## 三、module_rag 目录结构（直接照做）

```
module_rag/
├── __init__.py
├── controller/
│   ├── __init__.py
│   ├── knowledge_base_controller.py   # 知识库管理（增删改查）
│   ├── document_controller.py         # 文档管理（上传、列表、删除）
│   ├── chunk_controller.py            # 文档分块管理（查看、手动调整）
│   └── retrieval_controller.py        # 检索测试 + RAG 对话
├── dao/
│   ├── __init__.py
│   ├── knowledge_base_dao.py
│   ├── document_dao.py
│   ├── chunk_dao.py
│   └── retrieval_dao.py
├── entity/
│   ├── __init__.py
│   ├── do/
│   │   ├── __init__.py
│   │   ├── knowledge_base_do.py       # rag_knowledge_base 表 ORM
│   │   ├── document_do.py             # rag_document 表 ORM
│   │   ├── chunk_do.py                # rag_chunk 表 ORM（含向量字段）
│   │   └── embedding_task_do.py       # rag_embedding_task 异步任务表
│   └── vo/
│       ├── __init__.py
│       ├── knowledge_base_vo.py       # 知识库 Pydantic 模型
│       ├── document_vo.py             # 文档 Pydantic 模型
│       ├── chunk_vo.py                # 分块 Pydantic 模型
│       └── retrieval_vo.py            # 检索请求/响应模型
└── service/
    ├── __init__.py
    ├── knowledge_base_service.py      # 知识库 CRUD
    ├── document_service.py            # 文档上传 + 解析
    ├── chunk_service.py               # 分块 + 向量化
    ├── embedding_service.py           # Embedding 调用封装
    └── retrieval_service.py           # 向量检索 + RAG 对话
```

---

## 四、数据库表设计（4张核心表 + 1张任务表）

### 4.1 `rag_knowledge_base` — 知识库表

```sql
CREATE TABLE rag_knowledge_base (
    kb_id          BIGSERIAL PRIMARY KEY,
    kb_name        VARCHAR(100) NOT NULL,           -- 知识库名称
    kb_desc        VARCHAR(500),                    -- 知识库描述
    embedding_model VARCHAR(100) DEFAULT 'embedding-3', -- 使用的 Embedding 模型
    chunk_strategy  VARCHAR(30) DEFAULT 'fixed',    -- 分块策略: fixed/semantic
    chunk_size      INTEGER DEFAULT 500,            -- 分块大小（字符数）
    chunk_overlap   INTEGER DEFAULT 50,             -- 分块重叠（字符数）
    doc_count       INTEGER DEFAULT 0,              -- 文档数量（冗余统计）
    status         CHAR(1) DEFAULT '0',             -- 0正常 1停用
    dept_id        BIGINT,                          -- 所属部门（数据隔离）
    user_id        BIGINT,                          -- 创建者用户ID
    del_flag       CHAR(1) DEFAULT '0',             -- 删除标志
    create_by      VARCHAR(64) DEFAULT '',
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_by      VARCHAR(64) DEFAULT '',
    update_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    remark         VARCHAR(500)
);
COMMENT ON TABLE rag_knowledge_base IS 'RAG知识库表';
```

### 4.2 `rag_document` — 文档表

```sql
CREATE TABLE rag_document (
    doc_id         BIGSERIAL PRIMARY KEY,
    kb_id          BIGINT NOT NULL REFERENCES rag_knowledge_base(kb_id),
    doc_name       VARCHAR(255) NOT NULL,           -- 原始文件名
    file_path      VARCHAR(500) NOT NULL,           -- 存储路径
    file_type      VARCHAR(20),                     -- pdf/docx/txt/md
    file_size      BIGINT DEFAULT 0,                -- 文件大小(bytes)
    chunk_count    INTEGER DEFAULT 0,               -- 分块数（冗余统计）
    parse_status   CHAR(1) DEFAULT '0',             -- 0待解析 1解析中 2已完成 3失败
    embed_status   CHAR(1) DEFAULT '0',             -- 0待向量化 1向量化中 2已完成 3失败
    error_msg      VARCHAR(500),                    -- 错误信息
    user_id        BIGINT,                          -- 上传者用户ID
    dept_id        BIGINT,                          -- 所属部门
    del_flag       CHAR(1) DEFAULT '0',
    create_by      VARCHAR(64) DEFAULT '',
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_by      VARCHAR(64) DEFAULT '',
    update_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE rag_document IS 'RAG文档表';
```

### 4.3 `rag_chunk` — 文档分块表（含向量）

```sql
CREATE TABLE rag_chunk (
    chunk_id       BIGSERIAL PRIMARY KEY,
    doc_id         BIGINT NOT NULL REFERENCES rag_document(doc_id),
    kb_id          BIGINT NOT NULL REFERENCES rag_knowledge_base(kb_id),
    chunk_index    INTEGER NOT NULL,                -- 分块序号（从0开始）
    content        TEXT NOT NULL,                   -- 分块文本内容
    token_count    INTEGER DEFAULT 0,               -- Token 数
    embedding      vector(1024),                    -- pgvector 向量字段（1024维，匹配智谱embedding-3）
    metadata       JSONB,                           -- 元数据（页码、标题等）
    del_flag       CHAR(1) DEFAULT '0',
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE rag_chunk IS 'RAG文档分块表';

-- 向量检索必须的索引
CREATE INDEX idx_rag_chunk_embedding ON rag_chunk USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_rag_chunk_kb_id ON rag_chunk(kb_id);
CREATE INDEX idx_rag_chunk_doc_id ON rag_chunk(doc_id);
```

### 4.4 `rag_embedding_task` — 异步向量化任务表

```sql
CREATE TABLE rag_embedding_task (
    task_id        BIGSERIAL PRIMARY KEY,
    doc_id         BIGINT NOT NULL REFERENCES rag_document(doc_id),
    task_type      VARCHAR(30) DEFAULT 'embed',     -- embed/re_embed/delete
    total_chunks   INTEGER DEFAULT 0,
    done_chunks    INTEGER DEFAULT 0,
    status         CHAR(1) DEFAULT '0',             -- 0待执行 1执行中 2已完成 3失败
    error_msg      VARCHAR(500),
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE rag_embedding_task IS 'RAG向量化任务表';
```

---

## 五、核心流程设计

### 5.1 文件上传 → 解析 → 分块 → 向量化 Pipeline

```
用户上传文件（PDF/DOCX/TXT/MD）
        │
        ▼
  ① 文件存储到 vf_admin/upload_path/rag/
        │
        ▼
  ② 创建 rag_document 记录（parse_status=0）
        │
        ▼
  ③ 异步解析文档（PyMuPDF/pdfplumber 处理PDF，python-docx 处理DOCX）
     → 提取纯文本，按页/段落保留 metadata
        │
        ▼
  ④ 按 chunk_size 分块（默认500字符，重叠50字符）
     → 创建 rag_chunk 记录（embedding 暂为空）
        │
        ▼
  ⑤ 调用 Embedding API（智谱 embedding-3，1024维）
     → 批量向量化，写入 rag_chunk.embedding
     → 更新 doc 的 embed_status=2
```

### 5.2 RAG 检索流程

```
用户输入问题
        │
        ▼
  ① 问题文本 → Embedding API → 得到问题向量
        │
        ▼
  ② PgVector 向量检索（cosine similarity, top_k=5）
     → WHERE kb_id IN (用户有权访问的知识库)
        │
        ▼
  ③ 简单重排序（可选：用 LLM 做 rerank 或按 metadata 加权）
        │
        ▼
  ④ 拼接 Prompt:
     system = "你是社会工作教育助手，基于以下知识回答问题：\n{retrieved_chunks}"
     user = 用户问题
        │
        ▼
  ⑤ 调用 LLM（复用 AiUtil.get_model_from_factory）
     → 流式返回答案
```

### 5.3 四区联动中的 RAG 调用点

根据反身性文档（`architecture_reflexivity.md`），RAG 在以下场景被调用：

| 四区 | RAG 调用场景 | 说明 |
|------|-------------|------|
| **情境区** | 情境知识增强 | 上传案例材料到知识库，AI 分析情境时可引用 |
| **决策区** | 伦理准则检索 | 决策时检索社会工作伦理规范 |
| **反思区** | 理论关联推荐 | 学生写反思时，用反思文本检索相关理论 |
| **研究生成区** | 文献支撑 | 生成研究内容时检索知识库中的理论依据 |

---

## 六、接口设计（14个 API）

### 6.1 知识库管理（5个）

| 方法 | 路径 | 说明 | 权限标识 |
|------|------|------|---------|
| GET | `/rag/kb/list` | 知识库分页列表 | `rag:kb:list` |
| POST | `/rag/kb` | 创建知识库 | `rag:kb:add` |
| PUT | `/rag/kb` | 编辑知识库 | `rag:kb:edit` |
| DELETE | `/rag/kb/{kb_ids}` | 删除知识库 | `rag:kb:remove` |
| GET | `/rag/kb/{kb_id}` | 知识库详情 | `rag:kb:query` |

### 6.2 文档管理（4个）

| 方法 | 路径 | 说明 | 权限标识 |
|------|------|------|---------|
| GET | `/rag/doc/list` | 文档分页列表 | `rag:doc:list` |
| POST | `/rag/doc/upload` | 上传文档 | `rag:doc:upload` |
| DELETE | `/rag/doc/{doc_ids}` | 删除文档 | `rag:doc:remove` |
| POST | `/rag/doc/reparse/{doc_id}` | 重新解析 | `rag:doc:reparse` |

### 6.3 分块管理（3个）

| 方法 | 路径 | 说明 | 权限标识 |
|------|------|------|---------|
| GET | `/rag/chunk/list` | 分块列表（按文档ID） | `rag:chunk:list` |
| PUT | `/rag/chunk` | 编辑分块内容 | `rag:chunk:edit` |
| DELETE | `/rag/chunk/{chunk_ids}` | 删除分块 | `rag:chunk:remove` |

### 6.4 检索与对话（2个）

| 方法 | 路径 | 说明 | 权限标识 |
|------|------|------|---------|
| POST | `/rag/retrieval/search` | 检索测试（返回 top_k 分块） | `rag:retrieval:search` |
| POST | `/rag/retrieval/chat` | RAG 对话（检索+LLM流式） | `rag:retrieval:chat` |

---

## 七、权限与数据隔离设计

### 7.1 权限标识（注册到 sys_menu）

```
rag:kb:list      — 查看知识库列表
rag:kb:query     — 查看知识库详情
rag:kb:add       — 创建知识库
rag:kb:edit      — 编辑知识库
rag:kb:remove    — 删除知识库
rag:doc:list     — 查看文档列表
rag:doc:upload   — 上传文档
rag:doc:remove   — 删除文档
rag:doc:reparse  — 重新解析
rag:chunk:list   — 查看分块列表
rag:chunk:edit   — 编辑分块
rag:chunk:remove — 删除分块
rag:retrieval:search — 检索测试
rag:retrieval:chat   — RAG对话
```

### 7.2 数据隔离（复用 DataScope 机制）

```
知识库表有 dept_id 和 user_id 字段
→ 直接复用 DataScopeDependency(RagKnowledgeBase) 做部门级隔离

检索时：
→ WHERE kb_id IN (用户有权访问的知识库ID列表)
→ 教师只能检索自己部门的知识库
→ 学生只能检索被分配的知识库
→ 管理员看全部
```

### 7.3 角色权限矩阵

| 操作 | 管理员 | 教师 | 学生 |
|------|--------|------|------|
| 创建知识库 | 全部 | 自己部门 | 无 |
| 上传文档 | 全部 | 自己部门 | 无 |
| 检索/对话 | 全部 | 自己部门 | 被分配的知识库 |
| 管理分块 | 全部 | 自己部门 | 无 |

---

## 八、核心代码模式（照着现有 module_ai 写）

### 8.1 Controller 模式（直接复用框架装饰器）

```python
# module_rag/controller/knowledge_base_controller.py
from common.router import APIRouterPro
from common.aspect.pre_auth import PreAuthDependency, CurrentUserDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.data_scope import DataScopeDependency
from common.annotation.cache_annotation import ApiCache, ApiCacheEvict
from common.annotation.log_annotation import Log
from common.enums import BusinessType

rag_kb_controller = APIRouterPro(
    prefix='/rag/kb',
    order_num=20,
    tags=['RAG管理-知识库'],
    dependencies=[PreAuthDependency()],
)

@rag_kb_controller.get(
    '/list',
    summary='知识库列表',
    dependencies=[UserInterfaceAuthDependency('rag:kb:list')],
)
@ApiCache(namespace='rag:kb:list')
async def get_kb_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(RagKnowledgeBase)],
) -> Response:
    result = await KnowledgeBaseService.get_kb_list(query_db, data_scope_sql)
    return ResponseUtil.success(model_content=result)
```

### 8.2 Embedding Service（调用智谱 API）

```python
# module_rag/service/embedding_service.py
from openai import AsyncOpenAI  # 智谱兼容 OpenAI 接口

class EmbeddingService:
    _client = None

    @classmethod
    def get_client(cls) -> AsyncOpenAI:
        if cls._client is None:
            cls._client = AsyncOpenAI(
                api_key="your-zhipu-api-key",
                base_url="https://open.bigmodel.cn/api/paas/v4",
            )
        return cls._client

    @classmethod
    async def embed_texts(cls, texts: list[str]) -> list[list[float]]:
        """批量文本向量化"""
        client = cls.get_client()
        response = await client.embeddings.create(
            model="embedding-3",
            input=texts,
        )
        return [item.embedding for item in response.data]
```

### 8.3 向量检索 SQL

```python
# module_rag/service/retrieval_service.py
from sqlalchemy import text

class RetrievalService:
    @classmethod
    async def search(
        cls,
        db: AsyncSession,
        query_embedding: list[float],
        kb_ids: list[int],
        top_k: int = 5,
    ) -> list[dict]:
        """PgVector 向量检索"""
        embedding_str = str(query_embedding)
        sql = text("""
            SELECT chunk_id, doc_id, kb_id, content, metadata,
                   1 - (embedding <=> :query_vec::vector) AS similarity
            FROM rag_chunk
            WHERE kb_id = ANY(:kb_ids)
              AND del_flag = '0'
            ORDER BY embedding <=> :query_vec::vector
            LIMIT :top_k
        """)
        result = await db.execute(sql, {
            "query_vec": embedding_str,
            "kb_ids": kb_ids,
            "top_k": top_k,
        })
        return [dict(row._mapping) for row in result.fetchall()]
```

---

## 九、开发任务拆解（按执行顺序）

### 阶段 0：基础设施（2天）

| # | 任务 | 涉及文件 | 说明 |
|---|------|----------|------|
| 0.1 | 添加依赖到 requirements-pg.txt | `requirements-pg.txt` | 添加 `pgvector`, `langchain-text-splitters`, `PyMuPDF`, `python-docx`, `zhipuai` |
| 0.2 | PostgreSQL 启用 PgVector 扩展 | SQL脚本 | `CREATE EXTENSION IF NOT EXISTS vector;` |
| 0.3 | 创建 `module_rag/` 骨架目录 | `module_rag/` | 按第三节的目录结构创建所有 `__init__.py` |
| 0.4 | 配置 Embedding API Key | `config/env.py` 或 `.env.test` | 新增 `ZHIPU_API_KEY` 配置项 |

### 阶段 1：数据表 + ORM（2天）

| # | 任务 | 涉及文件 |
|---|------|----------|
| 1.1 | 执行 SQL 建表（4张表 + 索引） | `sql/rag_tables.sql` |
| 1.2 | 编写 ORM 模型（`_do.py` 四个文件） | `module_rag/entity/do/` |
| 1.3 | 编写 Pydantic VO 模型（`_vo.py` 四个文件） | `module_rag/entity/vo/` |
| 1.4 | 编写 DAO 层（CRUD 操作） | `module_rag/dao/` |

### 阶段 2：文档解析 + 分块 + 向量化（4天）

| # | 任务 | 涉及文件 |
|---|------|----------|
| 2.1 | 文档解析服务（PDF/DOCX/TXT/MD → 纯文本） | `module_rag/service/document_service.py` |
| 2.2 | 文本分块服务（固定长度分块 + 语义分块） | `module_rag/service/chunk_service.py` |
| 2.3 | Embedding 服务（封装智谱 API 调用） | `module_rag/service/embedding_service.py` |
| 2.4 | 文档上传 Controller（上传 → 异步解析 → 分块 → 向量化） | `module_rag/controller/document_controller.py` |
| 2.5 | 向量化任务进度查询接口 | `module_rag/controller/document_controller.py` |

### 阶段 3：知识库管理（2天）

| # | 任务 | 涉及文件 |
|---|------|----------|
| 3.1 | 知识库 CRUD Service | `module_rag/service/knowledge_base_service.py` |
| 3.2 | 知识库 CRUD Controller | `module_rag/controller/knowledge_base_controller.py` |
| 3.3 | 分块管理接口（查看/编辑/删除） | `module_rag/controller/chunk_controller.py` |

### 阶段 4：RAG 检索 + 对话（3天）

| # | 任务 | 涉及文件 |
|---|------|----------|
| 4.1 | 向量检索服务（PgVector cosine search） | `module_rag/service/retrieval_service.py` |
| 4.2 | RAG 对话服务（检索 → 拼接 Prompt → 调 LLM） | `module_rag/service/retrieval_service.py` |
| 4.3 | 检索测试接口 | `module_rag/controller/retrieval_controller.py` |
| 4.4 | RAG 对话接口（SSE 流式） | `module_rag/controller/retrieval_controller.py` |

### 阶段 5：权限 + 数据隔离 + 菜单（1天）

| # | 任务 | 涉及文件 |
|---|------|----------|
| 5.1 | 在 sys_menu 表中插入 RAG 菜单和按钮权限 | SQL 脚本 |
| 5.2 | 在 `ApiNamespace` 中添加 RAG 命名空间 | `common/constant.py` |
| 5.3 | 给角色分配 RAG 权限 | SQL 脚本 |

---

## 十、合规、隐私、安全（教育场景）

| 关注点 | 措施 |
|--------|------|
| **学生反思文本隐私** | 调用 LLM 前脱敏姓名/学号，AI 输出标注"AI 生成内容" |
| **知识库内容安全** | 上传文档时做敏感词扫描，防止上传涉密/不当内容 |
| **数据隔离** | 教师只看自己部门知识库，学生只能检索被分配的知识库（DataScope） |
| **个人信息保护法** | 注册时明示数据用途，提供数据导出和删除接口 |
| **心理危机预警** | 学生反思文本中扫描危机关键词（自杀/自残），自动通知教师 |
| **API Key 安全** | 知识库的 Embedding Key 复用 `AiModels` 表的加密存储机制（`CryptoUtil`） |
| **文件上传安全** | 复用 `UploadUtil.check_file_extension()` 白名单校验 |
| **审计日志** | 所有 RAG 操作加 `@Log` 注解，操作记录进 sys_oper_log |

---

## 十一、技术选型汇总

| 用途 | 选型 | 理由 |
|------|------|------|
| 向量数据库 | PgVector（PostgreSQL 扩展） | 零额外部署，项目已用 PostgreSQL |
| Embedding 模型 | 智谱 Embedding-3（1024维） | 中文效果好，API 稳定 |
| 文档解析 PDF | PyMuPDF (fitz) | 免费、速度快、支持表格提取 |
| 文档解析 DOCX | python-docx | 轻量、成熟 |
| 文本分块 | langchain TextSplitter | 支持固定/语义分块，可配置 |
| LLM 调用 | 复用 `AiUtil.get_model_from_factory()` | 项目已有 agno 集成，直接复用 |
| 前端 | Vue3 + Element Plus | 复用 RuoYi 前端 |

---

## 十二、与反身性模块的衔接

反身性文档（`architecture_reflexivity.md`）中定义了反思区的 RAG 调用：

```python
# 反思区的 ai_engine.py 调用 RAG 检索的方式
from module_rag.service.retrieval_service import RetrievalService

# 在反思区 AI 引擎中：
retrieved = await RetrievalService.search(
    db=query_db,
    query_text=reflection_text,    # 学生的反思文本作为检索 query
    kb_ids=[1, 2],                  # 社会工作理论知识库
    top_k=5,
)
# retrieved 就是相关理论片段，拼入 system_prompt 的 {retrieved_knowledge} 位置
```

这样 `module_learning`（反思区）只需 import `module_rag` 的 `RetrievalService`，不需要关心向量化实现细节。

---

## 十三、总预计工期

| 阶段 | 天数 |
|------|------|
| 阶段 0：基础设施 | 2天 |
| 阶段 1：数据表 + ORM | 2天 |
| 阶段 2：文档解析 + 分块 + 向量化 | 4天 |
| 阶段 3：知识库管理 | 2天 |
| 阶段 4：RAG 检索 + 对话 | 3天 |
| 阶段 5：权限 + 菜单 | 1天 |
| **总计** | **14天** |

完成后，四区联动的情境区、决策区、反思区、研究生成区都可以直接调用 `RetrievalService.search()` 获取知识库支撑。
