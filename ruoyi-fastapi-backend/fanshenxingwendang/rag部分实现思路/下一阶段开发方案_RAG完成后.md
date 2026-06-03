# RAG 完成后的完整开发方案

> **当前状态**：`module_rag` 代码已开发完毕，数据尚未入库（知识库为空）
> **目标**：按顺序完成「知识库初始化 → LLM 服务封装 → 四区联动」的全部开发工作
> **框架**：RuoYiFast（FastAPI + SQLAlchemy async + Vue3）
> **原则**：每个阶段都要有可验证的交付物，做完一步再做下一步
> **文档版本**：v2.0（2026-06-03 修订，修复数据类型、补全教师功能、新增 LLM 封装层）

---

## 总体开发顺序

```
当前位置
    ↓
阶段 0：知识库数据初始化（把数据灌进去，验证 RAG 可用）
    ↓
阶段 0.5：封装统一 LLM 调用层（四区 AI 功能的前置依赖）        ← 新增！
    ↓
阶段 1：教学任务管理（教师创建任务，学生看到任务）
    ↓
阶段 2：学习记录主表 + 状态机（四区联动的骨架）
    ↓
阶段 3：情境区（第一区）
    ↓
阶段 4：决策区（第二区）
    ↓
阶段 5：反思区（第三区，核心创新）
    ↓
阶段 6：研究生成区（第四区）
    ↓
阶段 7：教师监控 + 评价功能                                      ← 重写！
    ↓
阶段 8：前端四区页面开发
```

**为什么这个顺序？**

- 阶段 0 先做：没有知识库数据，后面所有 AI 功能都是空壳，无法测试
- **阶段 0.5 先做**：四区所有 AI 功能都需要调 LLM，不先封装好统一调用层，每个区都各自为战，API Key / 重试 / JSON 解析逻辑会重复散落各处
- 阶段 1-2 先做：任务和学习记录是四区的骨架，没它们，情境/决策/反思都挂不上去
- 阶段 3-6 按四区顺序：每区依赖前一区的数据（情境→决策→反思→研究）
- 阶段 7 最后：消费前面所有数据，放最后做最合理
- 阶段 8 可以和后端并行：前端可以在后端出接口的同时开始页面框架

---

## 阶段 0：知识库数据初始化

> **目标**：把社会工作专业文档灌入知识库，验证检索效果
> **预计时间**：1-2 天
> **交付物**：`rag_chunk` 表里有向量化完成的分块数据，检索测试通过

### Step 0.0 RAG 模块冒烟测试（新增）

在灌数据之前，先验证 RAG 模块的管道是否通畅。不要等上传文档后才发现 parser 或 embedding 有 bug。

```python
# tests/test_rag_smoke.py
"""RAG 模块冒烟测试 — 在灌数据前先跑一遍"""
import asyncio

async def test_rag_pipeline():
    from module_rag.service.parser.txt_parser import TxtParser
    from module_rag.service.chunker.fixed_chunker import FixedChunker
    from module_rag.service.embedding_service import EmbeddingService

    # 1. 解析
    blocks = TxtParser().parse("tests/test_sample.txt")  # 准备一个 500+ 字的 txt
    assert len(blocks) > 0, "解析结果为空"

    # 2. 分块
    chunks = FixedChunker(500, 50).chunk(blocks[0]["text"])
    assert len(chunks) > 0, "分块结果为空"

    # 3. 向量化
    embeddings = await EmbeddingService.embed_texts([chunks[0]["content"]])
    assert len(embeddings[0]) == 1024, f"向量维度错误: {len(embeddings[0])}"

    print("✅ RAG 管道冒烟测试通过")

if __name__ == "__main__":
    asyncio.run(test_rag_pipeline())
```

```bash
python tests/test_rag_smoke.py
# 预期输出：✅ RAG 管道冒烟测试通过
```

### Step 0.1 确认 module_rag 的接口可用

在开始灌数据前，先验证 RAG 模块的接口是否正常工作：

```bash
# 启动项目
cd your-ruoyifast-project
python app.py

# 测试知识库创建接口（用 curl 或 Postman）
curl -X POST http://localhost:8080/rag/kb \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "kb_name": "社会工作理论知识库",
    "kb_desc": "包含社会工作教材、论文、伦理守则等",
    "chunk_size": 500,
    "chunk_overlap": 50
  }'
```

预期：返回 `kb_id`，数据库 `rag_knowledge_base` 表有记录。

### Step 0.2 准备知识库文档

按 PRD 的知识来源规划，优先级从高到低准备以下文档：

| 优先级 | 文档类型 | 建议数量 | 格式 |
|---|---|---|---|
| P0（必须有） | 社会工作伦理守则（如 NASW 伦理守则中文版） | 1-2 份 | PDF/TXT |
| P0（必须有） | 社会工作教材核心章节（反身性、行动研究相关） | 3-5 份 | PDF |
| P1 | 教师课件（PPT 转 PDF） | 若干 | PDF |
| P1 | 行动研究方法相关论文 | 5-10 篇 | PDF |
| P2 | 已整理的结构化案例（JSON 格式） | 若干 | JSON/TXT |

**推荐先从最少量开始**：准备 3-5 份 PDF，够验证检索效果即可，后续持续补充。

### Step 0.3 通过接口上传文档

```bash
# 上传一个 PDF 文档
curl -X POST http://localhost:8080/rag/document/upload/1 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/社会工作伦理守则.pdf"
```

**观察数据库状态变化**：

```sql
-- 文档状态应该从 0 → 1(解析中) → 2(完成)
SELECT doc_id, doc_name, parse_status, embed_status, chunk_count
FROM rag_document
WHERE kb_id = 4;

-- 分块记录应该有数据
SELECT COUNT(*), AVG(token_count)
FROM rag_chunk
WHERE kb_id = 4;

-- 验证向量已写入（embedding 不为空）
SELECT chunk_id, LEFT(content, 50), token_count,
       CASE WHEN embedding IS NOT NULL THEN '有向量' ELSE '无向量' END AS vec_status
FROM rag_chunk
WHERE kb_id = 4
LIMIT 10;
```

### Step 0.4 验证检索效果（关键！）

这步不能跳过。用真实的社会工作问题测试检索：

```bash
# 测试向量检索
curl -X POST http://localhost:8080/rag/retrieval/search \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "kb_ids": [4],
    "query": "社会工作者如何处理服务对象的阻抗行为",
    "top_k": 5
  }'
```

**验收标准**：返回的 5 个文本块内容，应该和"服务对象阻抗"话题相关。如果结果完全不相关，说明 Embedding 或索引有问题，必须先修复再继续。

### Step 0.5 建立「伦理守则」专用知识库

决策区的 AI 需要专门检索伦理相关内容，建议单独建一个知识库：

```bash
# 创建伦理守则知识库
curl -X POST http://localhost:8080/rag/kb \
  -d '{"kb_name": "社会工作伦理守则库", "kb_desc": "NASW伦理守则、本土伦理规范"}'

# 再创建理论知识库
curl -X POST http://localhost:8080/rag/kb \
  -d '{"kb_name": "社会工作理论库", "kb_desc": "行动研究、反身性、赋权理论等"}'
```

> **为什么要分开？** 决策区检索伦理条款，反思区检索理论概念，目的不同，分开能提高检索精准度。

---

## 阶段 0.5：封装统一 LLM 调用层（新增）

> **目标**：为四区 AI 功能提供统一的 LLM 调用接口
> **预计时间**：1 天
> **交付物**：`LlmService` 类 + `parse_llm_json()` 工具函数
> **为什么必须先做**：四区所有 AI 功能都需要调 LLM，不先封装好，API Key / 重试 / JSON 解析逻辑会重复散落各处

### 问题背景

文档里到处引用 `call_llm()`，但你项目里已有 `module_ai` 模块（从 `module_ai/controller/ai_chat_controller.py` 可以看出）。新模块 `module_learning` 不能各自为战，必须统一封装。

### 目录结构

```
module_learning/
├── service/
│   ├── llm_service.py              ← 统一 LLM 调用层
│   └── llm_json_parser.py          ← LLM JSON 输出解析器
```

### llm_json_parser.py（先写这个，所有 AI 接口都依赖它）

```python
# module_learning/service/llm_json_parser.py
"""
LLM JSON 输出解析器
大模型偶尔返回带 markdown 代码块的文本或不合法 JSON，这个工具兼容各种格式
"""
import json
import re


def parse_llm_json(text: str) -> dict:
    """
    从 LLM 输出中提取 JSON，兼容各种格式：
    1. 直接 JSON
    2. ```json ... ``` 代码块
    3. 最外层 { } 匹配
    """
    if not text or not text.strip():
        raise ValueError("LLM 输出为空")

    text = text.strip()

    # 尝试 1：直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试 2：提取 ```json ... ``` 代码块
    match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 尝试 3：找最外层 { }
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"无法从 LLM 输出中提取 JSON，原文前200字: {text[:200]}")


def safe_parse_llm_json(text: str, default: dict = None) -> dict:
    """安全版本：解析失败返回 default 而不是抛异常"""
    try:
        return parse_llm_json(text)
    except Exception:
        return default or {}
```

### llm_service.py

