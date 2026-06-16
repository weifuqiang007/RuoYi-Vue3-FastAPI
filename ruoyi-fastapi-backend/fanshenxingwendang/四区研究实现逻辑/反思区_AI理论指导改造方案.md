# 反思区 AI 理论指导改造 — 变更文档

> **版本**：V1.0
> **日期**：2026-06-12
> **编写人**：后端架构师
> **变更范围**：阶段5 反思区（后端 controller/service + 前端全部组件）

---

## 一、变更背景

### 1.1 原始设计问题

反思区代码框架已搭建完成，但存在以下问题：

| # | 问题 | 影响 |
|---|---|---|
| 1 | 后端缺少 `PUT /confirm` 接口 | 前端调用 `confirmReflection()` 返回 404，无法推进到研究区 |
| 2 | AI 提问仅返回泛泛追问，未结合知识库理论给出具体指导 | 学生得不到有价值的理论参照，反思深度无法有效提升 |
| 3 | 前端只展示当前一轮反思，历史对话未利用 | 多轮反思过程不可见，学生无法回顾自己的思维演变 |
| 4 | 理论关联面板仅显示 tag 名称 | 理论名称 + 简短描述，无法传达理论与反思的具体关联 |

### 1.2 用户诉求

> 反思区要结合前两个区域（情境区+决策区）的内容，然后结合上理论，给出指导意见。
> 需要显示多轮反思的结果，每一个反思的结果对应知识库中的理论知识。

**核心转变**：从"AI 泛泛追问"升级为"AI 结合理论给出具体指导"。

---

## 二、变更决策

### 2.1 Prompt 升级策略

**结论**：升级 `REFLECTION_PROMPT` 输出结构，从简单追问模式升级为理论指导模式。

| 维度 | 原设计 | 新设计 |
|---|---|---|
| 理论输出 | `theories: [{name, description}]` | `theory_guidance: [{theory_name, theory_source, relevance, suggestion}]` |
| 指导方向 | 无 | 新增 `reflection_direction` 字段 |
| 追问 | 有 | 保留，作为辅助 |
| 数据库 | `linked_theories` 存 theories | 兼容：优先存 theory_guidance，降级存 theories |

### 2.2 前端布局策略

**结论**：从"左编辑器 + 右面板"改为"多轮反思时间线"布局。

```
原布局：                              新布局：
┌─────────────┬──────────────┐       ┌─ 深度指示器 ─────────────────────┐
│             │ AI提问引导栏  │       │ 深度：0.65（分析性）              │
│ 反思编辑器  │              │       ├──────────────────────────────────┤
│             │ 理论标签     │       │ ┌─ 第1轮反思（只读）──────────┐  │
│             │              │       │ │ 📖 赋权理论 → 建议从...     │  │
│             │              │       │ │ 💡 AI建议：从...角度反思     │  │
│             │              │       │ └──────────────────────────────┘  │
│             │              │       │ ┌─ 第2轮（编辑中）────────────┐  │
│             │              │       │ │ [反思编辑器 textarea]        │  │
│             │              │       │ │ [保存] [生成理论指导]        │  │
│             │              │       │ │ ── AI理论指导 ──             │  │
│             │              │       │ │ 📖 赋权理论：关联...建议... │  │
│             │              │       │ │ 💡 方向：建议你...           │  │
│             │              │       │ └──────────────────────────────┘  │
└─────────────┴──────────────┘       │ [深度图] [理论总览] [确认推进]   │
                                     └──────────────────────────────────┘
```

### 2.3 confirm 接口设计

**结论**：参考 `scenario_controller.py` 的 confirm 模式，新增 `PUT /confirm` 路由。

逻辑：
1. 校验反思内容非空
2. 设 `reflection.status = '1'`
3. 更新 `record.reflection_status = '2'`

---

## 三、后端变更清单

### 3.1 controller 层

**文件**：`module_learning/controller/reflection_controller.py`

| 变更类型 | 内容 |
|---|---|
| 新增 import | `from fastapi import Body` |
| 新增路由 | `PUT /confirm` — 确认反思完成 |

`/confirm` 接口签名：
```python
@reflection_controller.put('/confirm', summary='确认反思完成')
async def confirm(
    request: Request,
    query_db: ...,
    current_user: ...,
    record_id: int = Body(..., embed=True, description='学习记录ID'),
) -> Response
```

### 3.2 service 层

**文件**：`module_learning/service/reflection_service.py`

| # | 变更类型 | 内容 |
|---|---|---|
| 1 | 新增 import | `import logging`，创建 `logger = logging.getLogger(__name__)` |
| 2 | 重写 | `REFLECTION_PROMPT` — 升级为理论指导模式（详见 3.3） |
| 3 | 新增方法 | `confirm(db, record_id, user_id)` — 确认反思完成 |
| 4 | 修改方法 | `generate_questions` — 兼容新格式 `theory_guidance`，新增 3 处日志 |
| 5 | 修改方法 | `get_detail` — 返回值新增 `depth_score_before/after` |
| 6 | 修改方法 | `_retrieve_theory_knowledge` — 新增 4 处日志和异常保护 |

### 3.3 REFLECTION_PROMPT 新旧对比

**旧版输出 JSON 结构**：
```json
{
  "depth_score": 0.65,
  "depth_level": "analytical",
  "questions": [
    {"level": "reflexive", "question": "追问内容", "purpose": "引导目的"}
  ],
  "theories": [
    {"name": "理论名称", "description": "关联说明"}
  ]
}
```

