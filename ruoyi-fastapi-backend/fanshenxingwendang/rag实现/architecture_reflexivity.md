# 反身性学习闭环系统 — 架构方案

| 项目信息 | |
|---|---|
| 文档版本 | v1.0 |
| 编写日期 | 2026年5月28日 |
| 基础框架 | RuoYi-Vue3-FastAPI |
| 模块定位 | 四区联动之反思区（核心创新模块） |

---

## 一、项目现状诊断

| 已完成 | 未完成 |
|--------|--------|
| RuoYiFast 框架运行正常 | 无 Alembic 迁移记录 |
| 角色体系 ORM 已建（`module_admin/entity/do/edu_do.py` 有 Student/Teacher/Audit 三个模型） | 无 `module_rag/`、`module_learning/` 目录 |
| AI 对话模块可用（基于 agno 框架的 `_build_agent` + SSE 流式输出） | `requirements-pg.txt` 无 pgvector/langchain 等依赖 |
| 注册审核代码（后端 controller/service） | 四区联动代码为零 |

**结论：项目处于 Phase 1.1 中期，角色体系 ORM 已建但未迁移到数据库，RAG 和四区功能完全未动。**

---

## 二、模块定位

反身性模块是整个系统的**核心创新点**，位于四区联动的第三区（反思区），但它的实现依赖前序三层的完整支撑：

```
知识库（RAG）→ 情境区 → 决策区 → 【反思区（核心）】→ 研究生成区
```

建设优先级：

1. **先做 RAG 知识库基础设施**（没有知识检索，AI 就是空壳）
2. **再做情境区 + 决策区**（为反思区提供输入数据）
3. **然后做反思区**（反身性核心）
4. **最后做研究生成区**（消费前三区的产出）

---

## 三、核心功能

| 功能 | 优先级 | 说明 |
|------|--------|------|
| 反思日志撰写 | P0 | 学生在富文本编辑器中撰写反思文本 |
| AI 三层递进提问 | P0 | 描述性→分析性→反身性→理论连接，四层问题链 |
| 反思深度自动评估 | P0 | AI 分析当前文本深度，给出分数和等级 |
| 深度演变追踪 | P1 | 可视化展示学生多轮反思的深度变化曲线 |
| 理论关联推荐 | P1 | RAG 检索并推送相关社会工作理论 |
| 历史反思参考 | P2 | 匿名化的历史优秀反思片段 |

---

## 四、数据表规划

### 4.1 反思区前置表（需先存在）

以下表在反思区之前需要创建（属于情境区和决策区）：

- `edu_task` — 教学任务表
- `edu_task_class` — 任务-班级关联表
- `edu_learning_record` — 学习记录主表（四区联动核心）
- `edu_scenario_data` — 情境区数据表
- `edu_scenario_dialogue` — 情境区AI对话记录表
- `edu_decision_data` — 决策区数据表
- `edu_decision_dialogue` — 决策区AI对话记录表

详细建表 SQL 见 `process_ruoyi.md` Phase 1.3 和 Phase 1.4。

### 4.2 反思区核心表

#### 表 1: `edu_reflection_data` — 反思数据主表

```sql
CREATE TABLE edu_reflection_data (
    reflection_id  BIGSERIAL PRIMARY KEY,
    record_id      BIGINT NOT NULL REFERENCES edu_learning_record(record_id),
    scenario_id    BIGINT NOT NULL REFERENCES edu_scenario_data(scenario_id),
    student_id     BIGINT NOT NULL REFERENCES sys_user(user_id),
    content        TEXT,                              -- 反思文本内容
    depth_level    VARCHAR(20) DEFAULT 'descriptive', -- descriptive/analytical/reflexive
    depth_score    DECIMAL(3,2) DEFAULT 0.00,         -- 深度评分 0.00-1.00
    linked_theories JSONB,                           -- 关联的专业理论
    version        INTEGER DEFAULT 1,                 -- 迭代版本号
    status         CHAR(1) DEFAULT '0',               -- 0草稿 1已确认
    del_flag       CHAR(1) DEFAULT '0',               -- 删除标志（0存在 1删除）
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE edu_reflection_data IS '反思区数据表';
```

#### 表 2: `edu_reflection_dialogue` — 反思区AI对话记录表

```sql
CREATE TABLE edu_reflection_dialogue (
    dialogue_id    BIGSERIAL PRIMARY KEY,
    reflection_id  BIGINT NOT NULL REFERENCES edu_reflection_data(reflection_id),
    role           VARCHAR(20) NOT NULL,              -- user / assistant
    content        TEXT NOT NULL,
    question_level VARCHAR(20),                       -- descriptive/analytical/reflexive/theory
    depth_score_before DECIMAL(3,2),                  -- 回答前深度评分
    depth_score_after  DECIMAL(3,2),                  -- 回答后深度评分
    linked_theories JSONB,                            -- 本轮关联的理论
    token_count    INTEGER,
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE edu_reflection_dialogue IS '反思区AI对话记录表';
```