```python
# module_learning/service/llm_service.py
"""
统一 LLM 调用层
复用 module_ai 的模型配置，但调用方式独立（非流式 JSON 输出为主）
"""
import os
import asyncio
from openai import AsyncOpenAI
from module_learning.service.llm_json_parser import parse_llm_json


class LlmService:
    """
    统一的大模型调用服务
    - 非流式调用（四区 AI 分析场景，需要完整 JSON 输出）
    - 统一重试、超时、JSON 解析
    - API 配置复用 .env.test 中的环境变量
    """

    # 从环境变量读取配置（和 module_ai 保持一致）
    API_KEY = os.getenv('ZHIPU_API_KEY', '')       # 或 DEEPSEEK_API_KEY
    BASE_URL = os.getenv('LLM_BASE_URL', 'https://open.bigmodel.cn/api/paas/v4')
    MODEL_NAME = os.getenv('LLM_MODEL', 'glm-4-flash')   # 默认用便宜的模型
    MAX_RETRIES = 3
    TIMEOUT = 60  # 秒

    @classmethod
    def _get_client(cls) -> AsyncOpenAI:
        return AsyncOpenAI(
            api_key=cls.API_KEY,
            base_url=cls.BASE_URL,
            timeout=cls.TIMEOUT,
        )

    @classmethod
    async def chat(cls, prompt: str, system: str = None, max_tokens: int = 2000) -> str:
        """
        基础调用：发送 prompt，返回文本结果
        """
        client = cls._get_client()
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        for retry in range(cls.MAX_RETRIES):
            try:
                response = await client.chat.completions.create(
                    model=cls.MODEL_NAME,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=0.7,
                )
                return response.choices[0].message.content
            except Exception as e:
                if retry == cls.MAX_RETRIES - 1:
                    raise RuntimeError(f"LLM 调用失败（重试 {cls.MAX_RETRIES} 次后）: {str(e)}")
                await asyncio.sleep(1 * (retry + 1))

    @classmethod
    async def chat_json(cls, prompt: str, system: str = None, max_tokens: int = 2000) -> dict:
        """
        JSON 调用：发送 prompt，返回解析后的 dict
        自动处理 LLM 返回的各种 JSON 格式（带代码块、带前缀文字等）
        """
        raw_text = await cls.chat(prompt, system=system, max_tokens=max_tokens)
        return parse_llm_json(raw_text)
```

### .env.test 追加配置

```env
# -------- LLM 统一调用配置 --------
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
LLM_MODEL=glm-4-flash
# 或用 DeepSeek:
# LLM_BASE_URL=https://api.deepseek.com/v1
# LLM_MODEL=deepseek-chat
```

### 验收标准

```python
# tests/test_llm_service.py
import asyncio
from module_learning.service.llm_service import LlmService
from module_learning.service.llm_json_parser import parse_llm_json

async def test_llm():
    # 测试基础调用
    result = await LlmService.chat("请说一句话")
    print(f"基础调用: {result}")

    # 测试 JSON 调用
    result = await LlmService.chat_json(
        "请输出一个 JSON，包含 name 和 age 两个字段。只输出 JSON，不要其他内容。"
    )
    print(f"JSON 调用: {result}")
    assert "name" in result or "age" in result

    # 测试 JSON 解析器（兼容带代码块的输出）
    parsed = parse_llm_json('```json\n{"key": "value"}\n```')
    assert parsed["key"] == "value"

    print("✅ LLM 服务验收通过")

asyncio.run(test_llm())
```

---

## 阶段 1：教学任务管理模块

> **目标**：教师可以创建任务，学生可以看到并开始任务
> **预计时间**：3 天
> **交付物**：任务 CRUD 接口 + 任务-班级分配接口

### 涉及数据表

```sql
-- 教学任务表
CREATE TABLE edu_task (
    task_id        BIGSERIAL PRIMARY KEY,
    task_name      VARCHAR(200) NOT NULL,          -- 任务名称
    task_description TEXT,                         -- 任务描述（给学生看的引导语）【v2.0: task_desc→task_description】
    teacher_id     BIGINT NOT NULL REFERENCES sys_user(user_id),
    -- 各区知识库配置（告诉系统这个任务用哪些知识库）
    scenario_kb_ids  JSONB,                        -- 情境区使用的知识库 ID 列表
    decision_kb_ids  JSONB,                        -- 决策区使用的知识库 ID 列表
    reflection_kb_ids JSONB,                       -- 反思区使用的知识库 ID 列表
    research_kb_ids  JSONB,                        -- 研究区使用的知识库 ID 列表
    -- 各区 AI 行为配置
    scenario_config  JSONB,                        -- 情境区 Prompt 参数（可选，用默认也行）
    reflection_config JSONB,                       -- 反思区配置（最小反思深度等）
    deadline       TIMESTAMP,                      -- 截止时间
    status         CHAR(1) DEFAULT '0',            -- 0草稿 1已发布 2已关闭
    del_flag       CHAR(1) DEFAULT '0',
    create_by      VARCHAR(64) DEFAULT '',
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_by      VARCHAR(64) DEFAULT '',
    update_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE edu_task IS '教学任务表';

-- 任务-班级分配表（一个任务可分配给多个班级）
CREATE TABLE edu_task_class (
    id             BIGSERIAL PRIMARY KEY,
    task_id        BIGINT NOT NULL REFERENCES edu_task(task_id),
    dept_id        BIGINT NOT NULL,                -- 班级（复用 sys_dept 表的部门）
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE edu_task_class IS '任务-班级分配表';
```

### 需要实现的接口

| 接口 | 方法 | 权限 | 说明 |
|---|---|---|---|
| `/learning/task/list` | GET | teacher/admin | 任务列表（教师看自己的） |
| `/learning/task/create` | POST | teacher | 创建任务 |
| `/learning/task/update` | PUT | teacher | 编辑任务 |
| `/learning/task/delete/{task_id}` | DELETE | teacher | 逻辑删除任务（del_flag='2'） |
| `/learning/task/copy/{task_id}` | POST | teacher | 复制任务（复制配置，不复制班级分配） |
| `/learning/task/publish/{task_id}` | PUT | teacher | 发布任务到班级 |
| `/learning/task/student/list` | GET | student | 学生查看自己的任务列表 |
| `/learning/task/detail/{task_id}` | GET | all | 任务详情 |

### 目录结构（按 RuoYiFast 规范）

```
module_learning/
├── __init__.py
├── controller/
│   └── task_controller.py
├── dao/
│   └── task_dao.py
├── entity/
│   ├── do/
│   │   └── task_do.py
│   └── vo/
│       └── task_vo.py
└── service/
    ├── llm_service.py              ← 阶段0.5已创建
    ├── llm_json_parser.py          ← 阶段0.5已创建
    └── task_service.py
```

### task_do.py 核心字段

```python
# module_learning/entity/do/task_do.py
from datetime import datetime
from sqlalchemy import CHAR, BigInteger, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from config.database import Base


class EduTask(Base):
    __tablename__ = "edu_task"
    __table_args__ = {"comment": "教学任务表"}

    task_id          = Column(BigInteger, primary_key=True, autoincrement=True)
    task_name        = Column(String(200), nullable=False)
    task_description = Column(Text)                                  # 【v2.0: task_desc→task_description】
    teacher_id       = Column(BigInteger, nullable=False)
    scenario_kb_ids  = Column(JSONB)               # [1, 2]
    decision_kb_ids  = Column(JSONB)               # [3]
    reflection_kb_ids = Column(JSONB)              # [1, 2]
    research_kb_ids  = Column(JSONB)               # [1, 2, 4]
    scenario_config  = Column(JSONB)
    reflection_config = Column(JSONB)
    deadline         = Column(DateTime)
    status           = Column(CHAR(1), server_default='0')         # 【v2.0: String(1)→CHAR(1)】
    del_flag         = Column(CHAR(1), server_default='0')         # 【v2.0: String(1)→CHAR(1)】
    create_by        = Column(String(64), server_default='')
    create_time      = Column(DateTime, default=datetime.now)
    update_by        = Column(String(64), server_default='')
    update_time      = Column(DateTime, default=datetime.now)
```

### 验收标准

```bash
# 教师创建任务
POST /learning/task/create
{
  "task_name": "张大爷案例行动研究",
  "task_description": "请结合你的实习经历，完成情境描述、决策分析、反思日志和研究框架的撰写。",
  "scenario_kb_ids": [1, 2],
  "decision_kb_ids": [3],
  "reflection_kb_ids": [1, 2],
  "deadline": "2026-09-30T23:59:59"
}
# 预期：返回 task_id

# 发布任务到班级
PUT /learning/task/publish/1
{"dept_ids": [100]}
# 预期：edu_task_class 表有记录，task 的 status 变为 1

# 学生查看任务列表
GET /learning/task/student/list
# 预期：返回学生所在班级的已发布任务

# 复制任务
POST /learning/task/copy/1
# 预期：创建一个新任务，配置和原任务相同，名称自动加"(副本)"
```

---

## 阶段 2：学习记录主表 + 状态机

> **目标**：为每个「学生+任务」组合创建学习记录，驱动四区状态流转
> **预计时间**：2 天
> **交付物**：`edu_learning_record` 表 + 状态流转接口

### 核心设计思想

`edu_learning_record` 是四区联动的**主控表**，记录一个学生完成一个任务的完整状态。

```
学生点击「开始任务」
      ↓
创建 edu_learning_record（current_stage=scenario，各状态默认值）
      ↓
学生完成情境区 → 点击「进入决策区」
      ↓
current_stage 变为 decision
      ↓
完成决策区 → current_stage 变为 reflection
      ↓
完成反思区 → current_stage 变为 research
      ↓
提交研究成果 → status 变为 submitted
      ↓
教师评分 → status 变为 completed
```

### 数据表

