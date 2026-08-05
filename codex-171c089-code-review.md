# Codex `171c089` 代码审查报告（合并前 Review）

> 对照基线：`cefeebc`（新增总结）→ `171c089`（codex 重写）
> 审查人：Claude（含 2 处 agent 误报的剔除）
> 用途：决定 `feature/kb-permission-scope` 能否合并到 master

---

## TL;DR

- **20 个 `.py` 文件，+1279/-471**。codex 干了三件事：① 知识库权限按「机制/规则」切分；② 重写 RAG 检索链路（双路召回→RRF→可插拔精排→阈值）；③ 重写解析/切块/嵌入链路。
- **方向是对的**，且白送两个严重历史 bug 修复（docx 只返回首块、embedding 向量错位）。
- **没有数据库 schema 变更**（DO 只删未用 import），不需要迁移脚本。
- **合并前必须确认 4 个风险点**（见文末「风险清单」），其中 `SET LOCAL` 和关键词召回确定性两个会**静默降低检索质量**。

> 自行看完整 diff：`git diff cefeebc..171c089 -- <文件路径>`

---

## 第一部分 · 知识库权限切分（本分支主题）

### 1.1 `module_rag/service/kb_scope_policy.py` 【重写 -125/+70】把四级权限下沉为「产品无关默认」

**改了什么**：原来这个文件直接实现了学校/班级/师生四级权限（教育领域规则混在 RAG 模块）。codex 把它简化成 `DefaultKbScopePolicy`——只认 public + 本人 personal，作为 RAG 模块独立存在时的安全兜底。

**BEFORE**（cefeebc，节选核心逻辑）：
```python
class KbScopePolicy(ScopePolicy[RagKnowledgeBase]):
    async def build_principal(self, db, current_user) -> KbPrincipal:
        # admin / student / teacher 三分支，查 EduDao 加载 school_id/class_id/
        # taught_class_ids/owned_student_ids/school_dept_ids 等教育身份字段
        ...

    def visible_filter(self, p, model):
        # SQL 级：PUBLIC ∪ (SCHOOL & school_id) ∪ (CLASS & class_id/school_dept_ids)
        #         ∪ (PERSONAL & owner_user_id)
        ...

    def can_access(self, p, kb):
        # 四级纯 Python 判定
        ...

    def validate_create(self, p, kb_scope, scope_dept_id):
        # 教师：仅可建 SCHOOL(本校)/CLASS(任课班)；学生：仅 PERSONAL
        ...

ScopeRegistry.register('rag.knowledge_base', KbScopePolicy())  # 模块导入即注册
```

**AFTER**（171c089）：
```python
class DefaultKbScopePolicy(ScopePolicy[RagKnowledgeBase]):
    """默认仅支持公共库和本人个人库，适合作为独立 RAG 模块的安全兜底。"""

    async def build_principal(self, db, current_user) -> KbPrincipal:
        # 不再查任何教育表；只识别 admin / 普通 user
        return KbPrincipal(user_id=..., is_admin=..., role=..., role_keys=...)

    def visible_filter(self, principal, model):
        return or_(model.kb_scope == KbScope.PUBLIC,
                   and_(model.kb_scope == KbScope.PERSONAL,
                        model.owner_user_id == principal.user_id))

    def can_access(self, principal, kb):
        return scope == KbScope.PUBLIC or (PERSONAL and owner 是本人)

    def validate_create(self, principal, kb_scope, scope_dept_id):
        if not is_admin and kb_scope != PERSONAL:
            raise PermissionException('当前产品未注册该知识库作用域的创建策略')

ScopeRegistry.register('rag.knowledge_base', DefaultKbScopePolicy())
```

**🔍 Review 关注点**：
- ✅ 这是 [[framework-mechanism-vs-policy-split]] 的落地：机制（Principal/ScopePolicy/ScopeRegistry）留 common，教育规则搬到 module_learning。RAG 模块自包含、可独立复用。
- ⚠️ 注册从「导入即注册」改成默认兜底，教育规则要靠 module_learning 覆盖——见 1.3 的注册顺序风险。

---

### 1.2 `module_learning/service/kb_scope_policy.py` 【新增 +169】教育领域四级规则