**新版输出 JSON 结构**：
```json
{
  "depth_score": 0.65,
  "depth_level": "analytical",
  "theory_guidance": [
    {
      "theory_name": "赋权理论",
      "theory_source": "Solomon (1976)",
      "relevance": "该理论与你反思中提到的...直接相关，因为...",
      "suggestion": "建议你从服务对象的能力和优势出发，重新审视你在...中的角色定位，思考..."
    }
  ],
  "reflection_direction": "基于以上理论，建议你从...角度继续反思，重点关注...",
  "questions": [
    {"level": "reflexive", "question": "追问内容", "purpose": "引导目的"}
  ]
}
```

**关键新增字段**：
- `theory_guidance[].theory_name` — 理论名称
- `theory_guidance[].theory_source` — 理论来源（作者/年份）
- `theory_guidance[].relevance` — 该理论与学生反思的具体关联
- `theory_guidance[].suggestion` — 基于该理论的具体反思建议
- `reflection_direction` — 整体反思方向建议

**兼容处理**：`generate_questions` 方法中优先取 `theory_guidance`，为空时降级取 `theories`。

---

## 四、前端变更清单

### 4.1 新增文件

| 文件 | 说明 |
|---|---|
| `views/learning/reflection/components/ReflectionRoundCard.vue` | 多轮反思历史卡片组件（只读），展示：理论指导 + 反思方向 + 追问 + 深度变化 |

### 4.2 修改文件

| 文件 | 变更内容 |
|---|---|
| `reflection/index.vue` | **完全重构**：从左右分栏改为多轮时间线布局；新增"生成理论指导"按钮；解析 dialogues 为历史轮次卡片；内联展示最新 AI 指导 |
| `reflection/components/AiQuestionPanel.vue` | **重构**：从"AI提问引导"改为"AI理论指导"面板，展示 theory_guidance + reflection_direction + questions |
| `reflection/components/TheoryLinkage.vue` | **升级**：从 tag 列表改为详细理论卡片，支持展示 theory_name + theory_source + relevance + suggestion |

### 4.3 未修改文件

| 文件 | 说明 |
|---|---|
| `DepthIndicator.vue` | 不变，继续展示深度进度条 |
| `DepthChart.vue` | 不变，继续展示深度演变折线图 |
| `ReflectionEditor.vue` | 不变，当前轮次编辑器内嵌到 index.vue 中 |
| `api/learning/reflection.js` | 不变，所有 API 路径与后端一致 |

---

## 五、交互流程

### 5.1 用户操作流程

```
用户进入反思区
  → loadDetail() 加载反思数据（含 dialogues 历史）
  → 历史轮次以 ReflectionRoundCard 只读展示（第1轮、第2轮...）
  → 当前轮次显示 textarea 编辑器 + 保存/生成按钮

用户写反思 → 点"保存反思"
  → POST /learning/reflection/save → 返回 reflection_id + depth_score
  → reflectionId 获得 → "生成理论指导"按钮启用

用户点"生成理论指导"
  → POST /learning/reflection/questions
  → 后端：RAG 检索理论 → 构建 Prompt → LLM 返回 theory_guidance + reflection_direction + questions
  → 前端内联展示：📖 关联理论（名称+来源+关联+建议） + 💡 反思方向 + 📌 追问
  → 深度分数更新 → DepthIndicator + DepthChart 同步更新

用户基于 AI 指导继续写反思 → 再保存 → 再生成 → 形成新一轮
  → 上一轮变为只读 ReflectionRoundCard
  → 当前轮次重新开始

用户满意后 → 点"确认并进入研究区"
  → PUT /learning/reflection/confirm → 成功
  → PUT /learning/record/advance/{record_id} → 推进到 research 阶段
```

### 5.2 数据流转

```
每轮 AI 交互：
  前端 POST /questions {reflection_id}
      → 后端 generate_questions()
          → _get_scenario_summary()   ← 情境区数据
          → _get_decision_summary()   ← 决策区数据
          → _retrieve_theory_knowledge() ← RAG 检索理论（用反思文本查询）
          → 构建 Prompt（含三层提问策略）
          → AiCall.call_llm_json()    ← LLM 调用
      → 返回 {theory_guidance, reflection_direction, questions, depth_score, depth_level}
      → 存入 edu_reflection_dialogue（content = 完整 JSON）
      → 存入 edu_reflection_depth_history（深度变化记录）

前端 loadDetail()：
  → GET /detail/{record_id}
  → 返回 {content, depth_score, linked_theories, dialogues: [...]}
  → dialogues 中 role='assistant' 的 content 解析为每轮 ReflectionRoundCard
```

---

## 六、数据库影响

**无数据库变更**。所有改动复用现有表结构：

| 表 | 复用方式 |
|---|---|
| `edu_reflection_data` | `linked_theories` 字段改为存储 `theory_guidance` 数组（JSONB，格式兼容） |
| `edu_reflection_dialogue` | `content` 存储 AI 返回的完整 JSON（已含新字段），`linked_theories` 同步更新 |
| `edu_reflection_depth_history` | 无变化，继续记录深度演变 |

---

## 七、风险与注意事项

| # | 风险 | 应对 |
|---|---|---|
| 1 | LLM 返回的 `theory_guidance` 字段可能缺失或不规范 | 前端组件做了兼容：优先取 `theory_guidance`，降级取 `theories` |
| 2 | 旧数据中 dialogue 的 content 是旧格式 JSON（只有 questions + theories） | `ReflectionRoundCard` 内部 `computed` 做了字段容错，缺失的字段不展示 |
| 3 | RAG 检索无结果时 LLM 无理论参考 | 日志记录 warning，Prompt 中说明"暂无理论参考"让 LLM 自行补充 |
| 4 | `model_id=1` 硬编码 | 如数据库中 model_id=1 不存在会报错，后续应改为从任务配置中读取 |