```sql
CREATE TABLE edu_learning_record (
    record_id      BIGSERIAL PRIMARY KEY,
    task_id        BIGINT NOT NULL REFERENCES edu_task(task_id),
    student_id     BIGINT NOT NULL REFERENCES sys_user(user_id),
    -- 当前所在阶段：scenario/decision/reflection/research/submitted/completed
    current_stage  VARCHAR(20) DEFAULT 'scenario',
    -- 各区完成状态：0未开始 1进行中 2已完成
    scenario_status  CHAR(1) DEFAULT '0',
    decision_status  CHAR(1) DEFAULT '0',
    reflection_status CHAR(1) DEFAULT '0',
    research_status  CHAR(1) DEFAULT '0',
    -- 关联的各区数据 ID（方便快速查找，避免每次 JOIN）【v2.0: 补全四个区】
    scenario_id    BIGINT,                         -- 关联 edu_scenario_data.scenario_id
    decision_id    BIGINT,                         -- 关联 edu_decision_data.decision_id（最新/汇总）
    reflection_id  BIGINT,                         -- 关联 edu_reflection_data.reflection_id
    research_id    BIGINT,                         -- 关联 edu_research_data.research_id
    -- 整体状态
    status         VARCHAR(20) DEFAULT 'ongoing',  -- ongoing/submitted/completed
    score          DECIMAL(5,2),                   -- 教师评分
    teacher_feedback TEXT,                         -- 教师反馈
    start_time     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    submit_time    TIMESTAMP,
    complete_time  TIMESTAMP,
    del_flag       CHAR(1) DEFAULT '0',
    create_by      VARCHAR(64) DEFAULT '',
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_by      VARCHAR(64) DEFAULT '',
    update_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(task_id, student_id)                    -- 一个学生对一个任务只有一条记录
);
COMMENT ON TABLE edu_learning_record IS '学习记录主表（四区联动主控）';
```

### 需要实现的接口

| 接口 | 方法 | 权限 | 说明 |
|---|---|---|---|
| `/learning/record/start/{task_id}` | POST | student | 开始任务（创建 record） |
| `/learning/record/my` | GET | student | 我的学习记录列表 |
| `/learning/record/detail/{record_id}` | GET | student/teacher | 记录详情（包含各区完成状态） |
| `/learning/record/advance/{record_id}` | PUT | student | 推进到下一区（状态流转） |
| `/learning/record/class` | GET | teacher | 班级所有学生的记录（教师监控） |

### advance 接口的状态流转逻辑

```python
# module_learning/service/record_service.py
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

STAGE_FLOW = {
    "scenario": "decision",
    "decision": "reflection",
    "reflection": "research",
    "research": "submitted",
}

STAGE_STATUS_FIELD = {
    "scenario": "scenario_status",
    "decision": "decision_status",
    "reflection": "reflection_status",
    "research": "research_status",
}


class RecordService:
    @classmethod
    async def advance_stage(cls, db: AsyncSession, record_id: int, student_id: int):
        """
        推进到下一区
        前置校验：当前区的核心数据必须已保存（否则不允许推进）【v2.0: 新增校验】
        """
        record = await RecordDao.get_by_id(db, record_id)

        # 权限校验
        if record.student_id != student_id:
            raise PermissionError("无权操作他人记录")

        # 【v2.0: 前置校验——当前区必须有数据才能推进】
        current_stage = record.current_stage
        cls._validate_advance(record, current_stage)

        # 当前区状态置为完成
        status_field = STAGE_STATUS_FIELD.get(current_stage)
        if status_field:
            setattr(record, status_field, "2")  # 2=完成

        # 切换到下一区
        next_stage = STAGE_FLOW.get(current_stage)
        if not next_stage:
            raise ValueError(f"已是最后阶段: {current_stage}")

        record.current_stage = next_stage

        # 如果推进到 decision，同时标记 decision 为进行中
        next_status_field = STAGE_STATUS_FIELD.get(next_stage)
        if next_status_field:
            setattr(record, next_status_field, "1")  # 1=进行中

        # 如果是 submitted，记录提交时间
        if next_stage == "submitted":
            record.status = "submitted"
            record.submit_time = datetime.now()

        await db.commit()
        return record

    @classmethod
    def _validate_advance(cls, record, current_stage: str):
        """
        【v2.0: 前置校验逻辑】
        检查当前区是否有必要的数据，没有就不让推进
        """
        if current_stage == "scenario":
            # 情境区必须有关联的 scenario 数据
            if not record.scenario_id:
                raise ValueError("情境区尚未保存数据，无法进入决策区")
        elif current_stage == "decision":
            # 决策区至少需要有一条决策记录（通过 record_id 查询）
            # 这里只做基本检查，详细检查在 dao 层
            pass
        elif current_stage == "reflection":
            # 反思区必须有反思文本
            if not record.reflection_id:
                raise ValueError("反思区尚未保存数据，无法进入研究生成区")
```

### 验收标准

```sql
-- 学生开始任务后，应该有记录
SELECT record_id, task_id, student_id, current_stage, scenario_status
FROM edu_learning_record
WHERE student_id = 1;
-- 预期: current_stage='scenario', scenario_status='0'

-- 调用 advance 后
-- current_stage='decision', scenario_status='2', decision_status='1'

-- 四区外键都有值
SELECT record_id, scenario_id, decision_id, reflection_id, research_id
FROM edu_learning_record
WHERE record_id = 1;
-- 预期: 随着各区推进，四个外键依次有值
```

---

## 阶段 3：情境区（Scenario Zone）

> **目标**：学生描述实践场景，AI 识别关键事件和专业问题
> **预计时间**：3 天
> **交付物**：情境区 CRUD + AI 分析接口

### 数据表

```sql
-- 情境区主数据表
CREATE TABLE edu_scenario_data (
    scenario_id    BIGSERIAL PRIMARY KEY,
    record_id      BIGINT NOT NULL REFERENCES edu_learning_record(record_id),
    student_id     BIGINT NOT NULL REFERENCES sys_user(user_id),
    -- 学生输入
    description    TEXT,                           -- 场景描述正文
    key_events     JSONB,                          -- 学生标注的关键事件节点列表
    -- AI 分析结果（存储最新一次的分析结果）
    identified_problems JSONB,                     -- AI 识别的专业问题列表
    category_tags  JSONB,                          -- 场景分类标签（老年社工/医务社工等）
    -- 状态
    status         CHAR(1) DEFAULT '0',            -- 0草稿 1已确认（进入决策区）
    del_flag       CHAR(1) DEFAULT '0',
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 情境区 AI 对话记录表（追问历史）
CREATE TABLE edu_scenario_dialogue (
    dialogue_id    BIGSERIAL PRIMARY KEY,
    scenario_id    BIGINT NOT NULL REFERENCES edu_scenario_data(scenario_id),
    role           VARCHAR(20) NOT NULL,           -- user / assistant
    content        TEXT NOT NULL,
    dialogue_type  VARCHAR(30),                    -- analyze（首次分析）/ followup（追问）
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 需要实现的接口

| 接口 | 方法 | 说明 |
|---|---|---|
| `/learning/scenario/save` | POST/PUT | 保存/更新场景描述（草稿自动保存） |
| `/learning/scenario/analyze` | POST | AI 首次分析：识别关键事件 + 专业问题 |
| `/learning/scenario/followup` | POST | AI 追问：根据已有描述追问关键细节 |
| `/learning/scenario/confirm` | PUT | 确认情境，允许进入决策区 |
| `/learning/scenario/detail/{record_id}` | GET | 获取情境区数据（含对话历史） |

### AI 分析接口的核心逻辑

```python
# module_learning/service/scenario_service.py
from module_rag.service.embedding_service import EmbeddingService
from module_rag.service.retrieval_service import RetrievalService
from module_learning.service.llm_service import LlmService


SCENARIO_ANALYZE_PROMPT = """你是一位经验丰富的社会工作督导，擅长帮助实习社工分析实践情境。

任务：根据学生描述的实践场景，完成以下工作：
1. 识别场景中的关键事件节点（2-4个，按时间顺序）
2. 界定其中蕴含的专业问题（2-3个）
3. 判断问题所属的社会工作实践领域
4. 提出追问建议，帮助学生补充关键信息

专业知识参考：
{retrieved_knowledge}

学生场景描述：
{student_scenario}

请以专业但易于理解的语气回复。

输出 JSON 格式：
{{
  "key_events": [
    {{"index": 1, "event": "事件描述", "timestamp": "可选的时间节点"}}
  ],
  "identified_problems": [
    {{"title": "问题标题", "description": "详细描述", "domain": "社工领域"}}
  ],
  "category_tags": ["老年社工", "危机干预"],
  "followup_questions": ["追问1", "追问2"]
}}"""


class ScenarioAiEngine:
    @classmethod
    async def analyze(cls, db, scenario, task) -> dict:
        """情境分析：RAG 检索 + LLM 生成"""

        # 1. RAG 检索：用场景描述检索相关知识
        kb_ids = task.scenario_kb_ids or []
        if kb_ids:
            query_embedding = await EmbeddingService.embed_single(scenario.description)
            retrieved_chunks = await RetrievalService.hybrid_search(
                db=db,
                query_text=scenario.description,
                query_embedding=query_embedding,
                kb_ids=kb_ids,
                top_k=5,
            )
            knowledge_context = "\n\n".join([
                f"【参考{i+1}】{chunk['content']}"
                for i, chunk in enumerate(retrieved_chunks)
            ])
        else:
            knowledge_context = "（暂无相关知识库）"

        # 2. 构建 Prompt
        prompt = SCENARIO_ANALYZE_PROMPT.format(
            retrieved_knowledge=knowledge_context,
            student_scenario=scenario.description,
        )

        # 3. 调用 LLM（使用阶段 0.5 封装的统一服务）
        result = await LlmService.chat_json(prompt, max_tokens=2000)
        return result