**改了什么**：把 1.1 删掉的四级权限逻辑搬到 module_learning，类名 `LearningKbScopePolicy`，通过 `register_learning_kb_scope_policy()` 显式覆盖 RAG 默认策略。逻辑与原 `KbScopePolicy` 基本一致（学校/班级/师生/个人四级），但 `LearningKbPrincipal` 继承自 `KbPrincipal`。

**AFTER**（全文核心，before 不存在）：
```python
class LearningKbPrincipal(KbPrincipal):
    school_id / class_id / taught_class_ids / owned_student_ids / school_dept_ids  # 教育身份扩展

class LearningKbScopePolicy(ScopePolicy[RagKnowledgeBase]):
    async def build_principal(...):  # admin/student/teacher 三分支，查 EduDao
    def visible_filter(...):         # 四级 SQL 过滤
    def can_access(...):             # 四级 Python 判定
    def validate_create(...):        # 教师仅 SCHOOL/CLASS，学生仅 PERSONAL

def register_learning_kb_scope_policy():
    ScopeRegistry.register('rag.knowledge_base', LearningKbScopePolicy())  # 覆盖默认
```

**🔍 Review 关注点**：
- ✅ 逻辑与原 `KbScopePolicy` 等价，规则没有丢失。
- ⚠️ `can_access` 里学生分支同时把 CLASS 和 PERSONAL 两个条件 append（[L112-114](ruoyi-fastapi-backend/module_learning/service/kb_scope_policy.py#L112)），原代码也是这样，语义正确（学生可见本班库 + 自己的个人库）。

---

### 1.3 `module_learning/hooks.py` 【+5】注册入口

**AFTER**：
```python
from module_learning.service.kb_scope_policy import register_learning_kb_scope_policy
# 模块发现阶段注册反身性产品的知识库作用域策略。
register_learning_kb_scope_policy()
```

**🔍 Review 关注点（中等风险）· 注册依赖隐式 import 顺序**：
- 我推演了实际加载链：`server.py` 启动时 `LifecycleHooks.discover_and_load()`（扫描 `module_*/hooks.py`）**先于** `auto_register_routers`。
- `hooks.py` 导入 `module_learning.service.kb_scope_policy` 时，其顶部 `from module_rag.service.kb_scope_policy import KbPrincipal` 会**先**触发 `DefaultKbScopePolicy` 注册，紧接着 `register_learning_kb_scope_policy()` 用 `Learning` **覆盖**。之后路由阶段 rag 模块已缓存，不再重跑顶层注册。**最终 Learning 胜出** ✅。
- 但这是隐式依赖。**非 server 启动场景**（celery worker、独立脚本、部分单测）若不走 `discover_and_load`，会静默回退到 `DefaultKbScopePolicy` → 学校/班级可见性全部失效。codex 在测试里也显式调了 register，说明它知道这层依赖。**建议**：给 `ScopeRegistry.register` 加优先级，或让 RAG 侧延迟解析，去掉顺序耦合。

---

### 1.2b 四个 learning service 【检索调用适配】统一改用 RagContextBuilder

`decision_service.py` / `reflection_service.py` / `review_service.py` / `scenario_service.py` 的改动**完全同构**：把原来「手写 embed + hybrid_search + 手动拼 chunks」换成 `RagContextBuilder.build(...)`。

**BEFORE**（以 decision 为例）：
```python
from module_rag.service.embedding_service import EmbeddingService
from module_rag.service.retrieval_service import RetrievalService
query_embedding = await EmbeddingService.embed_single(query_text)
chunks = await RetrievalService.hybrid_search(db=db, query_text=..., query_embedding=..., kb_ids=..., top_k=5)
return '\n\n'.join([f'【参考{i+1}】{c["content"]}' for i, c in enumerate(chunks)])
```

**AFTER**：
```python
from module_rag.service.context_builder import RagContextBuilder
context = await RagContextBuilder.build(db=db, query_text=..., kb_ids=..., top_k=5, max_chars_per_chunk=500)
return context.text or '（未检索到足够相关的伦理知识）'
```

**🔍 Review 关注点**：
- ✅ 消除了 4 处重复的 embed+search+拼装样板，统一到 context_builder，合理。
- ⚠️ **输出格式变了**（喂给 LLM 的文本）：原来 `【参考i】内容`，现在 `[n] 来源：doc.md · 第x页 · 标题路径\n内容` + 一句引用指令。格式变化可能影响生成效果，需业务回归。
- ⚠️ `decision_service` 原来**不截断**伦理内容（全量），现 `max_chars_per_chunk=500`，长内容可能被切。
- ✅ 日志用 `{}` 占位符——这是 **loguru** 的正确用法（[log_util.py:11](ruoyi-fastapi-backend/utils/log_util.py#L11)），不是 bug。反倒同文件旧的 `%s/%d` 在 loguru 下不格式化（历史遗留，非本次引入）。

---

## 第二部分 · RAG 检索链路（重写）

### 2.1 `module_rag/service/retrieval_service.py` 【重写 +220】双路召回→RRF→精排→阈值

**BEFORE** 链路：`SET ivfflat.probes=10` → 向量检索 + PG 全文检索(`to_tsvector('simple',...)`) → RRF → 取 top_k。

**AFTER** 链路：参数校验 → `SET LOCAL ivfflat.probes` → 向量召回 + ILIKE 粗召回+BM25 重排 → RRF（保留各阶段分） → 可插拔 rerank（异常降级 HeuristicReranker） → 阈值过滤。

**BEFORE 关键**：
```python
await db.execute(text("SET ivfflat.probes = 10"))          # session 级
vector_results = await cls._vector_search(...)
keyword_results = await cls._keyword_search(...)            # to_tsvector('simple') 全文检索
merged = cls._rrf_merge(vector_results, keyword_results)
return merged[:top_k]
```

**AFTER 关键**：
```python
probes = max(1, int(os.getenv('RAG_IVFFLAT_PROBES', '10')))
await db.execute(text(f'SET LOCAL ivfflat.probes = {probes}'))   # ⚠️ 事务级
vector_results = await cls._vector_search(..., top_k=candidate_k)
keyword_results = await cls._keyword_search(..., top_k=candidate_k)  # ILIKE+BM25
candidates = cls._rrf_merge(vector_results, keyword_results)
reranker = cls._reranker or build_reranker(); cls._reranker = reranker
try:
    ranked = await reranker.rerank(query_text, candidates, candidate_k)
except Exception:
    ranked = await HeuristicReranker().rerank(...)          # 降级
return [r for r in ranked if r['score'] >= threshold][:top_k]
```

**BEFORE 关键词检索（全文检索）**：
```python
sql = text("""SELECT ..., ts_rank(to_tsvector('simple', content), plainto_tsquery('simple', :query)) AS score
              FROM rag_chunk WHERE ... @@ ... ORDER BY score DESC LIMIT :top_k""")
```
**AFTER 关键词检索（ILIKE 粗召回 + 内存 BM25）**：
```python
tokens = cls._keyword_query_tokens(query_text)              # 中英混合分词
# 构造 OR ILIKE 条件，LIMIT :candidate_limit（max(top_k*10,100)，无 ORDER BY）
candidates = [cls._normalize_result(...) for ...]
scores = bm25_scores(query_text, [c['content'] for c in candidates])
for c, s in zip(candidates, scores, strict=True): c['score'] = s
candidates.sort(key=lambda item: item['score'], reverse=True)
return candidates[:top_k]
```

**🔍 Review 关注点**：
- 🔴 **高风险·`SET LOCAL` 事务作用域**（[retrieval_service.py:54](ruoyi-fastapi-backend/module_rag/service/retrieval_service.py#L54)）：codex 把 `SET` 改成 `SET LOCAL`。`SET LOCAL` 仅当前事务有效；若 `AsyncSession` 在两次 execute 间发生过 commit，probes 不作用于后面的向量查询 → 跑默认 probes=1 → **召回质量静默下降**。必须确认 `DBSessionDependency` 整条请求同一事务，否则改回 `SET`。
- 🟠 **中风险·关键词召回非确定性**（[retrieval_service.py:127-137](ruoyi-fastapi-backend/module_rag/service/retrieval_service.py#L127)）：ILIKE 粗召回 SQL **无 ORDER BY** 直接 `LIMIT candidate_limit`。PG 无排序键时按物理序返回，BM25 只能在这「任意 N 条」里重排 → 相关 chunk 若不在该批次会被**永久丢失**，同查询结果会漂移。建议加稳定排序键（如 `chunk_id`）或按命中数排序。
- ✅ `_rrf_merge` 重写后保留 `vector_score/keyword_score/fusion_score`，可解释性提升。
- ✅ `_vector_search` JOIN `rag_document` 补 `doc_name`，合理。
- ⚠️ `int(os.getenv(...))` 无 try/except，环境变量非数字会 500（配置错误，可接受）。
- ⚠️ 要求 Python 3.10+（`zip(..., strict=True)`、`X | None`）。`__pycache__` 显示 cpython-310/312，环境满足。

---

### 2.2 `module_rag/service/ranking.py` 【新增 +155】分词/BM25/精排器

**AFTER**（新增，before 不存在）：
- `MixedLanguageTokenizer`：英文按词、中文按单字+二元组（bigram）切分。
- `bm25_scores`：标准 BM25，对粗召回候选做词法精排。
- `Reranker`(Protocol) + `HeuristicReranker`（本地融合打分）+ `CohereReranker`（cross-encoder）+ `build_reranker` 工厂（按 `RAG_RERANKER_PROVIDER` 环境变量）。

HeuristicReranker 打分公式：
```python
score = 0.50*vector + 0.25*lexical_coverage + 0.10*keyword + 0.10*fusion + 0.05*heading_coverage
if metadata.get('block_type') == 'reference': score *= 0.8   # 参考文献降权
```

**🔍 Review 关注点**：
- ✅ **被真实调用**：retrieval_service 导入并使用了全部 5 个符号，非孤立代码。
- ✅ **`reference` 降权不是死代码**（已核实）：[markdown_parser.py:41](ruoyi-fastapi-backend/module_rag/service/parser/markdown_parser.py#L41) 确实在「参考文献」章节产生 `type='reference'`，经 document_service 写入 metadata 的 `block_type`。（agent 曾误报为死代码，已剔除。）
- 🟠 **CohereReranker 客户端泄漏**（[ranking.py:128](ruoyi-fastapi-backend/module_rag/service/ranking.py#L128)）：`cohere.AsyncClientV2()` 每次 rerank 新建且从不 `close()`，高频调用泄漏 HTTP 连接。改 `async with`。
- ⚠️ **降级后缓存不重置**：若 `_reranker` 缓存了配额耗尽的 CohereReranker，每次都失败→降级，但 `cls._reranker` 永不清空，改好 key 也不重建，需重启。运维隐患。
- ⚠️ `heading_coverage` 仅对**新摄入**文档生效（旧 chunk 无 heading_path）。

---

### 2.3 `module_rag/service/context_builder.py` 【新增 +80】统一上下文构建

**AFTER**（新增）：
- `RagContext` dataclass（text / citations / results）。
- `RagContextBuilder.build`：embed → hybrid_search → `from_results`。
- `from_results`：把检索结果拼成 `[n] 来源：doc · 第x页 · 标题路径\n内容` + 引用指令，并产出前端 citation 列表。

**🔍 Review 关注点**：
- ✅ 被 4 个 learning service 调用，是本次重构核心收益点。
- ⚠️ `metadata.heading_path/page/doc_name` 只有**新摄入**文档才有；存量 chunk 这些键缺失 → 引用信息降级（`来源：文档{doc_id}`，无页码/标题），不崩但退化。需决定是否回填（见风险清单）。
- ⚠️ `content[:max_chars_per_chunk]` 按字符硬截断，可能在中文句中/表格中截断。

---

### 2.4 `module_rag/service/embedding_service.py` 【重写 +125】Provider 协议 + 修复向量错位

**BEFORE**：单一 `EmbeddingService`，硬编码智谱，直接 `extend(item.embedding for item in response.data)`（假设 API 返回有序）。

**AFTER**：引入 `EmbeddingProvider` Protocol + `OpenAICompatibleEmbeddingProvider`；`EmbeddingService` 退化为门面，支持 `configure_provider` 依赖注入；配置全走环境变量。

**关键修复（BEFORE 有 bug）**：
```python
# BEFORE：假设 response.data 顺序与输入一致
batch_embeddings = [item.embedding for item in response.data]   # ⚠️ OpenAI 兼容 API 不保证顺序 → 向量错位

# AFTER：按 index 排序
ordered = sorted(response.data, key=lambda item: item.index)
all_embeddings.extend(item.embedding for item in ordered)       # ✅ 修复
# 并新增数量校验：len(embeddings) != len(texts) → RuntimeError
```

**🔍 Review 关注点**：
- ✅ **本次最重要的隐性 bug 修复**：原代码向量可能写错行，导致检索全乱。
- ✅ 维度/模型/批量与原一致（1024 / embedding-3 / batch 25），无错配。
- ✅ 默认 base_url 仍 bigmodel，`RAG_EMBEDDING_API_KEY` 回退 `ZHIPU_API_KEY`，向后兼容。
- ⚠️ `embed_single` 现在对空文本抛 `ValueError`（旧代码直接请求 API），调用方需注意（context_builder 已先 strip 校验）。

---

### 2.5 `module_rag/controller/retrieval_controller.py` 【±8】响应字段扩充

**AFTER**：响应新增 `kb_id/vector_score/keyword_score/fusion_score/rerank_score/metadata`，用于前端可解释性。删除未用的 `from fastapi import Body`。

**🔍 Review 关注点**：改动最小最干净。`rerank_score` 用 `.get(...,0)` 兜底，无 KeyError 风险。⚠️ controller 调 `hybrid_search` 未透传 `score_threshold`，走默认环境变量 `RAG_SCORE_THRESHOLD=0.15`。

---

## 第三部分 · 解析 / 切块 / 清洗

### 3.1 `module_rag/service/document_service.py` 【大改 +60】结构化摄入流水线

**BEFORE**：`blocks = parser.parse(...)` → 对每个 block 直接 `chunker.chunk(text=block["text"], metadata={"page":..,"type":..})` → extend。

**AFTER**：
```python
blocks = cls._enrich_heading_paths(parser.parse(...))   # 补 heading_path
for block in blocks:
    block_text = clean_block_text(block["text"])
    if block.get("type") == "title" or not block_text:   # 标题块不切块
        continue
    retrieval_text = cls._with_heading_context(block_text, heading_path)  # 面包屑前缀
    chunks = chunker.chunk(text=retrieval_text, metadata={
        "doc_id","doc_name","file_type","page","heading_path","block_type"   # 大幅扩充
    })
    for chunk in chunks:
        if not is_valid_chunk(chunk["content"]): continue
        fingerprint = content_fingerprint(chunk["content"])
        if fingerprint in seen_fingerprints: continue      # 文档内去重
        seen_fingerprints.add(fingerprint); all_chunks.append(chunk)
if not all_chunks:
    raise ValueError("文档解析后没有可用文本分块")
```
另：删除文档时新增 `await ChunkDao.delete_by_doc_id(db, doc_id)`（[L117](ruoyi-fastapi-backend/module_rag/service/document_service.py#L117)）——原代码只软删文档，分块残留会导致脏检索。

**🔍 Review 关注点**：
- ✅ 流水线设计合理（清洗→章节上下文→去重→结构化 metadata）。
- ✅ **parse_status 不会卡死**（已核实）：[L218-223](ruoyi-fastapi-backend/module_rag/service/document_service.py#L218) 的 `except Exception` 会把状态置 `"9"`（失败），覆盖 `raise ValueError`。（agent 曾误报卡死，已剔除。）
- ⚠️ `_enrich_heading_paths` 对 MarkdownParser 已自带 heading_path 的块用 `setdefault` 不覆盖，但内部仍维护冗余 heading_stack——功能正确，重复劳动。

---

### 3.2 `module_rag/service/parser/markdown_parser.py` 【新增 +104】结构感知 MD 解析

**AFTER**（新增）：按 `#` 标题层级维护 `heading_stack`，输出带 `heading_path/heading_level/type`（title/code/table/list/quote/reference/text）的块；识别「参考文献/references/bibliography」章节；用 `find_codec` 处理编码；支持 ` ``` `/`~~~` 围栏。

**🔍 Review 关注点**：
- ✅ `.md` 解析器从 `TxtParser` 升级为结构化解析（[parser/__init__.py](ruoyi-fastapi-backend/module_rag/service/parser/__init__.py) 已注册），是检索质量提升的基础。
- ⚠️ 围栏切换仅靠前缀 `startswith(('```','~~~'))`，`~~~` 结束 ` ``` ` 不匹配时不闭合（边缘）。
- ⚠️ `_table_re = r'^\s*\|.*\|\s*$'`，任何含 `|` 的普通段落会被误判为 table（低风险）。

---

### 3.3 `module_rag/service/parser/docx_parser.py` 【修复+优化 ±30】

**🔴 关键修复·return 缩进**：
```python
# BEFORE：return 在 for 循环体内（12 空格缩进）→ 只返回首个元素就退出，DOCX 内容大量丢失
            elif tag == 'tbl':
                ...
-            return blocks        # ⚠️ 在循环内！

# AFTER：移到循环外（8 空格）
        return blocks             # ✅
```
**性能优化**：原代码每个 element 在内层 `for p in doc.paragraphs` 线性找样式（O(n²)），改为预建 `{p._element: p}` 字典（O(n)）；`para_text` 改用 `paragraph.text`（原遍历 `element.iter()` 可能重复抽取）。

**🔍 Review 关注点**：
- ✅ **严重历史 bug 修复**——原 DOCX 解析几乎丢光内容。新测试 [test_parser_and_chunker.py:24](ruoyi-fastapi-backend/tests/rag/test_parser_and_chunker.py#L24) 覆盖。
- ⚠️ 标题识别改为 `'heading' in para_style.lower()`，**"Title"/"Subtitle" 这类不含 "heading" 的样式会被判为正文**，DOCX 结构信息可能丢失（取决于实际文档样式）。

---

### 3.4 `module_rag/service/chunker/fixed_chunker.py` 【重写切分逻辑 ±39】

**BEFORE**（逐字符累加）：
```python
current = prefix
for char in text:
    current += char
    if char in SENTENCE_ENDS and len(current) >= chunk_size:
        chunks.append(make_chunk(current.strip())); current = current[-overlap:]
```
**AFTER**（滑动窗口找句子边界，`[chunk_size*0.6, chunk_size]` 区间）：
```python
content = prefix + text; start = 0; minimum_boundary = max(1, int(chunk_size*0.6))
while len(content) - start > chunk_size:
    hard_end = start + chunk_size
    # 在 [hard_end, start+minimum_boundary) 倒序找句子结束符
    boundary = ... ; end = boundary if boundary > start else hard_end
    chunks.append(make_chunk(content[start:end].strip()))
    start = max(end - overlap, start + 1)
```

**🔍 Review 关注点**：
- ✅ 新算法优先在句子边界切，切片质量更好；`_make_chunk` 用 `dict(metadata or {})` 浅拷贝，避免多处共享引用。
- 🟠 **长段→短段过渡丢 overlap**（[fixed_chunker.py:55-57](ruoyi-fastapi-backend/module_rag/service/chunker/fixed_chunker.py#L55)）：长段落切分后 `current_chunk=""`，紧接一个**正常段落**时会走 `current_chunk = overlap_text + para` 分支——但此时 `overlap_text` 是上一长段的尾，OK；问题在若长段后又来长段，`overlap_text` 被重新赋值前的中间态。建议复核过渡处行为一致性。

---

### 3.5 `module_rag/utils/text_cleaner.py` 【新增 +30】清洗/校验/指纹

**AFTER**（新增）：`clean_block_text`（保留段落换行的轻量清洗）、`is_valid_chunk`（去空白后≥20 字且可打印率≥0.9）、`content_fingerprint`（sha256 去空白+casefold，文档内去重）。原有 `find_codec/clean_text/is_chinese` 保留。

**🔍 Review 关注点**：无 bug。`is_valid_chunk` 先判长度再除法，无除零；`content_fingerprint(None)` 有兜底。

---

### 3.6 `module_rag/service/parser/__init__.py` 【±5】注册 MarkdownParser

`.md` 映射从 `TxtParser` 改为 `MarkdownParser`。✅ 已正确注册，document_service 经 `get_parser` 调用链路通畅。

---

## 第四部分 · DAO / DO（清理 + 优化，低风险）

### `module_rag/dao/chunk_dao.py` 【±18】bulk_insert 性能优化
**BEFORE**：逐条 `db.add` + 每条 `await db.flush()`（N 次 flush）。
**AFTER**：`db.add_all([...])` + 单次 `await db.flush()`，返回的 `chunk_id` 由 SQLAlchemy 回填自增主键，**取值正确**。✅ 性能明显提升，行为一致。

### `chunk_do.py` / `knowledge_base_do.py` / `knowledge_base_dao.py` 【清理】
仅删除未使用的 import（`String`/`Text`/`DataBaseConfig`/`SqlalchemyUtil`/`text`/`delete`/`AsyncAttrs`）。**无任何 Column 增删改，`__table__` 未动，不需要迁移脚本。** ✅

---

## 第五部分 · 测试（新增 4 个，质量较好）

| 文件 | 覆盖 | 评价 |
|---|---|---|
| `test_kb_scope_policy.py` | Default/Learning 策略 + 注册覆盖 | ✅ 覆盖核心权限判定 |
| `test_ranking.py` | 分词/BM25/RRF(`2/61`)/HeuristicReranker | ✅ 验证 RRF 公式与重排 |
| `test_context_builder.py` | `from_results` 引用格式 | ✅ 覆盖 citation 生成 |
| `test_parser_and_chunker.py` | MD heading_path/docx 全读/切块不重复尾 | ✅ 覆盖 docx 修复点 |

> 建议合并前先跑：`cd ruoyi-fastapi-backend && python -m pytest tests/rag/ -v`（注意 ranking/embedding 依赖 `cohere`/`openai` 是否装了）。

---

## 🔴 风险清单（合并前必须确认）

| 级别 | 问题 | 位置 | 建议 |
|---|---|---|---|
| 🔴 高 | `SET LOCAL ivfflat.probes` 可能不作用于向量查询（事务作用域） | retrieval_service.py:54 | 确认会话事务模型，否则改回 `SET` |
| 🟠 中 | 关键词 ILIKE 粗召回无 ORDER BY，BM25 在任意子集重排，可能丢召回+结果漂移 | retrieval_service.py:127 | 加稳定排序键 |
| 🟠 中 | 存量 chunk 无 `heading_path/page`，精排与引用溯源对旧数据退化 | context_builder.py / ranking.py | 决定是否写回填脚本 |
| 🟡 低 | CohereReranker 客户端未 close，资源泄漏 | ranking.py:128 | 改 `async with` |
| 🟡 低 | 降级后 `_reranker` 缓存不重置，配额恢复后不自动重建 | retrieval_service.py:60 | 失败时置 None |
| 🟡 低 | 权限注册依赖隐式 import 顺序，非 server 场景回退到 Default | hooks.py / kb_scope_policy.py | 加优先级或延迟解析 |
| 🟡 低 | docx 标题仅认含 "heading" 的样式，Title/Subtitle 漏判 | docx_parser.py:31 | 视文档样式约定决定 |

## ✅ 本次改动的净收益（不要因为 review 就否掉）

1. **架构落地**：知识库权限机制/规则切分，RAG 模块可独立复用（对齐 [[framework-mechanism-vs-policy-split]]）。
2. **检索升级**：双路召回+RRF+可插拔精排+可解释分数，比原「simple 全文检索（中文实际失效）」强很多。
3. **修复严重 bug**：docx 只返回首块、embedding 向量错位——这两个不修，RAG 基本不可用。
4. **结构化摄入**：heading_path/章节面包屑/去重，提升检索精度。
5. **测试覆盖**：4 个新测试覆盖核心新逻辑。

## 合并建议

- **可以合并**，但建议合并前：① 确认 `SET LOCAL` 事务行为（或直接改回 `SET`）；② 跑通 `tests/rag/`；③ 决定存量数据 metadata 是否回填。
- 低风险项（Cohere 泄漏、缓存重置、docx 标题）可合并后单独修，不阻塞。