#### 表 3: `edu_reflection_depth_history` — 深度演变记录表

```sql
CREATE TABLE edu_reflection_depth_history (
    history_id     BIGSERIAL PRIMARY KEY,
    reflection_id  BIGINT NOT NULL REFERENCES edu_reflection_data(reflection_id),
    depth_score    DECIMAL(3,2) NOT NULL,
    depth_level    VARCHAR(20) NOT NULL,
    trigger_type   VARCHAR(30),                       -- auto_check/ai_question/student_edit
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE edu_reflection_depth_history IS '反思深度演变记录表';
```

---

## 五、接口规划

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/learning/reflection/create` | 创建反思记录 | student |
| PUT | `/learning/reflection/update` | 更新反思内容 | student |
| POST | `/learning/reflection/questions` | AI生成结构化提问 | student |
| GET | `/learning/reflection/depth/{id}` | 获取反思深度评估 | student/teacher |
| GET | `/learning/reflection/depth-history/{id}` | 深度变化曲线数据 | student/teacher |
| PUT | `/learning/reflection/confirm` | 确认反思完成，流转到研究区 | student |
| GET | `/learning/reflection/detail/{id}` | 反思详情（教师查看） | teacher |

---

## 六、反身性核心逻辑 — AI 三层递进提问策略

### 6.1 提问引擎流程

```
┌─────────────────────────────────────────────────────────┐
│                    AI 提问引擎流程                         │
│                                                          │
│  输入：学生反思文本 + 情境描述 + 决策记录 + 历史反思        │
│                                                          │
│  Step 1: 深度评估                                        │
│    AI 判断当前文本处于哪个层次 → 输出 depth_score          │
│                                                          │
│  Step 2: 根据层次生成追问                                  │
│    if depth < 0.40 (描述性):                              │
│      → 从分析性层次出题（引导分析原因和互动）               │
│    if depth 0.40-0.70 (分析性):                           │
│      → 从反身性层次出题（引导审视自身立场）                 │
│    if depth > 0.70 (反身性):                              │
│      → 理论连接提问 + 巩固深化                             │
│                                                          │
│  Step 3: RAG 检索理论支撑                                 │
│    用反思文本 → 向量检索知识库 → 返回相关理论片段          │
│                                                          │
│  输出：depth_score + 2-3个追问 + 关联理论 + 建议方向       │
└─────────────────────────────────────────────────────────┘
```

### 6.2 深度评分标准

| 等级 | 分数区间 | 判定特征 |
|------|----------|----------|
| 描述性 | 0.20 - 0.40 | 复述事件经过、描述感受、不涉及原因 |
| 分析性 | 0.50 - 0.70 | 分析原因、互动模式、策略选择依据 |
| 反身性 | 0.80 - 1.00 | 审视自身价值观、权力位置、专业角色 |

### 6.3 提问示例

**第一层：描述性提问（还原事件）**

- "当时张大爷说了什么？你的第一反应是什么？"
- "你注意到情境中有哪些细节？"

**第二层：分析性提问（理解互动）**

- "你认为张大爷拒绝沟通的背后可能有什么原因？"
- "你的紧张情绪是否影响了你的沟通方式？"
- "在这个互动中，你的角色期望是什么？"

**第三层：反身性提问（审视自身）**

- "你的介入决策是否受到了你自身价值观的影响？"
- "如果你是张大爷，你希望社工如何对待你？"
- "这次经历如何改变了你对'专业帮助'的理解？"

**第四层：理论连接提问（知识整合）**

- "你所描述的这种现象，与社会学中的XX理论有什么关联？"
- "从XX视角来看，你如何重新理解这个情境？"

---

## 七、AI Prompt 设计

```python
REFLECTION_SYSTEM_PROMPT = """你是一位引导反思的社会工作教育者，擅长通过提问帮助学生从"描述经历"走向"反身性反思"。

当前学生信息：
- 实践情境：{scenario_summary}
- 决策记录：{decision_summary}
- 历史反思：{reflection_history}
- 当前反思深度：{current_depth_level}（{current_depth_score}）

反思深度评估规则：
- 描述性（0.2-0.4）：仅复述事件经过和个人感受
- 分析性（0.5-0.7）：分析事件原因、互动模式、策略选择
- 反身性（0.8-1.0）：审视自身价值观、立场、权力关系对实践的影响

任务：
1. 评估学生当前反思所处的层次（给出分数和等级）
2. 基于当前层次，生成2-3个推动反思深化的追问
3. 关联1-2个相关的社会工作理论或社会学概念
4. 提供理论依据说明为什么这种关联成立

专业知识参考：
{retrieved_knowledge}

重要原则：
- 追问必须针对学生文本中的具体内容，不要泛泛而谈
- 每个追问都有明确目标——推动学生进入更深一层的反思
- 语气要温暖鼓励，而非评判
- 避免一次性给出过多理论

输出JSON格式：
{
  "depth_score": 0.65,
  "depth_level": "analytical",
  "questions": [
    {
      "level": "reflexive",
      "question": "你的介入决策是否受到了你自身价值观的影响？具体是哪些价值观？",
      "purpose": "引导学生审视自身立场"
    }
  ],
  "theories": [
    {
      "name": "赋权理论",
      "description": "你意识到服务对象的'拒绝'是一种权利表达...",
      "source": "Solomon, 1976"
    }
  ]
}
"""
```

---

## 八、技术实现架构 — 复用若依 AI 模块

关键原则：**不要重写 AI 对话机制，而是封装 `AiChatService._build_agent()`**

### 8.1 模块结构

```
module_learning/
├── controller/
│   ├── reflection_controller.py      # 反思区API
│   └── ...
├── dao/
│   ├── reflection_dao.py
│   └── ...
├── entity/
│   ├── do/
│   │   └── reflection_do.py          # 反思区ORM模型
│   └── vo/
│       └── reflection_vo.py          # Pydantic模型
└── service/
    ├── ai_engine.py                  # 核心：封装 AiChatService，注入反思区专用Prompt
    ├── reflection_service.py         # 反思区业务逻辑
    └── ...