```

### 情境区的 AI 追问接口

追问（followup）和首次分析（analyze）的区别：

- analyze：不带对话历史，只分析场景文本，输出结构化结果
- followup：带对话历史，模拟督导追问，输出自然语言问题

```python
SCENARIO_FOLLOWUP_PROMPT = """你是一位经验丰富的社会工作督导。

当前学生的场景描述：
{student_scenario}

已识别的关键事件：
{key_events}

对话历史：
{dialogue_history}

你的任务：针对场景中信息不够完整的地方，追问一个最关键的问题。
要求：
- 只问一个问题
- 问题要具体，指向场景中的关键细节
- 语气温和，像督导引导实习生一样"""
```

### 验收标准

```bash
# 1. 学生保存场景描述
POST /learning/scenario/save
{"record_id": 1, "description": "社区张大爷因为经济困难拒绝与人沟通..."}

# 2. AI 分析
POST /learning/scenario/analyze
{"scenario_id": 1}
# 预期：返回 key_events（2-4个关键事件）、identified_problems（2-3个专业问题）

# 3. 检查对话记录
SELECT role, LEFT(content, 100), dialogue_type
FROM edu_scenario_dialogue
WHERE scenario_id = 1;

# 4. 检查 record 的 scenario_id 已回填
SELECT scenario_id FROM edu_learning_record WHERE record_id = 1;
# 预期: scenario_id 不为 NULL
```

---

## 阶段 4：决策区（Decision Zone）

> **目标**：学生在关键事件节点做出伦理决策分析，AI 提供伦理参照
> **预计时间**：3 天
> **交付物**：决策记录 CRUD + AI 伦理分析接口

### 数据表

```sql
-- 决策区主数据表（每个关键事件节点一条记录）
CREATE TABLE edu_decision_data (
    decision_id    BIGSERIAL PRIMARY KEY,
    record_id      BIGINT NOT NULL REFERENCES edu_learning_record(record_id),
    scenario_id    BIGINT NOT NULL REFERENCES edu_scenario_data(scenario_id),
    student_id     BIGINT NOT NULL REFERENCES sys_user(user_id),
    -- 关联的关键事件（来自情境区）
    key_event_index INTEGER CHECK (key_event_index >= 0),   -- 【v2.0: 加 CHECK 约束】
    key_event_desc TEXT,                           -- 冗余存储，方便展示
    -- 学生填写的决策内容
    is_intervened  BOOLEAN,                        -- 是否介入
    action_taken   TEXT,                           -- 具体行动
    reasoning      TEXT,                           -- 行动理由
    psychological_state TEXT,                      -- 心理活动和感受
    alternatives   TEXT,                           -- 考虑的替代方案
    expected_outcome TEXT,                         -- 预期结果
    actual_outcome TEXT,                           -- 实际结果（事后补充）
    -- AI 分析结果
    ethics_analysis JSONB,                         -- AI 伦理分析结果
    -- 状态
    status         CHAR(1) DEFAULT '0',            -- 0草稿 1已完成
    del_flag       CHAR(1) DEFAULT '0',
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 决策区 AI 对话记录
CREATE TABLE edu_decision_dialogue (
    dialogue_id    BIGSERIAL PRIMARY KEY,
    decision_id    BIGINT NOT NULL REFERENCES edu_decision_data(decision_id),
    role           VARCHAR(20) NOT NULL,
    content        TEXT NOT NULL,
    dialogue_type  VARCHAR(30),                    -- ethics_analyze / alternative / followup
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 需要实现的接口

| 接口 | 方法 | 说明 |
|---|---|---|
| `/learning/decision/save` | POST/PUT | 保存决策记录（支持逐字段保存） |
| `/learning/decision/ethics-analyze` | POST | AI 伦理分析：分析决策的伦理维度 |
| `/learning/decision/alternatives` | POST | AI 生成替代决策方案 |
| `/learning/decision/list/{record_id}` | GET | 获取本次学习的所有决策记录 |
| `/learning/decision/confirm/{record_id}` | PUT | 确认所有决策完成，进入反思区 |

### AI 伦理分析的 Prompt

```python
DECISION_ETHICS_PROMPT = """你是一位社会工作伦理专家，正在指导一位实习社工分析其在实践中的伦理决策。

当前关键事件：
{key_event_desc}

学生的决策记录：
- 是否介入：{is_intervened}
- 具体行动：{action_taken}
- 行动理由：{reasoning}
- 心理活动：{psychological_state}

相关伦理知识参考（来自伦理守则知识库）：
{retrieved_ethics_knowledge}

任务：
1. 识别这个决策涉及的伦理维度（如：自决权 vs 保护义务、保密原则等）
2. 引用相关的伦理守则条款
3. 分析这个决策的伦理合理性
4. 提出需要进一步思考的伦理问题

语气要引导性，而非评判性。

输出 JSON 格式：
{{
  "ethics_dimensions": [
    {{"name": "伦理维度名称", "description": "与本决策的关联", "stance": "支持/张力"}}
  ],
  "relevant_codes": [
    {{"code": "守则条款", "source": "来源", "relevance": "关联说明"}}
  ],
  "analysis": "综合伦理分析文本",
  "further_questions": ["需进一步思考的问题1", "问题2"]
}}"""
```

**关键**：决策区的 RAG 检索要**指定伦理守则知识库**（`decision_kb_ids`），不是理论知识库，这样检索到的是伦理条款而不是理论概念。

### confirm 接口的前置校验

```python
# decision_service.py 的 confirm 方法里加校验
async def confirm_decisions(cls, db, record_id, student_id):
    """确认所有决策完成，推进到反思区"""
    # 检查至少有一条决策记录
    decisions = await DecisionDao.get_by_record_id(db, record_id)
    if not decisions:
        raise ValueError("至少需要完成一条决策记录才能进入反思区")

    # 检查关联的情境区是否有 key_events
    scenario = await ScenarioDao.get_by_record_id(db, record_id)
    if scenario and scenario.key_events:
        # 检查是否每个 key_event 都有对应的决策记录
        event_count = len(scenario.key_events)
        if len(decisions) < event_count:
            # 只是警告，不阻止推进
            pass

    # 推进到下一区
    await RecordService.advance_stage(db, record_id, student_id)
```

### 验收标准

```bash
# 决策区的 key_events 来自情境区，先检查情境区的 key_events 是否正确存储
SELECT key_events FROM edu_scenario_data WHERE scenario_id = 1;

# 保存决策记录（一个关键事件节点对应一条决策）
POST /learning/decision/save
{
  "record_id": 1,
  "scenario_id": 1,
  "key_event_index": 0,
  "key_event_desc": "大爷情绪失控，是否要强行介入",
  "is_intervened": true,
  "action_taken": "试图安抚大爷情绪，建议去社区服务中心坐下来谈",
  "reasoning": "不能放任大爷的情绪不管"
}

# AI 伦理分析
POST /learning/decision/ethics-analyze
{"decision_id": 1}
# 预期：返回伦理维度分析，引用具体的伦理守则条款
```

---

## 阶段 5：反思区（Reflection Zone）

> **目标**：AI 三层递进提问引导学生从描述性反思走向反身性反思
> **这是本系统的核心创新模块**
> **预计时间**：4 天
> **交付物**：反思日志 CRUD + AI 三层提问 + 深度评估接口

### 数据表

```sql
-- 反思区主数据表
CREATE TABLE edu_reflection_data (
    reflection_id  BIGSERIAL PRIMARY KEY,
    record_id      BIGINT NOT NULL REFERENCES edu_learning_record(record_id),
    scenario_id    BIGINT NOT NULL REFERENCES edu_scenario_data(scenario_id),
    student_id     BIGINT NOT NULL REFERENCES sys_user(user_id),
    content        TEXT,                           -- 反思文本（持续更新）
    depth_level    VARCHAR(20) DEFAULT 'descriptive', -- descriptive/analytical/reflexive
    depth_score    DECIMAL(3,2) DEFAULT 0.00 CHECK (depth_score >= 0 AND depth_score <= 1.00), -- 【v2.0: 加 CHECK 约束】
    linked_theories JSONB,                         -- AI 关联的专业理论列表
    version        INTEGER DEFAULT 1,              -- 编辑版本号（每次保存+1）
    status         CHAR(1) DEFAULT '0',            -- 0草稿 1已确认
    del_flag       CHAR(1) DEFAULT '0',
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 反思区 AI 对话记录
CREATE TABLE edu_reflection_dialogue (
    dialogue_id    BIGSERIAL PRIMARY KEY,
    reflection_id  BIGINT NOT NULL REFERENCES edu_reflection_data(reflection_id),
    role           VARCHAR(20) NOT NULL,           -- user / assistant
    content        TEXT NOT NULL,
    question_level VARCHAR(20),                    -- descriptive/analytical/reflexive/theory
    depth_score_before DECIMAL(3,2),
    depth_score_after  DECIMAL(3,2),
    linked_theories JSONB,
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 反思深度演变历史（用于绘制深度曲线图）
CREATE TABLE edu_reflection_depth_history (
    history_id     BIGSERIAL PRIMARY KEY,
    reflection_id  BIGINT NOT NULL REFERENCES edu_reflection_data(reflection_id),
    depth_score    DECIMAL(3,2) NOT NULL,
    depth_level    VARCHAR(20) NOT NULL,
    trigger_type   VARCHAR(30),                    -- save（保存触发）/ ai_question（AI提问后）
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 需要实现的接口

| 接口 | 方法 | 说明 |
|---|---|---|
| `/learning/reflection/save` | POST/PUT | 保存反思文本（带防抖的深度评估） |
| `/learning/reflection/questions` | POST | AI 生成结构化提问（核心接口） |
| `/learning/reflection/depth/{reflection_id}` | GET | 获取当前深度评估结果 |
| `/learning/reflection/depth-history/{reflection_id}` | GET | 深度变化曲线数据 |
| `/learning/reflection/detail/{record_id}` | GET | 反思区完整数据（含对话历史） |
| `/learning/reflection/confirm` | PUT | 确认反思完成，进入研究生成区 |

### 反思区 AI 引擎（核心）

这是整个系统技术含量最高的部分。AI 要同时做三件事：
1. 评估反思深度（给分）
2. 根据深度生成下一层的追问
3. 检索匹配的理论概念

```python
# module_learning/service/reflection_ai_engine.py
from module_rag.service.embedding_service import EmbeddingService
from module_rag.service.retrieval_service import RetrievalService
from module_learning.service.llm_service import LlmService


REFLECTION_PROMPT = """你是一位引导反思的社会工作教育者，擅长通过提问帮助学生从"描述经历"走向"反身性反思"。

学生的实践背景：
- 情境描述：{scenario_summary}
- 关键决策：{decision_summary}
- 历史反思记录（最近2次）：{reflection_history}

反思深度评估规则：
- 描述性（0.20-0.40）：仅复述事件经过和个人感受，没有分析为什么
- 分析性（0.41-0.70）：开始分析事件原因、互动模式、策略选择依据
- 反身性（0.71-1.00）：审视自身价值观、立场、权力关系对实践的影响

当前学生的反思文本：
{reflection_text}

相关专业理论参考（来自知识库）：
{retrieved_knowledge}

任务：
1. 评估当前反思的深度（给出分数和等级）
2. 根据当前深度，生成 2-3 个推动反思深化的追问
   - 如果是描述性：从分析性层次出题（引导分析原因和互动）
   - 如果是分析性：从反身性层次出题（引导审视自身立场）
   - 如果是反身性：从理论连接层次出题（引导理论整合）
3. 关联 1-2 个相关的专业理论或概念，说明关联理由

重要原则：
- 追问必须针对学生文本中的具体内容，不要泛泛而谈
- 语气温暖鼓励，而非评判

输出 JSON：
{{
  "depth_score": 0.65,
  "depth_level": "analytical",
  "questions": [
    {{
      "level": "reflexive",
      "question": "具体的追问内容",
      "purpose": "这个问题希望引导学生..."
    }}
  ],
  "theories": [
    {{
      "name": "理论名称",
      "description": "与学生反思内容的具体关联",
      "source": "Solomon, 1976（可选）"
    }}
  ]
}}"""


class ReflectionAiEngine:

    @classmethod
    async def evaluate_and_question(
        cls,
        db,
        reflection,
        task,
        scenario,
        decisions,
        dialogue_history,
    ) -> dict:
        """
        核心方法：评估反思深度 + 生成下一层追问
        """
        # 1. 准备上下文数据
        scenario_summary = cls._summarize_scenario(scenario)
        decision_summary = cls._summarize_decisions(decisions)
        reflection_history = cls._format_history(dialogue_history, last_n=2)

        # 2. RAG 检索：用反思文本检索相关理论
        kb_ids = task.reflection_kb_ids or []
        retrieved_knowledge = ""
        if kb_ids and reflection.content:
            query_embedding = await EmbeddingService.embed_single(reflection.content)
            chunks = await RetrievalService.hybrid_search(
                db=db,
                query_text=reflection.content,
                query_embedding=query_embedding,
                kb_ids=kb_ids,
                top_k=4,
            )
            retrieved_knowledge = "\n\n".join([
                f"【{chunk['content'][:200]}】"
                for chunk in chunks
            ])

        # 3. 构建 Prompt 并调用 LLM
        prompt = REFLECTION_PROMPT.format(
            scenario_summary=scenario_summary,
            decision_summary=decision_summary,
            reflection_history=reflection_history,
            reflection_text=reflection.content or "（学生尚未输入反思内容）",
            retrieved_knowledge=retrieved_knowledge or "（暂无相关理论参考）",
        )

        result = await LlmService.chat_json(prompt, max_tokens=2000)
        return result

    @classmethod
    def _summarize_scenario(cls, scenario) -> str:
        """提取情境摘要（不把整个描述都塞进 Prompt）"""
        if not scenario:
            return "（无情境数据）"
        problems = scenario.identified_problems or []
        problem_titles = [p.get("title", "") for p in problems[:3]]
        return f"场景：{(scenario.description or '')[:200]}...\n核心问题：{', '.join(problem_titles)}"

    @classmethod
    def _summarize_decisions(cls, decisions: list) -> str:
        """提取决策摘要"""
        if not decisions:
            return "（无决策记录）"
        summaries = []
        for d in decisions[:3]:
            summaries.append(
                f"- 节点「{d.key_event_desc[:30]}」："
                f"{'介入' if d.is_intervened else '未介入'}，{(d.action_taken or '')[:50]}"
            )
        return "\n".join(summaries)

    @classmethod
    def _format_history(cls, dialogues, last_n=2) -> str:
        """格式化最近 N 轮对话"""
        if not dialogues:
            return "（无历史对话）"
        recent = dialogues[-last_n:] if len(dialogues) > last_n else dialogues
        lines = []
        for d in recent:
            role = "AI" if d.role == "assistant" else "学生"
            lines.append(f"{role}：{d.content[:100]}")
        return "\n".join(lines)
```

### save 接口的防抖深度评估

每次学生保存反思文本，系统自动计算深度分数并记录历史。但为了控制 LLM 调用成本，采用**防抖策略**：距离上次评估不足 30 秒的保存不触发重新评估。

```python
# module_learning/service/reflection_service.py
from datetime import datetime
from module_learning.service.llm_service import LlmService

EVALUATE_THROTTLE_SECONDS = 30  # 【v2.0: 防抖间隔，避免频繁调 LLM】


class ReflectionService:

    @classmethod
    async def save_and_evaluate(cls, db, reflection_id: int, content: str, student_id: int):
        """
        保存反思文本，带防抖的自动深度评估
        """
        reflection = await ReflectionDao.get_by_id(db, reflection_id)

        # 更新内容
        reflection.content = content
        reflection.version += 1

        # 【v2.0: 防抖检查——距离上次评估不足 30 秒则跳过评估】
        should_evaluate = await cls._should_evaluate(db, reflection_id)
        if should_evaluate:
            depth_result = await cls._quick_depth_evaluate(content)
            reflection.depth_score = depth_result["depth_score"]
            reflection.depth_level = depth_result["depth_level"]

            # 记录深度历史
            await ReflectionDepthHistoryDao.insert(db, {
                "reflection_id": reflection_id,
                "depth_score": depth_result["depth_score"],
                "depth_level": depth_result["depth_level"],
                "trigger_type": "save",
            })

        await db.commit()
        return reflection

    @classmethod
    async def _should_evaluate(cls, db, reflection_id: int) -> bool:
        """检查是否应该触发深度评估（防抖）"""
        last_history = await ReflectionDepthHistoryDao.get_latest(db, reflection_id)
        if not last_history:
            return True  # 从未评估过，必须评估
        elapsed = (datetime.now() - last_history.create_time).total_seconds()
        return elapsed >= EVALUATE_THROTTLE_SECONDS

    @classmethod
    async def _quick_depth_evaluate(cls, content: str) -> dict:
        """
        快速深度评估（只给分，不出题，节省 LLM token）
        """
        QUICK_EVAL_PROMPT = """评估以下反思文本的深度层次，只需输出 JSON，不要其他内容：
- 描述性（0.20-0.40）：只复述经历
- 分析性（0.41-0.70）：分析原因和互动模式
- 反身性（0.71-1.00）：审视自身价值观和权力位置

文本：{text}

输出：{{"depth_score": 0.65, "depth_level": "analytical"}}"""

        result = await LlmService.chat_json(
            QUICK_EVAL_PROMPT.format(text=content[:500]),
            max_tokens=50,
        )
        return result
```

### 验收标准

```bash
# 保存反思文本
POST /learning/reflection/save
{
  "record_id": 1,
  "content": "我觉得这次经历让我意识到社工不是简单地帮助别人。张大爷的拒绝其实也是一种权利表达。"
}
# 预期：返回 depth_score ≈ 0.7, depth_level = "analytical"

# 请求 AI 提问
POST /learning/reflection/questions
{"reflection_id": 1}
# 预期：返回 2-3 个追问，最后一个追问的 level 应该是 "reflexive"（推动到下一层）

# 查看深度演变历史（用于前端画折线图）
GET /learning/reflection/depth-history/1
# 预期：按时间顺序返回多个深度分数记录

# 连续快速保存测试（验证防抖）
# 30秒内连续保存3次，只有第1次触发评估
```

---

## 阶段 6：研究生成区（Research Generation Zone）

> **目标**：AI 帮助学生把前三区的材料转化为研究问题、论文框架和初稿段落
> **预计时间**：3 天
> **交付物**：研究问题生成 + 论文框架 + 章节辅助撰写接口

### 数据表

```sql
-- 研究区主数据表
CREATE TABLE edu_research_data (
    research_id    BIGSERIAL PRIMARY KEY,
    record_id      BIGINT NOT NULL REFERENCES edu_learning_record(record_id),
    student_id     BIGINT NOT NULL REFERENCES sys_user(user_id),
    -- Step 1: 材料汇总（系统自动生成，学生可编辑）
    material_summary TEXT,                         -- 前三区材料的综合摘要
    -- Step 2: 研究问题
    candidate_questions JSONB,                     -- AI 生成的候选研究问题列表
    selected_question TEXT,                        -- 学生选定的研究问题
    -- Step 3: 论文框架
    framework      JSONB,                          -- 论文大纲（嵌套结构）
    -- Step 5: 文献推荐
    references     JSONB,                          -- RAG 检索到的推荐文献
    -- 状态
    status         CHAR(1) DEFAULT '0',            -- 0进行中 1已提交
    del_flag       CHAR(1) DEFAULT '0',
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 【v2.0: 章节独立表，替代 chapter_drafts JSONB 大字段】
-- 原方案把所有章节塞一个 JSONB 字段，前端每次保存一章要整体读写，并发会丢数据
CREATE TABLE edu_research_chapter (
    chapter_id     BIGSERIAL PRIMARY KEY,
    research_id    BIGINT NOT NULL REFERENCES edu_research_data(research_id),
    chapter_index  INTEGER NOT NULL,               -- 章节序号
    chapter_title  VARCHAR(200),                   -- 章节标题
    content        TEXT,                           -- 章节内容
    ai_suggestion  TEXT,                           -- AI 写作建议
    status         CHAR(1) DEFAULT '0',            -- 0草稿 1已完成
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 需要实现的接口

| 接口 | 方法 | 说明 |
|---|---|---|
| `/learning/research/init/{record_id}` | POST | 初始化研究区（汇总前三区材料） |
| `/learning/research/questions` | POST | AI 生成候选研究问题（3-5个） |
| `/learning/research/framework` | POST | AI 基于研究问题生成论文框架 |
| `/learning/research/chapter/save` | PUT | 保存单个章节内容 |
| `/learning/research/chapter/draft` | POST | AI 辅助撰写指定章节 |
| `/learning/research/references` | POST | AI 推荐相关文献 |
| `/learning/research/save` | PUT | 保存研究区基本信息 |
| `/learning/research/submit` | PUT | 提交，流转到 submitted 状态 |

### 研究问题生成的核心逻辑

```python
RESEARCH_QUESTION_PROMPT = """你是一位行动研究方法专家，正在帮助一位社会工作专业的学生，
从其实习经历中凝练研究问题。

学生的实习材料汇总：
情境描述：{scenario_summary}
决策分析：{decision_summary}
反思记录（精华摘录）：{reflection_summary}

相关学术文献参考：
{retrieved_literature}

任务：基于以上材料，生成 3-5 个适合本科生行动研究的候选研究问题。
要求：
- 问题要从学生自身实践中"内生"，有具体性
- 适合行动研究方法论（聚焦过程和意义，而非因果推断）
- 难度适合本科生独立完成
- 每个问题附上选择理由和可能的研究路径

输出 JSON：
{{
  "questions": [
    {{
      "question": "研究问题表述",
      "rationale": "选择理由（与学生材料的关联）",
      "approach": "可能的研究路径（方法论方向）"
    }}
  ]
}}"""
```

### 章节独立保存接口

```python
# module_learning/service/research_service.py

class ResearchService:

    @classmethod
    async def save_chapter(cls, db, research_id: int, chapter_index: int,
                           content: str, student_id: int):
        """
        保存单个章节内容
        【v2.0: 章节独立表，避免 JSONB 大字段的并发问题】
        """
        chapter = await ResearchChapterDao.get_by_index(db, research_id, chapter_index)
        if chapter:
            chapter.content = content
            chapter.update_time = datetime.now()
        else:
            chapter = EduResearchChapter(
                research_id=research_id,
                chapter_index=chapter_index,
                content=content,
            )
            db.add(chapter)
        await db.flush()
        return chapter
```

### 验收标准

```bash
# 初始化研究区（汇总前三区材料）
POST /learning/research/init/1
# 预期：返回 material_summary（自动生成的摘要）

# AI 生成研究问题
POST /learning/research/questions
{"research_id": 1}
# 预期：返回 3-5 个候选研究问题

# AI 生成论文框架
POST /learning/research/framework
{"research_id": 1, "selected_question": "社会工作者在服务对象阻抗情境中的伦理决策过程研究"}
# 预期：返回论文大纲（含章节列表），同时在 edu_research_chapter 创建对应记录

# 保存单个章节
POST /learning/research/chapter/save
{"research_id": 1, "chapter_index": 1, "content": "绪论正文..."}
# 预期：edu_research_chapter 表有对应记录

# AI 辅助撰写章节
POST /learning/research/chapter/draft
{"research_id": 1, "chapter_index": 2}
# 预期：返回该章节的 AI 写作建议和段落草稿
```

---

## 阶段 7：教师监控 + 评价功能

> **目标**：教师可以查看班级学生的学习进度，对提交成果进行评价，管理优秀案例
> **预计时间**：3 天
> **交付物**：班级监控接口 + 评价接口 + 优秀案例库接口

### 数据表

```sql
-- 教师评价表
CREATE TABLE edu_evaluation (
    evaluation_id    BIGSERIAL PRIMARY KEY,
    record_id        BIGINT NOT NULL REFERENCES edu_learning_record(record_id),
    teacher_id       BIGINT NOT NULL REFERENCES sys_user(user_id),
    -- 各区评分
    scenario_score   DECIMAL(5,2),                 -- 情境区分数
    decision_score   DECIMAL(5,2),                 -- 决策区分数
    reflection_score DECIMAL(5,2),                 -- 反思区分数
    research_score   DECIMAL(5,2),                 -- 研究区分数
    total_score      DECIMAL(5,2),                 -- 总分（加权计算）
    -- 评价内容
    scenario_feedback  TEXT,                       -- 情境区评语
    decision_feedback  TEXT,                       -- 决策区评语
    reflection_feedback TEXT,                      -- 反思区评语
    research_feedback  TEXT,                       -- 研究区评语
    overall_feedback   TEXT,                       -- 总评语
    -- 状态
    is_excellent     BOOLEAN DEFAULT FALSE,        -- 是否标记为优秀案例
    status           CHAR(1) DEFAULT '0',          -- 0草稿 1已发布（学生可见）
    create_time      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(record_id)                              -- 一个学习记录只有一条评价
);
COMMENT ON TABLE edu_evaluation IS '教师评价表';

-- 优秀案例库（匿名化，供后续学生参考）
CREATE TABLE edu_excellent_case (
    case_id           BIGSERIAL PRIMARY KEY,
    source_record_id  BIGINT,                      -- 原始记录ID（仅教师可见）
    task_id           BIGINT NOT NULL,
    -- 匿名化后的数据（脱敏处理）
    scenario_desc     TEXT,                        -- 脱敏后的情境描述
    decision_data     JSONB,                       -- 脱敏后的决策记录
    reflection_data   TEXT,                        -- 脱敏后的反思精华
    research_data     TEXT,                        -- 脱敏后的研究成果
    teacher_comment   TEXT,                        -- 教师推荐语
    tags              JSONB,                       -- 案例标签
    -- 状态
    status            CHAR(1) DEFAULT '0',         -- 0待审核 1已发布 2已下架
    create_time       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE edu_excellent_case IS '优秀案例库（匿名化）';
```

### 需要实现的接口

| 接口 | 方法 | 权限 | 说明 |
|---|---|---|---|
| `/learning/monitor/class/{task_id}` | GET | teacher | 班级进度概览 |
| `/learning/monitor/student/{record_id}` | GET | teacher | 单个学生完整学习过程详情 |
| `/learning/monitor/statistics/{task_id}` | GET | teacher | 班级统计数据（各区平均分、深度分布等） |
| `/learning/evaluation/submit` | POST | teacher | 提交评价（评分+评语） |
| `/learning/evaluation/update` | PUT | teacher | 修改评价 |
| `/learning/evaluation/detail/{record_id}` | GET | student/teacher | 查看评价（学生只能看自己的） |
| `/learning/case/mark-excellent/{record_id}` | PUT | teacher | 标记为优秀案例（触发匿名化入库） |
| `/learning/case/list` | GET | all | 获取优秀案例列表（匿名化，学生可看） |
| `/learning/case/detail/{case_id}` | GET | all | 获取单个优秀案例详情 |

### 班级进度概览接口的核心逻辑

```python
# module_learning/service/monitor_service.py

class MonitorService:

    @classmethod
    async def get_class_overview(cls, db, task_id: int, teacher_id: int) -> dict:
        """
        班级进度概览
        返回：每个学生在哪个区、各区完成率、反思深度分数等
        """
        # 1. 查询该任务的所有学习记录
        records = await RecordDao.get_by_task_id(db, task_id)

        # 2. 统计
        total = len(records)
        stage_counts = {
            "scenario": 0, "decision": 0, "reflection": 0,
            "research": 0, "submitted": 0, "completed": 0,
        }
        student_progress = []

        for record in records:
            stage_counts[record.current_stage] = stage_counts.get(record.current_stage, 0) + 1
            student_progress.append({
                "record_id": record.record_id,
                "student_name": record.student.name if hasattr(record, 'student') else "未知",
                "current_stage": record.current_stage,
                "scenario_status": record.scenario_status,
                "decision_status": record.decision_status,
                "reflection_status": record.reflection_status,
                "research_status": record.research_status,
                "reflection_depth": None,  # 需要额外查
                "submit_time": str(record.submit_time) if record.submit_time else None,
            })

        return {
            "task_id": task_id,
            "total_students": total,
            "stage_distribution": stage_counts,
            "completion_rate": {
                "scenario": f"{sum(1 for r in records if r.scenario_status == '2')}/{total}",
                "decision": f"{sum(1 for r in records if r.decision_status == '2')}/{total}",
                "reflection": f"{sum(1 for r in records if r.reflection_status == '2')}/{total}",
                "research": f"{sum(1 for r in records if r.research_status == '2')}/{total}",
            },
            "students": student_progress,
        }
```

### 评价提交接口

```python
# module_learning/service/evaluation_service.py

class EvaluationService:

    @classmethod
    async def submit(cls, db, data, teacher_id: int):
        """教师提交评价"""
        # 检查学习记录是否已提交
        record = await RecordDao.get_by_id(db, data.record_id)
        if record.status not in ("submitted", "completed"):
            raise ValueError("学生尚未提交，无法评价")

        # 计算总分（可配置权重）
        total = (
            (data.scenario_score or 0) * 0.2 +
            (data.decision_score or 0) * 0.2 +
            (data.reflection_score or 0) * 0.3 +
            (data.research_score or 0) * 0.3
        )

        evaluation = EduEvaluation(
            record_id=data.record_id,
            teacher_id=teacher_id,
            scenario_score=data.scenario_score,
            decision_score=data.decision_score,
            reflection_score=data.reflection_score,
            research_score=data.research_score,
            total_score=total,
            scenario_feedback=data.scenario_feedback,
            decision_feedback=data.decision_feedback,
            reflection_feedback=data.reflection_feedback,
            research_feedback=data.research_feedback,
            overall_feedback=data.overall_feedback,
        )
        db.add(evaluation)

        # 更新学习记录状态
        record.status = "completed"
        record.score = total
        record.teacher_feedback = data.overall_feedback
        record.complete_time = datetime.now()

        await db.flush()
        return evaluation

    @classmethod
    async def mark_excellent(cls, db, record_id: int, teacher_id: int):
        """标记为优秀案例，触发匿名化入库"""
        # 1. 获取完整数据
        record = await RecordDao.get_by_id(db, record_id)
        scenario = await ScenarioDao.get_by_record_id(db, record_id)
        decisions = await DecisionDao.get_by_record_id(db, record_id)
        reflection = await ReflectionDao.get_by_record_id(db, record_id)
        research = await ResearchDao.get_by_record_id(db, record_id)

        # 2. 匿名化处理（去除学生姓名等敏感信息）
        case = EduExcellentCase(
            source_record_id=record_id,
            task_id=record.task_id,
            scenario_desc=cls._anonymize(scenario.description if scenario else ""),
            decision_data=cls._anonymize_decisions(decisions),
            reflection_data=cls._anonymize(reflection.content if reflection else ""),
            research_data=cls._anonymize(research.selected_question if research else ""),
            tags=scenario.category_tags if scenario else [],
        )
        db.add(case)

        # 3. 标记评价
        evaluation = await EvaluationDao.get_by_record_id(db, record_id)
        if evaluation:
            evaluation.is_excellent = True

        await db.flush()
        return case

    @classmethod
    def _anonymize(cls, text: str) -> str:
        """简单匿名化：去除人名替换为 XX"""
        import re
        # 替换常见人名模式（张三→张X，李大爷→X大爷）
        text = re.sub(r'[一-鿿]{1}[大爷叔阿姨哥姐妹妹弟弟]', lambda m: 'X' + m.group(0)[1:], text)
        return text
```

### 验收标准

```bash
# 教师查看班级进度
GET /learning/monitor/class/1
# 预期：返回各阶段人数分布、各区完成率、每个学生的当前状态

# 教师查看学生详情
GET /learning/monitor/student/1
# 预期：返回该学生的情境描述、所有决策记录、反思日志（含深度曲线）、研究成果

# 教师提交评价
POST /learning/evaluation/submit
{
  "record_id": 1,
  "scenario_score": 85,
  "decision_score": 80,
  "reflection_score": 90,
  "research_score": 75,
  "reflection_feedback": "反思深度达到反身性层次，有很好的自我觉察能力",
  "overall_feedback": "整体表现优秀，反思部分尤其突出"
}
# 预期：edu_evaluation 有记录，record 的 status 变为 completed

# 标记优秀案例
PUT /learning/case/mark-excellent/1
# 预期：edu_excellent_case 有记录（匿名化），evaluation 的 is_excellent = true

# 学生查看评价
GET /learning/evaluation/detail/1
# 预期：返回教师评分和评语

# 任何人查看优秀案例列表
GET /learning/case/list
# 预期：返回匿名化的优秀案例列表
```

---

## 阶段 8：前端页面开发

> **与后端并行开发**，后端出接口文档（FastAPI 的 `/docs` 自动生成）后前端即可开始

### 前端目录结构（在现有 RuoYiFast Vue 项目里新建）

```
src/views/learning/
├── task/
│   ├── StudentTaskList.vue          # 学生任务列表
│   └── TeacherTaskManager.vue       # 教师任务管理
├── scenario/
│   ├── index.vue                    # 情境区主页面
│   └── components/
│       ├── ScenarioEditor.vue       # 富文本编辑器
│       ├── KeyEventTimeline.vue     # 关键事件时间轴
│       ├── AiFollowupPanel.vue      # AI 追问面板（SSE 流式）
│       └── ProblemCard.vue          # 问题识别卡片
├── decision/
│   ├── index.vue                    # 决策区主页面
│   └── components/
│       ├── DecisionForm.vue         # 决策记录表单
│       ├── EthicsPanel.vue          # 伦理分析面板（SSE 流式）
│       └── AlternativeView.vue      # 替代方案对比
├── reflection/
│   ├── index.vue                    # 反思区主页面（最复杂）
│   └── components/
│       ├── ReflectionEditor.vue     # 反思日志编辑器（自动保存）
│       ├── AiQuestionPanel.vue      # AI 提问引导栏
│       ├── TheoryLinkage.vue        # 理论关联面板
│       ├── DepthIndicator.vue       # 深度指示器（进度条）
│       └── DepthChart.vue           # 深度演变折线图（ECharts）
├── research/
│   ├── index.vue                    # 研究生成区主页面
│   └── components/
│       ├── MaterialSummary.vue      # 材料汇总展示
│       ├── QuestionSelector.vue     # 研究问题选择器
│       ├── FrameworkEditor.vue      # 论文框架拖拽编辑
│       └── ChapterEditor.vue        # 章节编辑器（每个章节独立编辑）
├── monitor/
│   ├── ClassOverview.vue            # 班级进度监控
│   ├── StudentDetail.vue            # 学生详情查看
│   └── EvaluationForm.vue           # 评价表单
├── case/
│   └── CaseList.vue                 # 优秀案例列表
└── components/
    ├── ZoneNavigator.vue            # 四区导航组件（顶部步骤条）
    ├── AiChatPanel.vue              # 通用 AI 对话面板（SSE 流式）
    └── AutoSaveMixin.js             # 自动保存混入（30秒/失焦时触发）
```

### SSE 流式输出对接方案（新增）

AI 回复需要流式展示，不能让用户等 10 秒才看到完整回复。后端需要增加 SSE 端点：

```python
# 后端：以情境区追问为例
from fastapi.responses import StreamingResponse

@scenario_controller.post('/followup-stream', summary='AI 追问（流式）')
async def followup_stream(data: FollowupRequest, query_db: ...):
    async def generate():
        async for chunk in LlmService.chat_stream(prompt):
            yield f"data: {json.dumps({'content': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

```javascript
// 前端：AiFollowupPanel.vue 中的 SSE 对接
const eventSource = new EventSource('/learning/scenario/followup-stream', {
  // 注意：POST 请求的 SSE 需要用 fetch + ReadableStream
})

// 推荐：用 fetch API 实现 POST SSE
async function streamAiResponse(question) {
  const response = await fetch('/learning/scenario/followup-stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
    body: JSON.stringify({ scenario_id: currentScenarioId })
  })
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    // 解析 SSE 数据...
    const lines = buffer.split('\n')
    for (const line of lines) {
      if (line.startsWith('data: ') && line !== 'data: [DONE]') {
        const data = JSON.parse(line.slice(6))
        aiResponseText.value += data.content
      }
    }
  }
}
```

### 自动保存机制（新增）

反思区和研究区编辑器需要自动保存，防止丢失。

```javascript
// AutoSaveMixin.js
export const autoSaveMixin = {
  data() {
    return {
      autoSaveTimer: null,
      lastSaveTime: 0,
      hasUnsavedChanges: false,
    }
  },
  methods: {
    startAutoSave(saveFn, intervalMs = 30000) {
      // 定时保存（每 30 秒）
      this.autoSaveTimer = setInterval(() => {
        if (this.hasUnsavedChanges) {
          this.doSave(saveFn)
        }
      }, intervalMs)
    },
    // 失焦时保存
    onBlurSave(saveFn) {
      if (this.hasUnsavedChanges) {
        this.doSave(saveFn)
      }
    },
    async doSave(saveFn) {
      try {
        await saveFn()
        this.hasUnsavedChanges = false
        this.lastSaveTime = Date.now()
      } catch (e) {
        console.error('自动保存失败:', e)
      }
    },
  },
  beforeUnmount() {
    if (this.autoSaveTimer) {
      clearInterval(this.autoSaveTimer)
    }
  },
}
```

### 四区导航组件（新增）

```
┌──────────────────────────────────────────────────────────┐
│  ① 情境区 ──── ② 决策区 ──── ③ 反思区 ──── ④ 研究生成区  │
│  ✅ 已完成      ✅ 已完成     🟡 进行中      ○ 未开始     │
└──────────────────────────────────────────────────────────┘
```

- 学生可以点击已完成的区回溯查看和编辑
- 当前区的按钮高亮，未解锁的区灰色不可点击
- 数据变更后自动同步到后端

### 反思区前端布局（最关键的页面）

```
┌────────────────────────────────────────────────────┐
│  任务：XXX  当前阶段：反思日志 [3/4]   [返回][下一步] │
├────────────────────────────────────────────────────┤
│  反思深度：████████████░░  0.65 (分析性)             │
│  深度曲线：[折线图，显示每次保存后的深度变化]           │
├──────────────────────┬─────────────────────────────┤
│                      │                             │
│   反思日志编辑器       │  AI 提问引导栏              │
│   (富文本，自动保存)   │                             │
│                      │  ▶ 当前层次：分析性           │
│   "我觉得这次经历     │                             │
│    让我意识到..."     │  📌 第1个追问                │
│                      │   你提到'好意可能是控制'——   │
│                      │   这是在哪个瞬间意识到的？     │
│                      │                             │
│   [点击这里开始写     │  📌 第2个追问                │
│    或继续编辑...]     │   如果你是张大爷，你希望社工  │
│                      │   如何对待你？               │
│                      │                             │
│                      │  ─────────────────          │
│                      │  🔖 相关理论                │
│                      │  · 赋权理论（Solomon）       │
│                      │  · 反压迫实践（Dominelli）   │
│                      │                             │
│                      │  [请 AI 出新问题]  [换一组]  │
└──────────────────────┴─────────────────────────────┘
```

---

## 关键：各区之间的数据流向

```
edu_task（任务配置，含各区 kb_ids）
    ↓
edu_learning_record（学生+任务的主控记录，含状态机和四区外键）
    ↓  scenario_id
edu_scenario_data（情境描述 + AI 识别结果）
    ↓    ← 情境区的 key_events 作为输入
edu_decision_data（每个关键事件一条决策记录）
    ↓    ← 情境+决策的摘要作为反思区的背景
edu_reflection_data（反思文本 + 深度评估）
    ↓    ← 情境+决策+反思的全部材料作为输入
edu_research_data + edu_research_chapter（研究问题 + 论文框架 + 各章节）
    ↓
edu_evaluation（教师评价）
```

每个区的 AI 调用，统一模式：

```python
# 所有区的 AI 调用都遵循这个模式
async def ai_call(区的数据, task):
    # 1. 从 task.{区}_kb_ids 拿知识库 ID
    kb_ids = task.reflection_kb_ids  # 以反思区为例

    # 2. RAG 检索
    embedding = await EmbeddingService.embed_single(用户输入文本)
    chunks = await RetrievalService.hybrid_search(db, 用户输入, embedding, kb_ids, top_k=5)

    # 3. 注入 Prompt
    prompt = PROMPT_TEMPLATE.format(retrieved_knowledge=format_chunks(chunks), ...)

    # 4. 调用 LLM（使用阶段 0.5 封装的 LlmService）
    result = await LlmService.chat_json(prompt)
    return result
```

---

## 完整开发 Checklist

### 阶段 0：知识库数据初始化
- [ ] 运行 RAG 模块冒烟测试（parser → chunker → embedding 管道通畅）
- [ ] 验证 module_rag 接口可用（创建知识库、上传文档）
- [ ] 准备至少 3-5 份社会工作专业文档
- [ ] 上传文档，确认 rag_chunk 表有向量化数据
- [ ] 运行检索测试，验证检索结果相关性
- [ ] 建立「伦理守则」和「理论知识」两个独立知识库

### 阶段 0.5：封装统一 LLM 调用层（新增）
- [ ] 实现 `llm_json_parser.py`（兼容各种 LLM JSON 输出格式）
- [ ] 实现 `llm_service.py`（统一 LLM 调用 + 重试 + 超时）
- [ ] 配置 `.env.test` 中的 LLM 环境变量
- [ ] 验收：`LlmService.chat_json()` 正常返回 dict

### 阶段 1：教学任务管理
- [ ] 建表：`edu_task`, `edu_task_class`
- [ ] 实现 ORM / DAO / Service / Controller
- [ ] 实现教师创建任务（含知识库配置）
- [ ] 实现任务发布到班级
- [ ] 实现学生查看任务列表
- [ ] 实现任务复制和逻辑删除接口

### 阶段 2：学习记录状态机
- [ ] 建表：`edu_learning_record`（含四区外键字段）
- [ ] 实现学生开始任务接口（创建 record）
- [ ] 实现 `advance_stage` 状态流转逻辑（含前置校验）
- [ ] 实现教师查看班级进度接口

### 阶段 3：情境区
- [ ] 建表：`edu_scenario_data`, `edu_scenario_dialogue`
- [ ] 实现情境保存接口（回填 record.scenario_id）
- [ ] 实现 AI 首次分析接口（RAG + LlmService）
- [ ] 实现 AI 追问接口
- [ ] 实现确认进入决策区接口

### 阶段 4：决策区
- [ ] 建表：`edu_decision_data`, `edu_decision_dialogue`
- [ ] 实现决策记录保存（逐字段支持）
- [ ] 实现 AI 伦理分析接口（指定伦理守则知识库）
- [ ] 实现 AI 替代方案生成接口
- [ ] 实现确认进入反思区接口（校验至少有一条决策记录）

### 阶段 5：反思区
- [ ] 建表：`edu_reflection_data`, `edu_reflection_dialogue`, `edu_reflection_depth_history`
- [ ] 实现反思保存 + 防抖自动深度评估（30 秒间隔）
- [ ] 实现 AI 三层递进提问接口（核心）
- [ ] 实现深度历史记录
- [ ] 实现深度曲线数据接口
- [ ] 实现确认进入研究区接口

### 阶段 6：研究生成区
- [ ] 建表：`edu_research_data`, `edu_research_chapter`
- [ ] 实现材料汇总接口（自动聚合前三区数据）
- [ ] 实现 AI 研究问题生成（3-5 个候选）
- [ ] 实现 AI 论文框架生成（自动创建章节记录）
- [ ] 实现 AI 章节辅助撰写
- [ ] 实现文献推荐接口（RAG 检索）
- [ ] 实现章节独立保存接口
- [ ] 实现提交接口

### 阶段 7：教师功能
- [ ] 建表：`edu_evaluation`, `edu_excellent_case`
- [ ] 实现班级进度概览接口
- [ ] 实现班级统计数据接口
- [ ] 实现单个学生详情查看接口
- [ ] 实现教师评分+反馈接口（含加权总分计算）
- [ ] 实现标记优秀案例接口（含匿名化处理）
- [ ] 实现优秀案例列表/详情接口（匿名化，学生可看）
- [ ] 实现学生查看评价接口

### 阶段 8：前端页面
- [ ] 四区导航组件（ZoneNavigator.vue）
- [ ] 通用 AI 对话面板（AiChatPanel.vue，SSE 流式）
- [ ] 自动保存混入（AutoSaveMixin.js）
- [ ] 学生任务列表页
- [ ] 情境区页面（编辑器 + AI 追问面板 + 关键事件时间轴）
- [ ] 决策区页面（结构化表单 + 伦理分析面板）
- [ ] 反思区页面（编辑器 + AI 提问栏 + 理论面板 + 深度图表）
- [ ] 研究生成区页面（材料汇总 + 框架编辑 + 章节写作）
- [ ] 教师监控页面（班级概览 + 学生详情）
- [ ] 教师评价页面
- [ ] 优秀案例展示页面

---

## 跨模块注意事项

### 1. LLM 返回格式不稳定

所有 AI 接口都期望 LLM 返回 JSON，但大模型偶尔返回带 markdown 代码块或不合法 JSON。
已在阶段 0.5 中通过 `llm_json_parser.py` 统一处理。

### 2. module_ai 和 module_learning 的 AI 调用要统一

- `module_ai`（已有的聊天模块）→ 直接面向用户的 AI 对话，流式输出
- `module_learning`（新模块）→ 后台调用 LLM 做 RAG + 分析，非流式 JSON 输出

两者底层 API 配置相同（API Key、模型名），但调用方式不同。通过 `LlmService` 统一管理。

### 3. 事务管理注意

各区的 Service 方法涉及多表操作（主数据 + 对话记录 + 学习记录回填），需要确保：
- 所有写操作在同一个 `db` session 中
- 出错时整体回滚，不产生脏数据
- 推荐在 Controller 层用 `try/except` 包裹，失败时 `await db.rollback()`

### 4. 权限控制要点

| 角色 | 可访问的接口 |
|---|---|
| 学生 | `/learning/task/student/*`, `/learning/record/my`, `/learning/scenario/*`, `/learning/decision/*`, `/learning/reflection/*`, `/learning/research/*`, `/learning/evaluation/detail/*`（只看自己的） |
| 教师 | `/learning/task/*`（教师端）, `/learning/monitor/*`, `/learning/evaluation/*`, `/learning/case/*` |
| 管理员 | 所有接口 |

使用 RuoYiFast 的 `PreAuthDependency()` + 权限标识符实现。

---

*文档版本 v2.0 | 修订日期 2026-06-03 | 修复内容：数据类型、补全教师功能、新增 LLM 封装层、新增 SSE 和自动保存方案*