```

### 8.2 ai_engine.py 核心代码思路

```python
from module_ai.service.ai_chat_service import AiChatService

class ReflectionAiEngine:
    @classmethod
    async def evaluate_and_question(cls, db, reflection_text, scenario, decisions, history):
        # 1. RAG 检索：用反思文本 → 检索知识库 → 得到理论片段
        retrieved = await RetrievalService.search(reflection_text, top_k=5)

        # 2. 构建 Prompt
        system_prompt = REFLECTION_SYSTEM_PROMPT.format(
            scenario_summary=scenario,
            decision_summary=decisions,
            reflection_history=history,
            current_depth_level="待评估",
            current_depth_score="待评估",
            retrieved_knowledge=retrieved
        )

        # 3. 复用若依 Agent 构建
        agent = AiChatService._build_agent(
            model_config=model_config,
            temperature=0.3,
            system_prompt=system_prompt,
            user_id=student_id,
            session_id=session_id,
            add_history=True,
            num_history=3,
        )

        # 4. 执行 → 返回 JSON 结果
        result = await agent.arun(reflection_text, stream=False)
        return json.loads(result.content)
```

### 8.3 前端页面布局

```
src/views/learning/
├── reflection/
│   ├── index.vue                       # 反思区主页面
│   └── components/
│       ├── ReflectionEditor.vue        # 反思日志编辑器
│       ├── AIQuestionPanel.vue         # AI提问引导栏
│       ├── TheoryLinkage.vue           # 理论关联面板
│       ├── DepthIndicator.vue          # 反思深度指示器
│       └── DepthChart.vue              # 深度演变曲线图（ECharts）
```

```
反思区页面布局：
┌─────────────────────────────────────────────────────┐
│  学习任务：XXX    当前阶段：反思日志 [3/4]             │
├─────────────────────────────────────────────────────┤
│  反思深度：████████████░░░░░░ 0.65 (分析性)          │
│  演变曲线： ↗ ___/‾‾‾ （ECharts折线图）              │
├──────────────────────────┬──────────────────────────┤
│                          │                          │
│   反思日志编辑器          │   AI 提问引导栏            │
│   （大型富文本编辑区）     │                          │
│                          │   ▶ 描述性提问             │
│   "我觉得这次经历让我     │     · 当时大爷说了什么？   │
│    意识到社工不是简单      │                          │
│    地帮助别人..."         │   ▶ 分析性提问             │
│                          │     · 你的紧张情绪是否     │
│                          │       影响了沟通方式？     │
│                          │                          │
│                          │   ▶ 反身性提问             │
│   [AI生成追问]            │     · 你的介入决策是否     │
│                          │       受自身价值观影响？   │
├──────────────────────────┼──────────────────────────┤
│                          │   理论关联：               │
│                          │   ▸ 赋权理论              │
│                          │   ▸ 反压迫实践            │
│                          │                          │
│                          │   [推送追问] [换一组问题]    │
├──────────────────────────┴──────────────────────────┤
│  [← 返回决策区]  [保存草稿]  [确认，进入研究生成区 →]   │
└─────────────────────────────────────────────────────┘
```

---

## 九、开发任务拆解（细粒度）

按必须的执行顺序排列。

### 阶段 0: 前置基础（必须先做完）

| # | 任务 | 依赖 | 涉及文件 | 预计 |
|---|------|------|----------|------|
| 0.1 | 安装 RAG 依赖：pgvector, langchain, PyMuPDF, python-docx, zhipuai | 无 | requirements-pg.txt | 0.5天 |
| 0.2 | 启用 PgVector 扩展 + Alembic 初始化 | 0.1 | alembic/ | 0.5天 |
| 0.3 | 执行已有 edu_* 表的数据库迁移 | 0.2 | alembic/versions/ | 0.5天 |
| 0.4 | 创建 `module_rag/` 模块骨架 | 0.1 | module_rag/ | 1天 |
| 0.5 | 实现文档上传→解析→分块→向量化 Pipeline | 0.4 | module_rag/service/ | 3天 |
| 0.6 | 实现 PgVector 向量检索 + 重排序 | 0.5 | module_rag/service/retrieval_service.py | 2天 |

### 阶段 1: 情境区 + 决策区（反思区的前序）

| # | 任务 | 依赖 | 涉及文件 | 预计 |
|---|------|------|----------|------|
| 1.1 | 创建 `module_learning/` 模块骨架 | 0.3 | module_learning/ | 1天 |
| 1.2 | 学习记录主表 + 状态机引擎 | 1.1 | module_learning/service/record_service.py | 2天 |
| 1.3 | 情境区后端 CRUD + AI 分析接口 | 1.2, 0.6 | module_learning/controller/scenario_controller.py | 3天 |
| 1.4 | 决策区后端 CRUD + AI 伦理分析接口 | 1.3 | module_learning/controller/decision_controller.py | 3天 |

### 阶段 2: 反思区（核心）

| # | 任务 | 依赖 | 涉及文件 | 预计 |
|---|------|------|----------|------|
| 2.1 | 反思区数据表迁移（3张表） | 1.2 | alembic/versions/ | 0.5天 |
| 2.2 | 反思区 ORM 模型 + VO 模型 | 2.1 | module_learning/entity/ | 1天 |
| 2.3 | 反思区 DAO 层 | 2.2 | module_learning/dao/reflection_dao.py | 1天 |
| 2.4 | **反思深度评估 Prompt 设计与调优** | 0.6 | module_learning/service/ai_engine.py | 3天 |
| 2.5 | **AI 三层递进提问逻辑实现** | 2.4 | module_learning/service/ai_engine.py | 3天 |
| 2.6 | 反思区 Service 层（CRUD + 深度记录 + 理论关联） | 2.3, 2.5 | module_learning/service/reflection_service.py | 2天 |
| 2.7 | 反思区 Controller 层（7个 API） | 2.6 | module_learning/controller/reflection_controller.py | 1.5天 |
| 2.8 | 反思区前端页面（编辑器 + AI 提问栏 + 深度指示器） | 2.7 | 前端 views/learning/reflection/ | 4天 |
| 2.9 | 深度演变曲线图（ECharts） | 2.6 | 前端 DepthChart.vue | 1.5天 |

### 阶段 3: 研究生成区

| # | 任务 | 依赖 | 涉及文件 | 预计 |
|---|------|------|----------|------|
| 3.1 | 研究区后端（研究问题生成 + 论文框架 + 段落辅助） | 2.7 | module_learning/ | 5天 |
| 3.2 | 研究区前端 | 3.1 | 前端 views/learning/research/ | 4天 |

---

## 十、风险与合规

| 风险 | 等级 | 应对 |
|------|------|------|
| **AI 深度评估不准确** | 高 | 前2周用人工标注的样本反复调Prompt，建立评分一致性 |
| **反身性提问太学术化，学生看不懂** | 高 | Prompt里强调"温暖鼓励、非评判"语气，加入具体追问模板 |
| **RAG 检索不相关** | 中 | 社会工作知识库需要高质量入库（教材优先），分块粒度500-800字 |
| **学生反思内容涉及心理危机** | 高 | 警报系统关键词扫描（自杀/自残/崩溃），自动通知教师 |
| **隐私合规** | 中 | 学生反思文本调用大模型前脱敏姓名，AI输出标注"AI生成" |
| **个人信息保护法** | 高 | 注册时明示数据用途，提供数据导出和删除功能 |

---

## 十一、技术栈建议

| 用途 | MVP阶段（现在） | 扩展阶段 |
|------|-------------------|----------|
| 向量数据库 | PgVector（零部署成本） | 百万级后再迁移Milvus |
| Embedding | 智谱 Embedding-3 API | 后期本地部署 bge-large-zh |
| 大模型 | DeepSeek-V3 API | 可随时切换（agno已支持多Provider） |
| 文档解析 | PyMuPDF + python-docx | 如需OCR再加Tesseract |
| 前端图表 | ECharts | — |
| 富文本 | WangEditor（复用若依的） | — |
| 异步任务 | 暂用同步（文档量小） | Celery + Redis（量大了再加） |
