# 产品需求文档（PRD）

**项目名称：** 生成式AI驱动的反身性学习闭环系统  
**子标题：** 面向《社会工作行动研究》课程的"情境—决策—反思—研究生成"四区联动平台  
**文档版本：** v1.0  
**编制单位：** 浙江树人学院 公共管理学院  
**项目负责人：** 张亦弛  
**文档日期：** 2026年5月  
**文档状态：** 评审稿

---

## 目录

1. [项目背景与目标](#1-项目背景与目标)
2. [系统四层结构总览](#2-系统四层结构总览)
3. [核心功能模块详述](#3-核心功能模块详述)
4. [用户操作流程](#4-用户操作流程)
5. [整体系统架构](#5-整体系统架构)
6. [技术框架详述](#6-技术框架详述)
7. [数据模型设计](#7-数据模型设计)
8. [非功能性需求](#8-非功能性需求)
9. [项目实施计划](#9-项目实施计划)
10. [风险与应对](#10-风险与应对)

---

## 1. 项目背景与目标

### 1.1 背景

社会工作专业的核心教学目标是培养学生在真实情境中运用专业理论、做出专业判断、并从实践中生成研究问题的能力。这一过程被称为"反身性实践"——学生既是行动者，也是研究者，需要在行动中持续反思自身与情境的关系。

传统《社会工作行动研究》课程面临两个结构性困境：

**困境一：实践场的缺失**
课堂难以模拟连续、真实、有责任压力的实践情境。学生缺乏在动态行动中形成专业判断的土壤，反思易停留于对既定案例的静态复述，无法实现"行动中建构意义"的能力目标。

**困境二：研究思考的悬置**
学生难以在"计划—行动—观察—反思"的完整循环中获得高频、个性化的过程性指导。研究问题多依赖教师预设或文献推导，而非从自身实践困境中内生演化。

上述困境的本质是传统教学模式无法支撑**"连续行动—动态反思—研究生成"**的完整学习闭环。

### 1.2 项目目标

本项目旨在开发一套以生成式AI为核心驱动力的数字化学习平台，实现以下目标：

| 目标维度 | 具体指标 |
|---|---|
| 闭环构建 | 打通"情境进入→问题识别→伦理决策→反思追问→研究生成"完整链路 |
| 能力培养 | 学生反身性反思能力、专业判断能力、研究问题生成能力可测可评 |
| 课程转型 | 从"方法讲授"模式转向"过程生成"模式 |
| 技术落地 | 专业知识库驱动的AI系统，而非通用对话工具 |

### 1.3 用户群体

| 用户角色 | 人群描述 | 核心诉求 |
|---|---|---|
| 学生用户 | 社会工作专业本科/研究生，参与实习或课程实践 | 在实践中得到专业引导，最终形成研究框架 |
| 教师用户 | 课程负责人、实习督导教师 | 管理知识库、监控学生进度、提供批注反馈 |
| 管理员 | 系统运维人员 | 系统配置、数据安全、权限管理 |

---

## 2. 系统四层结构总览

本系统采用**四层纵向架构**设计，每一层对应不同的功能职责与技术组件，层间通过标准接口进行数据流转。

```
┌─────────────────────────────────────────────────────────────┐
│                   第一层：用户交互层（前端）                    │
│        Web端 / 移动端 / 小程序  ——  四区联动学习界面             │
├─────────────────────────────────────────────────────────────┤
│                   第二层：业务逻辑层（后端）                    │
│    用户服务 / 学习流程引擎 / AI调度服务 / 评价分析服务           │
├─────────────────────────────────────────────────────────────┤
│                   第三层：数据存储层                           │
│    关系型数据库（结构化数据）+ 向量数据库（语义检索）             │
├─────────────────────────────────────────────────────────────┤
│                   第四层：AI能力层                            │
│    大模型API接口 / RAG检索增强 / 提示词工程 / 知识库管理          │
└─────────────────────────────────────────────────────────────┘
```

### 各层职责说明

**第一层 用户交互层**
负责呈现"情境区—决策区—反思区—研究生成区"四区学习界面，以及教师管理端界面。是用户与系统交互的唯一入口，采用响应式设计，支持PC浏览器与移动端。

**第二层 业务逻辑层**
处理所有业务规则，包括：学习流程状态机管理（控制四区流转逻辑）、AI任务调度（将用户输入包装为AI请求）、过程数据记录、评价计算等。是系统的核心控制层。

**第三层 数据存储层**
分为两类存储介质：关系型数据库存储用户数据、学习记录、案例结构化信息；向量数据库存储专业知识的语义向量，支持语义相似度检索，是RAG功能的核心基础设施。

**第四层 AI能力层**
封装对大模型API的调用逻辑，结合RAG检索结果构造完整提示词，输出专业化、有依据的AI回复。该层将"通用大模型"转化为"社会工作专业智能助手"。

---

## 3. 核心功能模块详述

### 3.1 情境区（Situation Zone）

**功能定位：** 学习起点，负责将学生的实习经历转化为可供分析的专业问题。

**输入形式：**
- 学生以自由文字描述在实习/社会实践中遇到的情景
- 支持语音输入（转文字后处理）
- 支持分段填写（时间背景 → 关键事件 → 参与人物 → 即时感受）

**AI处理流程：**

```
学生描述输入
    ↓
语义理解（大模型分析情景内容）
    ↓
RAG检索（从案例库中找相似历史情景）
    ↓
专业问题识别（输出：问题类型 + 专业标签 + 理论关联）
    ↓
呈现给学生（问题界定建议 + 相似案例 + 相关理论框架）
```

**输出内容：**
- 问题界定建议：将情景描述转化为社会工作专业语言（如"服务对象因经济困境产生的沟通拒绝行为"）
- 相似历史案例：从案例库检索2-3个相似情境，展示处理结果
- 理论关联标签：列出与该情景相关的专业理论（如优势视角、危机介入理论）
- 引导问题：推送1-2个促进学生深入思考的反问

**关键规则：**
- AI的问题界定仅作"建议"呈现，学生可修改或推翻
- 所有理论标签须标注知识来源（来自哪门课件/哪篇文献）

---

### 3.2 决策区（Decision Zone）

**功能定位：** 聚焦于关键行动节点的伦理判断训练，是专业价值观培养的核心区域。

**交互设计：**

系统根据情境区识别的问题类型，自动推送**结构化决策框架**，引导学生逐项填写：

| 填写项 | 说明 | 示例 |
|---|---|---|
| 关键节点描述 | 描述需要做出判断的具体时刻 | "大爷情绪失控，我是否要强行介入" |
| 我的决策 | 学生描述自己实际做了什么 | "我选择暂时退出，给大爷情绪空间" |
| 决策理由 | 说明为何这样做 | "认为强行介入会激化情绪，影响关系建立" |
| 当时心理状态 | 自我觉察描述 | "感到焦虑和无力，担心被督导认为不专业" |
| 结果评估 | 这个决策的实际后果 | "大爷5分钟后主动找我，后续沟通顺畅" |

**AI提供的参照：**
- 从历史案例库调取该类情景下其他社工/学生的决策方案（脱敏处理）
- 列出适用的伦理原则（如"服务对象自决权"、"最小伤害原则"）
- 提供简短的伦理分析，但不给出"正确答案"

**约束说明：**
- 系统明确标注：AI分析仅供参考，不替代专业督导判断
- 敏感情境（涉及人身安全、隐私）须触发教师提醒通知

---

### 3.3 反思区（Reflection Zone）

**功能定位：** 系统最核心的AI交互区域，通过结构化追问引导学生从"描述经历"走向"深度反身性反思"。

**AI追问策略（三层递进）：**

```
第一层：描述性追问（发生了什么）
  "您提到大爷拒绝沟通，能具体描述当时的场景吗？"

      ↓

第二层：分析性追问（为什么发生）
  "您认为触发大爷这个反应的根本原因是什么？
   这与他的经济困境之间有什么关联？"

      ↓

第三层：反身性追问（您与情境的关系）
  "在这个过程中，您自身的情绪反应对您的决策产生了怎样的影响？
   您是否注意到您的某些预设假设？"
```

**多轮追问逻辑：**
- 每次学生回复后，AI根据内容动态生成下一个问题
- 系统自动追踪反思深度：检测学生回答是否停留在事件层面，若停留则继续追问
- 最多进行5-7轮追问后，进入反思小结生成

**反思小结（AI生成）：**
- 梳理本次反思的核心洞见
- 指出学生尚未深入的角度
- 连接到相关专业理论，提示可供阅读的文献方向

**过程追踪：**
- 系统记录每一轮问答，形成可回溯的"反思日志"
- 可视化呈现学生多次反思记录的演变轨迹（思维成熟度曲线）

---

### 3.4 研究生成区（Research Generation Zone）

**功能定位：** 将前三区积累的实践材料转化为学术研究框架，完成从实践到研究的跨越。

**输入来源：**
- 情境区：问题界定、专业标签、理论关联
- 决策区：关键节点、决策逻辑、伦理依据
- 反思区：深层洞见、反身性分析、文献方向

**AI生成内容：**

**（1）研究问题提炼**
基于学生所有记录，提出2-3个可供选择的研究问题，格式示例：
> "社区老年服务对象经济困境对社工专业关系建立的影响机制研究"
> "社工自我情绪管理对危机介入决策的影响——基于反身性实践的探索"

**（2）论文框架建议**
```
一、研究背景与问题意义
   （基于情境区的问题界定自动生成参考段落）

二、文献综述
   （基于理论标签推荐相关文献，给出综述写作方向）

三、研究设计
   （根据事件类型推荐适用的研究方法：质性/行动研究）

四、研究发现（待完成）
   （提示：可将反思日志中的洞见作为初步分析材料）

五、讨论与反思
   （将反身性反思内容与理论框架对话）

六、结论与建议
```

**（3）段落写作支架**
针对每个章节，提供：
- 写作提示：该章节需要回答什么问题
- 材料映射：哪些已有记录可以支撑本节写作
- 学术表达建议：将口语化内容转化为学术语言的示例

**学生主权保障：**
所有AI生成内容均以"建议草稿"形式呈现，学生可全文修改、部分采纳或完全重写。系统记录AI生成内容与最终提交内容的差异，用于教学研究。

---

### 3.5 教师管理端

**功能模块：**

| 模块名称 | 功能说明 |
|---|---|
| 知识库管理 | 上传课件、论文、伦理框架文档；管理案例库；标注知识条目 |
| 学生进度看板 | 实时查看每位学生在四区的完成状态、反思深度评分 |
| 内容审核 | 审阅AI生成的问题界定、追问内容，可批注修改建议 |
| 警报管理 | 接收高风险情境警报（学生描述涉及人身安全等）|
| 评价报告 | 生成班级/个人能力成长报告，支持导出 |
| 提示词调试台 | 教师可直接调整AI提问策略和追问逻辑（需权限）|

---

## 4. 用户操作流程

### 4.1 学生操作完整流程

```
【起点：学生登录系统】
        │
        ▼
【新建学习记录】
  填写实习基本信息：
  · 实习机构名称
  · 日期与时间
  · 服务对象基本描述（脱敏）
        │
        ▼
┌───────────────────────────────┐
│            情境区              │
│  Step 1: 自由描述实习情景       │
│  （文字/语音，500字以内）        │
│                               │
│  Step 2: 查看AI的专业问题界定   │
│  · 确认/修改 AI给出的问题标签   │
│  · 浏览相似历史案例             │
│  · 了解关联理论框架             │
│                               │
│  Step 3: 确认情景描述完成       │
│  → 进入决策区                  │
└───────────────────────────────┘
        │
        ▼
┌───────────────────────────────┐
│            决策区              │
│  Step 4: 填写关键节点描述       │
│                               │
│  Step 5: 逐项填写决策表单       │
│  · 我的决策                    │
│  · 决策理由                    │
│  · 当时心理状态                 │
│  · 结果评估                    │
│                               │
│  Step 6: 查看AI提供的参照内容   │
│  · 历史案例决策方案              │
│  · 相关伦理原则                 │
│                               │
│  Step 7: 确认决策记录完成       │
│  → 进入反思区                  │
└───────────────────────────────┘
        │
        ▼
┌───────────────────────────────┐
│            反思区              │
│  Step 8: 接收AI第一轮追问       │
│  → 学生文字回复                 │
│                               │
│  Step 9: 多轮追问对话（3-7轮）  │
│  AI根据回复动态生成下一问        │
│  学生持续深化反思              │
│                               │
│  Step 10: 查看AI生成反思小结    │
│  · 核心洞见梳理                 │
│  · 尚需深入的角度               │
│  · 推荐阅读文献方向             │
│                               │
│  Step 11: 确认反思完成         │
│  → 进入研究生成区               │
└───────────────────────────────┘
        │
        ▼
┌───────────────────────────────┐
│          研究生成区             │
│  Step 12: 查看AI提炼的研究问题  │
│  · 从3个建议中选择/自行撰写     │
│                               │
│  Step 13: 查看论文框架建议      │
│  · 浏览每章节的写作提示         │
│  · 查看材料与章节的映射关系     │
│                               │
│  Step 14: 使用写作支架         │
│  · 选定章节，生成段落建议        │
│  · 在编辑器中修改完善           │
│                               │
│  Step 15: 提交本次学习记录      │
└───────────────────────────────┘
        │
        ▼
【完成 → 可在历史记录中回顾/继续完善】
```

**关键交互原则：**
- 四区之间顺序流转，前区完成后才能进入下一区
- 每区均可返回修改，但修改会触发AI重新分析
- 支持"中途保存"，学生可分多次完成一条记录
- 每条学习记录对应一次真实实践经历

---

### 4.2 教师操作完整流程

#### 场景一：知识库建设（项目初期/持续维护）

```
【教师登录管理端】
        │
        ▼
【进入知识库管理模块】
        │
  ┌─────┴─────┐
  ▼           ▼
上传文档     管理案例库
  │           │
  · PDF课件   · 新增历史案例
  · Word论文  · 填写案例结构化表单
  · 伦理框架  · 标注情境类型/决策方式/涉及理论
  · 阅读材料  · 审核案例质量
  │           │
  ▼           ▼
系统自动切分文本为知识块
系统自动生成向量嵌入
知识库更新完成
```

#### 场景二：课程进行中的日常督导

```
【登录管理端 → 进入学生进度看板】
        │
        ▼
查看班级整体完成情况
  · 各区完成人数
  · 平均反思深度评分
  · 本周新增记录数
        │
        ▼
选择特定学生 → 查看详细记录
  · 情景描述原文
  · AI的问题界定与学生修改版本
  · 决策表单完整内容
  · 反思追问对话全文
  · AI生成的研究框架
        │
        ▼
教师批注与反馈
  · 在具体内容处添加批注
  · 录制语音反馈（可选）
  · 推荐补充阅读资料
  · 将此案例（脱敏后）收录进案例库
        │
        ▼
发送反馈通知给学生
```

#### 场景三：警报处理

```
收到系统警报推送
（学生描述涉及人身安全/伦理高风险情境）
        │
        ▼
进入警报详情
  · 查看完整情景描述
  · 查看AI的风险评估
        │
        ▼
决定处理方式
  · 线下联系学生
  · 联系实习机构督导
  · 在线留言回复
  · 标记为已处理
```

#### 场景四：评价报告生成

```
【进入评价报告模块】
        │
  ┌─────┴───────────┐
  ▼                 ▼
班级报告           个人报告
  │                 │
  · 班级能力分布图   · 能力成长曲线
  · 反思深度趋势     · 各区完成质量
  · 高频情境类型     · 研究问题完成度
  · 高频理论使用     · 与班级对比分析
        │
        ▼
导出为PDF / Excel
        │
        ▼
用于期末成绩评定 / 教学研究
```

---

## 5. 整体系统架构

### 5.1 系统架构总图

```
                           ┌──────────────────────┐
                           │      用户端（前端）      │
                           │                      │
                           │  ┌──────┐ ┌────────┐ │
                           │  │Web端 │ │移动端  │ │
                           │  └──────┘ └────────┘ │
                           └──────────┬───────────┘
                                      │ HTTPS
                           ┌──────────▼───────────┐
                           │      API网关          │
                           │  · 身份验证           │
                           │  · 限流熔断           │
                           │  · 路由转发           │
                           └──────────┬───────────┘
                                      │
          ┌───────────────────────────┼────────────────────────┐
          │                           │                        │
          ▼                           ▼                        ▼
┌─────────────────┐        ┌──────────────────┐    ┌──────────────────┐
│   用户服务       │        │  学习流程引擎     │    │   AI调度服务      │
│ · 注册/登录     │        │ · 四区状态管理    │    │ · 提示词构造     │
│ · 权限管理      │        │ · 数据流转控制    │    │ · RAG检索调用    │
│ · 个人信息      │        │ · 过程数据记录    │    │ · 大模型API调用  │
└────────┬────────┘        └────────┬─────────┘    └────────┬─────────┘
         │                          │                        │
         └──────────────────────────┼────────────────────────┘
                                    │
                    ┌───────────────┼──────────────────┐
                    │               │                  │
                    ▼               ▼                  ▼
          ┌──────────────┐  ┌─────────────┐  ┌──────────────────┐
          │ PostgreSQL   │  │ 向量数据库   │  │  文件存储服务     │
          │（关系型数据） │  │（知识语义库）│  │（课件/文档/附件） │
          │ · 用户数据   │  │ · 知识块向量 │  │                  │
          │ · 学习记录   │  │ · 案例向量   │  │                  │
          │ · 案例结构   │  │ · 语义检索   │  │                  │
          └──────────────┘  └─────────────┘  └──────────────────┘
                                    │
                    ┌───────────────┘
                    │
                    ▼
          ┌──────────────────────────────────┐
          │          AI能力层                 │
          │                                  │
          │  ┌─────────────┐ ┌────────────┐  │
          │  │  RAG引擎     │ │ 大模型API  │  │
          │  │(LangChain)  │ │（Claude /  │  │
          │  │             │ │ DeepSeek） │  │
          │  └─────────────┘ └────────────┘  │
          │                                  │
          │  ┌─────────────────────────────┐  │
          │  │      提示词管理系统           │  │
          │  │ · 四区专属提示词模板          │  │
          │  │ · 动态上下文注入             │  │
          │  └─────────────────────────────┘  │
          └──────────────────────────────────┘
```

### 5.2 数据流示意（以反思区为例）

```
学生提交反思回答（文字）
        │
        ▼
前端发送API请求至后端
  {session_id, zone: "reflection", round: 3, content: "..."}
        │
        ▼
后端AI调度服务接收请求
        │
        ▼
① 从数据库读取本次会话上下文
  · 情境描述
  · 决策表单内容
  · 前2轮追问对话
        │
        ▼
② RAG检索
  将"学生回答内容"转为向量
  在向量数据库中检索相关知识块
  返回Top-3相关知识内容（带来源标注）
        │
        ▼
③ 构造提示词
  System Prompt（专业角色定义）
  + 会话历史上下文
  + RAG检索结果
  + 当前轮次追问策略
        │
        ▼
④ 调用大模型API，获得追问内容
        │
        ▼
⑤ 结果处理
  · 解析AI输出（追问内容 + 反思深度评估分）
  · 存入数据库（本轮问答记录）
        │
        ▼
⑥ 返回前端，渲染追问内容
```

---

## 6. 技术框架详述

### 6.1 前端技术框架

#### 技术选型

| 技术项 | 选型 | 选择理由 |
|---|---|---|
| 核心框架 | React 18 | 组件化开发，生态成熟，利于复杂状态管理 |
| 跨端方案 | Taro 3.x | 一套代码同时输出Web、微信小程序、H5 |
| 状态管理 | Zustand | 轻量级，适合中型项目，学习成本低 |
| UI组件库 | Ant Design / Ant Design Mobile | 企业级组件，表单处理能力强 |
| 富文本编辑 | Quill.js | 研究生成区的文档编辑需求 |
| HTTP客户端 | Axios + React Query | 请求缓存、自动重试、加载状态管理 |
| 数据可视化 | ECharts | 能力成长轨迹、反思深度图表 |
| 实时通信 | Socket.io Client | AI流式输出（打字机效果） |

#### 四区界面结构

```
App
├── AuthModule（登录/注册）
├── StudentModule（学生端）
│   ├── Dashboard（我的学习记录列表）
│   ├── RecordDetail（单条记录详情）
│   │   ├── SituationZone（情境区）
│   │   │   ├── InputPanel（情景描述输入）
│   │   │   └── AIResultPanel（AI分析结果展示）
│   │   ├── DecisionZone（决策区）
│   │   │   ├── DecisionForm（结构化表单）
│   │   │   └── ReferencePanel（历史案例参照）
│   │   ├── ReflectionZone（反思区）
│   │   │   ├── DialogPanel（多轮对话界面）
│   │   │   └── SummaryPanel（反思小结）
│   │   └── ResearchZone（研究生成区）
│   │       ├── QuestionPanel（研究问题建议）
│   │       ├── FrameworkPanel（论文框架）
│   │       └── WritingPanel（写作支架编辑器）
└── TeacherModule（教师端）
    ├── KnowledgeBase（知识库管理）
    ├── StudentDashboard（学生进度看板）
    ├── ReviewPanel（内容审核与批注）
    └── ReportModule（评价报告）
```

#### AI流式输出实现

AI追问内容采用流式返回（Streaming），实现打字机效果，提升用户体验：

```javascript
// 前端流式接收示例
const streamAIResponse = async (payload) => {
  const response = await fetch('/api/ai/reflect', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value);
    appendToDisplay(chunk); // 逐字追加到界面
  }
};
```

---

### 6.2 后端技术框架

#### 技术选型

| 技术项 | 选型 | 选择理由 |
|---|---|---|
| 主框架 | Python FastAPI | 异步支持好，适合AI服务场景；自动生成API文档 |
| 辅助服务 | Node.js (Express) | 处理文件上传、静态资源等轻量任务 |
| 任务队列 | Celery + Redis | AI调用为耗时任务，异步处理避免请求超时 |
| 认证授权 | JWT + OAuth2 | 标准化身份验证方案 |
| API规范 | RESTful API + OpenAPI 3.0 | 前后端分离，接口文档自动生成 |
| 日志系统 | Python logging + ELK Stack | 记录AI调用日志，便于排查与分析 |
| 容器化 | Docker + Docker Compose | 环境一致性，易于部署和迁移 |

#### 核心服务模块

**① 用户服务（User Service）**
```python
# 核心接口
POST   /api/auth/register       # 注册
POST   /api/auth/login          # 登录，返回JWT
POST   /api/auth/refresh        # 刷新Token
GET    /api/user/profile        # 获取个人信息
PUT    /api/user/profile        # 更新个人信息
```

**② 学习流程服务（Learning Service）**
```python
# 学习记录管理
POST   /api/records             # 新建学习记录
GET    /api/records             # 获取记录列表
GET    /api/records/{id}        # 获取记录详情

# 四区数据提交
POST   /api/records/{id}/situation    # 提交情境描述
PUT    /api/records/{id}/situation    # 更新情境内容
POST   /api/records/{id}/decision     # 提交决策表单
POST   /api/records/{id}/reflection   # 提交反思回复（触发AI追问）
POST   /api/records/{id}/research     # 触发研究框架生成
```

**③ AI调度服务（AI Orchestration Service）**
```python
# AI任务接口（后端内部调用，不直接暴露给前端）
async def process_situation(session_id, description):
    # 1. RAG检索相似情境
    # 2. 构造提示词
    # 3. 调用大模型
    # 4. 解析结果
    # 5. 存储并返回

async def process_reflection_round(session_id, round_num, student_answer):
    # 根据轮次和内容动态生成追问
    ...

async def generate_research_framework(session_id):
    # 汇总全部记录，生成论文框架
    ...
```

**④ 知识库管理服务（Knowledge Service）**
```python
POST   /api/knowledge/upload          # 上传文档（教师权限）
POST   /api/knowledge/cases           # 新增案例
GET    /api/knowledge/cases           # 查询案例库
PUT    /api/knowledge/cases/{id}      # 更新案例
DELETE /api/knowledge/cases/{id}      # 删除案例
POST   /api/knowledge/rebuild-index   # 重建向量索引（管理员）
```

#### 四区提示词工程框架

每个功能区使用独立的提示词模板，确保AI输出的专业性和一致性：

```python
SITUATION_SYSTEM_PROMPT = """
你是一位资深的社会工作督导，具备丰富的社区实践经验。
你的任务是帮助社工学生从专业角度审视他们的实习情景。

工作原则：
1. 使用专业的社会工作语言界定问题，但表达需平易近人
2. 识别情景中涉及的专业议题（如：沟通边界、资源链接、危机介入等）
3. 关联相关理论框架，但避免生搬硬套
4. 所有判断仅作参考，尊重学生的自主判断

参考知识（来自专业知识库）：
{rag_context}

学生描述的情景：
{student_situation}

请完成以下任务：
1. 用专业语言界定核心问题（100字以内）
2. 列出3个相关专业概念/理论标签（注明来源）
3. 提出1个引导学生深入思考的问题
"""

REFLECTION_SYSTEM_PROMPT = """
你是一位擅长苏格拉底式追问的社会工作教育者。
你的目标是通过递进式提问，帮助学生从描述事件走向深度反身性反思。

当前反思轮次：{round_num} / 7
当前追问策略：{strategy}  
（第1-2轮：描述性追问；第3-4轮：分析性追问；第5-7轮：反身性追问）

会话上下文：
{conversation_history}

相关专业知识（RAG检索结果）：
{rag_context}

学生本轮回答：
{student_answer}

请生成下一个追问问题：
要求：针对性强、开放式、字数在80字以内、不直接给出答案
"""
```

---

### 6.3 数据库设计

#### 关系型数据库（PostgreSQL）

**核心数据表：**

```sql
-- 用户表
CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username    VARCHAR(50) UNIQUE NOT NULL,
    role        VARCHAR(20) NOT NULL,  -- 'student' | 'teacher' | 'admin'
    real_name   VARCHAR(50),
    institution VARCHAR(100),
    created_at  TIMESTAMP DEFAULT NOW()
);

-- 学习记录主表
CREATE TABLE learning_records (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID REFERENCES users(id),
    title           VARCHAR(200),
    status          VARCHAR(30),  -- 'draft' | 'situation' | 'decision' | 'reflection' | 'research' | 'completed'
    practice_date   DATE,
    institution     VARCHAR(200),
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- 情境区数据表
CREATE TABLE situation_data (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    record_id       UUID REFERENCES learning_records(id),
    raw_description TEXT,                    -- 学生原始描述
    ai_problem_def  TEXT,                    -- AI的问题界定
    student_confirm TEXT,                    -- 学生确认/修改后的版本
    theory_tags     JSONB,                   -- 关联理论标签数组
    similar_cases   JSONB,                   -- 相似案例引用
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 决策区数据表
CREATE TABLE decision_data (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    record_id       UUID REFERENCES learning_records(id),
    key_moment      TEXT,                    -- 关键节点描述
    my_decision     TEXT,                    -- 我的决策
    decision_reason TEXT,                    -- 决策理由
    mental_state    TEXT,                    -- 心理状态
    outcome_eval    TEXT,                    -- 结果评估
    ethics_refs     JSONB,                   -- AI提供的伦理原则参照
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 反思区对话记录表
CREATE TABLE reflection_dialogues (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    record_id       UUID REFERENCES learning_records(id),
    round_number    INTEGER,                 -- 对话轮次
    ai_question     TEXT,                    -- AI追问内容
    student_answer  TEXT,                    -- 学生回答
    depth_score     DECIMAL(3,2),            -- 反思深度评分（0-1）
    rag_refs        JSONB,                   -- 本轮使用的RAG检索结果
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 反思小结表
CREATE TABLE reflection_summaries (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    record_id       UUID REFERENCES learning_records(id),
    ai_summary      TEXT,                    -- AI生成的反思小结
    key_insights    JSONB,                   -- 核心洞见列表
    reading_refs    JSONB,                   -- 推荐阅读方向
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 研究生成区数据表
CREATE TABLE research_data (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    record_id       UUID REFERENCES learning_records(id),
    research_questions  JSONB,               -- AI提炼的研究问题（列表）
    selected_question   TEXT,                -- 学生选定的研究问题
    paper_framework     JSONB,               -- 论文框架结构
    writing_drafts      JSONB,               -- 各章节写作草稿
    final_content       TEXT,                -- 学生最终提交内容
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 知识库案例表
CREATE TABLE knowledge_cases (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title           VARCHAR(200),
    situation_type  VARCHAR(100),            -- 情境类型标签
    situation_desc  TEXT,                    -- 情境描述（脱敏）
    decision_made   TEXT,                    -- 决策内容
    decision_reason TEXT,                    -- 决策理由
    outcome         TEXT,                    -- 实际结果
    theories_used   JSONB,                   -- 涉及理论
    ethics_applied  JSONB,                   -- 使用的伦理框架
    embedding_id    VARCHAR(100),            -- 向量数据库中的ID
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 教师批注表
CREATE TABLE teacher_annotations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    record_id       UUID REFERENCES learning_records(id),
    teacher_id      UUID REFERENCES users(id),
    target_zone     VARCHAR(30),             -- 'situation'|'decision'|'reflection'|'research'
    target_id       UUID,                    -- 具体数据行的ID
    content         TEXT,                    -- 批注内容
    created_at      TIMESTAMP DEFAULT NOW()
);
```

---

### 6.4 向量数据库与RAG检索

#### 技术选型

| 技术项 | 选型 | 说明 |
|---|---|---|
| 向量数据库 | Chroma（开发/小规模）/ Milvus（生产） | Chroma轻量易部署；Milvus性能更强，适合大规模 |
| 嵌入模型 | text2vec-large-chinese | 专为中文优化的句子嵌入模型，适合社会工作中文语料 |
| RAG框架 | LangChain | 封装了文档切分、向量存储、检索链等完整流程 |
| 文档处理 | PyMuPDF（PDF）+ python-docx（Word） | 支持主流格式的课件文档解析 |

#### 知识库构建流程

```python
from langchain.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma

# Step 1: 文档加载
loader = PyMuPDFLoader("社会工作理论与实践.pdf")
documents = loader.load()

# Step 2: 文本切分
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,        # 每个知识块约500字
    chunk_overlap=50,      # 相邻块有50字重叠，保证语义连贯性
    separators=["\n\n", "\n", "。", "；"]  # 中文优先按段落切分
)
chunks = text_splitter.split_documents(documents)

# Step 3: 元数据标注（每个知识块附加来源信息）
for chunk in chunks:
    chunk.metadata.update({
        "source_type": "course_material",  # 'case' | 'theory' | 'ethics' | 'literature'
        "course_name": "社会工作行动研究",
        "theory_tags": [],                  # 教师手动标注或AI自动识别
        "uploaded_by": teacher_id
    })

# Step 4: 向量化并存入向量数据库
embeddings = HuggingFaceEmbeddings(model_name="GanymedeNil/text2vec-large-chinese")
vectorstore = Chroma.from_documents(chunks, embeddings, persist_directory="./chroma_db")
vectorstore.persist()
```

#### RAG检索策略

```python
class SocialWorkRAG:
    def __init__(self):
        self.vectorstore = Chroma(
            persist_directory="./chroma_db",
            embedding_function=embeddings
        )
    
    def retrieve_for_situation(self, description: str, top_k: int = 3):
        """情境区检索：检索相似案例 + 相关理论"""
        # 混合检索：相似案例 + 理论知识
        cases = self.vectorstore.similarity_search(
            description,
            k=top_k,
            filter={"source_type": "case"}
        )
        theories = self.vectorstore.similarity_search(
            description,
            k=top_k,
            filter={"source_type": "theory"}
        )
        return {"cases": cases, "theories": theories}
    
    def retrieve_for_reflection(self, dialogue_history: str, top_k: int = 3):
        """反思区检索：侧重伦理框架和反思方法论"""
        ethics = self.vectorstore.similarity_search(
            dialogue_history,
            k=top_k,
            filter={"source_type": "ethics"}
        )
        return {"ethics": ethics}
    
    def retrieve_for_research(self, full_record: str, top_k: int = 5):
        """研究生成区检索：检索相关文献和研究方法"""
        literature = self.vectorstore.similarity_search(
            full_record,
            k=top_k,
            filter={"source_type": "literature"}
        )
        return {"literature": literature}
```

---

### 6.5 大模型调用层

#### 大模型选型策略

本系统采用**双轨大模型策略**，兼顾效果与合规性：

| 场景 | 推荐模型 | 理由 |
|---|---|---|
| 开发测试阶段 | Claude API（claude-sonnet-4-6） | 长文本理解强，结构化输出质量高，适合复杂追问逻辑 |
| 生产部署（主力） | DeepSeek API | 国内合规，中文能力强，成本较低 |
| 生产部署（备用） | 文心一言 API / 讯飞星火 | 多模型冗余，避免单点故障 |

系统设计为**模型无关架构**，通过统一接口抽象层切换模型：

```python
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, messages: list, stream: bool = False) -> str:
        pass

class ClaudeProvider(LLMProvider):
    async def generate(self, messages: list, stream: bool = False):
        import anthropic
        client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            messages=messages,
            stream=stream
        )
        return response

class DeepSeekProvider(LLMProvider):
    async def generate(self, messages: list, stream: bool = False):
        # DeepSeek API调用（兼容OpenAI接口格式）
        from openai import OpenAI
        client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com"
        )
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=stream
        )
        return response

# 工厂方法，根据配置选择Provider
def get_llm_provider() -> LLMProvider:
    if settings.LLM_PROVIDER == "claude":
        return ClaudeProvider()
    elif settings.LLM_PROVIDER == "deepseek":
        return DeepSeekProvider()
```

#### AI调用完整链路（以反思区为例）

```python
async def process_reflection(
    record_id: str,
    round_num: int,
    student_answer: str
) -> dict:
    
    # 1. 获取会话上下文
    record = await db.get_record(record_id)
    history = await db.get_reflection_history(record_id)
    
    # 2. RAG检索
    rag = SocialWorkRAG()
    rag_results = rag.retrieve_for_reflection(
        dialogue_history=str(history),
        top_k=3
    )
    
    # 3. 确定追问策略
    strategy = determine_strategy(round_num, student_answer)
    # 策略枚举：descriptive | analytical | reflexive | consolidating
    
    # 4. 构造完整提示词
    messages = build_reflection_messages(
        record=record,
        history=history,
        rag_results=rag_results,
        student_answer=student_answer,
        round_num=round_num,
        strategy=strategy
    )
    
    # 5. 调用大模型（流式）
    provider = get_llm_provider()
    response_stream = await provider.generate(messages, stream=True)
    
    # 6. 解析响应并评估反思深度
    ai_question = ""
    async for chunk in response_stream:
        ai_question += chunk
        yield chunk  # 实时推送给前端（SSE）
    
    depth_score = evaluate_reflection_depth(student_answer)
    
    # 7. 持久化本轮记录
    await db.save_reflection_round(
        record_id=record_id,
        round_number=round_num,
        ai_question=ai_question,
        student_answer=student_answer,
        depth_score=depth_score,
        rag_refs=[doc.metadata for doc in rag_results["ethics"]]
    )
    
    return {"depth_score": depth_score, "is_final_round": round_num >= 7}
```

---

## 7. 数据模型设计

### 7.1 知识库JSON结构（案例数据标准格式）

```json
{
  "case_id": "CASE_2024_001",
  "metadata": {
    "situation_type": "危机介入",
    "service_population": "社区老年人",
    "practice_setting": "社区服务中心",
    "created_at": "2024-03-15"
  },
  "situation": {
    "background": "服务对象张某，72岁，独居老人，子女在外地。因经济困难产生严重焦虑情绪……",
    "key_event": "在第三次家访时，服务对象突然情绪激动，拒绝社工进入并言语激烈……",
    "participants": ["社工", "服务对象"],
    "context_factors": ["经济困境", "社会隔离", "代际关系紧张"]
  },
  "decision": {
    "key_moment": "服务对象情绪失控，是否强行介入？",
    "decision_made": "退出当下情境，给予情绪空间，约定10分钟后再尝试沟通",
    "decision_reason": "评估暂无人身危险，强行介入会加剧对抗，损害专业关系",
    "outcome": "10分钟后服务对象主动开门，后续沟通顺畅，关系得到修复"
  },
  "theories_applied": [
    {
      "theory_name": "危机介入理论",
      "application": "识别情绪危机信号，采取非对抗性介入策略",
      "source": "《社会工作实务》第8章"
    },
    {
      "theory_name": "生态系统理论",
      "application": "将服务对象的情绪反应置于其经济与家庭系统背景中理解",
      "source": "Bronfenbrenner, 1979"
    }
  ],
  "ethics_applied": [
    "服务对象自决权",
    "最小伤害原则",
    "专业边界维护"
  ]
}
```

### 7.2 学习记录完整数据结构

```json
{
  "record_id": "REC_20240315_001",
  "student_id": "STU_001",
  "status": "completed",
  "created_at": "2024-03-15T14:30:00Z",
  
  "situation": {
    "raw_description": "今天去社区探访张大爷……",
    "ai_problem_definition": "服务对象因经济困境引发的情绪性沟通拒绝行为",
    "student_confirmed_definition": "大爷因为经济压力情绪失控，拒绝沟通",
    "theory_tags": ["危机介入", "优势视角", "专业关系建立"],
    "similar_cases": ["CASE_2024_001", "CASE_2023_087"]
  },
  
  "decision": {
    "key_moment": "大爷情绪失控，我是否要强行介入？",
    "my_decision": "我选择退出，给大爷情绪空间",
    "decision_reason": "担心强行介入会激化情绪",
    "mental_state": "当时很焦虑，怕被督导认为无能",
    "outcome_eval": "大爷5分钟后主动找我，后续顺利"
  },
  
  "reflection": {
    "rounds": [
      {
        "round": 1,
        "ai_question": "您描述了大爷情绪失控的场景，能具体说说当时大爷的哪些言语或行为让您判断需要退出吗？",
        "student_answer": "他开始大声说话，说不需要我来管……",
        "depth_score": 0.35
      },
      {
        "round": 3,
        "ai_question": "您提到当时担心被督导认为'无能'——这个想法是如何影响您最终做出退出决定的？您认为您的决策更多是基于专业判断还是自我保护？",
        "student_answer": "说实话，两者都有……我确实有点在保护自己……",
        "depth_score": 0.72
      }
    ],
    "final_depth_score": 0.68,
    "ai_summary": "本次反思的核心洞见：您识别出自我情绪（对督导评价的担忧）对专业判断的干扰……"
  },
  
  "research": {
    "suggested_questions": [
      "社工自我情绪管理对危机介入决策的影响",
      "专业关系建立过程中的'自我使用'研究"
    ],
    "selected_question": "社工自我情绪对危机介入专业判断的影响——基于反身性实践的探索",
    "paper_framework": {
      "chapter_1": "研究背景与问题意义",
      "chapter_2": "文献综述：危机介入理论、自我觉察与反身性实践",
      "chapter_3": "研究设计：质性研究，自我民族志方法",
      "chapter_4": "研究发现（基于本次及后续实践记录）",
      "chapter_5": "讨论：自我情绪与专业判断的辩证关系"
    }
  }
}
```

---

## 8. 非功能性需求

### 8.1 性能需求

| 指标 | 要求 | 说明 |
|---|---|---|
| 页面加载时间 | ≤ 2秒 | 核心页面首屏加载 |
| AI响应启动时间 | ≤ 3秒 | 流式输出开始前的等待时间 |
| RAG检索耗时 | ≤ 500ms | 向量检索响应时间 |
| 并发用户数 | 支持100人同时在线 | 按课程班级规模设计 |
| 数据库查询 | ≤ 200ms | 常规查询 |

### 8.2 安全与隐私

| 需求项 | 具体要求 |
|---|---|
| 数据传输 | 全程HTTPS加密传输 |
| 学生隐私 | 案例库中的服务对象信息须脱敏处理，不留真实身份信息 |
| 数据存储 | 学生学习数据存储于国内服务器（阿里云/华为云），满足数据安全法要求 |
| 访问控制 | 基于角色的权限控制（RBAC），学生只能查看自己的记录 |
| API密钥 | 大模型API密钥存储于服务器环境变量，不随代码提交 |
| 日志合规 | AI对话日志不含可识别学生身份信息 |

### 8.3 可用性

- 系统可用率：≥ 99%（教学期间）
- 支持主流浏览器：Chrome 90+、Safari 14+、Edge 90+
- 移动端：支持iOS 14+、Android 10+
- 网络适配：支持校园网环境（部分机构网络限制）

### 8.4 可维护性

- 知识库更新无需停机，支持热更新
- 提示词模板支持教师通过管理界面调整，无需修改代码
- 系统日志完整记录AI调用链，便于问题排查

---

## 9. 项目实施计划

### 9.1 分阶段开发路线图

| 阶段 | 时间 | 主要任务 | 里程碑 |
|---|---|---|---|
| **Phase 0** 基础建设 | 2026年5-7月 | 知识库内容整理、向量数据库搭建、核心提示词设计 | 知识库可用，RAG检索测试通过 |
| **Phase 1** MVP开发 | 2026年8-10月 | 四区核心功能开发、基础教师端 | 完整学习流程可运行 |
| **Phase 2** 教学试点 | 2026年11月-2027年3月 | 在《社会工作行动研究》课程中试运行 | 完成一个完整教学周期 |
| **Phase 3** 迭代优化 | 2027年4-6月 | 基于试点数据优化算法和交互 | 反思深度评分准确率提升 |
| **Phase 4** 拓展推广 | 2027年7-10月 | 延伸至实习环节，总结成果 | 形成可推广的教学范式 |

### 9.2 团队分工

| 角色 | 负责人 | 职责 |
|---|---|---|
| 项目负责人 | 张亦弛 | 整体方向把控、专业内容设计、提示词设计、教学试点 |
| AI技术支持 | 孙凌寒 | RAG系统、大模型接入、AI调度服务 |
| 系统开发 | 合作企业 | 前端、后端、数据库开发与部署 |
| 实验室支持 | 熊远来 | 服务器环境、实验室设备保障 |
| 课程试点 | 金卉 | 协同开展教学试点，提供教学反馈 |

---

## 10. 风险与应对

| 风险类型 | 风险描述 | 应对措施 |
|---|---|---|
| AI输出质量 | 大模型可能生成不准确的专业判断 | 所有AI输出标注"仅供参考"；教师端可审核纠错；建立人工review机制 |
| 隐私保护 | 学生实习记录涉及服务对象个人信息 | 强制脱敏要求；系统无法上传真实姓名等标识符 |
| 学生依赖 | 学生过度依赖AI输出，缺乏独立判断 | AI内容呈现方式设计为"建议"而非"答案"；评价维度中包含"与AI的分歧度" |
| 知识库质量 | 初期案例积累不足，RAG效果有限 | 第一阶段重点建库；允许系统在无案例时仍正常运行 |
| 网络合规 | 境外大模型API在某些网络环境下不稳定 | 优先配置DeepSeek等国内模型；设置自动故障切换 |
| 数据安全 | 学生学习数据的保存与使用边界 | 签署数据使用协议；研究用途数据须脱敏；不向第三方共享 |

---

## 附录

### 附录A：术语说明

| 术语 | 说明 |
|---|---|
| 反身性 | 研究者/实践者对自身与研究对象关系进行持续批判反思的能力 |
| RAG | Retrieval-Augmented Generation，检索增强生成，通过检索知识库增强大模型回答的准确性 |
| 向量数据库 | 将文本转化为数学向量后存储的数据库，支持语义相似度检索 |
| 四区联动 | 本系统核心设计，指情境区、决策区、反思区、研究生成区四个功能区的联动设计 |
| 提示词工程 | 通过设计输入给大模型的指令文本，控制AI输出的质量和方向 |
| 流式输出 | AI回复内容以数据流形式实时推送给前端，形成打字机效果 |

### 附录B：核心API接口清单

| 接口路径 | 方法 | 说明 |
|---|---|---|
| `/api/auth/login` | POST | 用户登录 |
| `/api/records` | POST | 新建学习记录 |
| `/api/records/{id}/situation` | POST | 提交情境描述，触发AI分析 |
| `/api/records/{id}/decision` | POST | 提交决策表单 |
| `/api/records/{id}/reflection` | POST | 提交反思回复，获取AI追问（SSE流式） |
| `/api/records/{id}/research` | POST | 触发研究框架生成 |
| `/api/teacher/students` | GET | 教师查看学生列表及进度 |
| `/api/teacher/students/{id}/records` | GET | 查看特定学生的全部记录 |
| `/api/knowledge/upload` | POST | 上传知识库文档 |
| `/api/knowledge/rebuild` | POST | 重建向量索引（管理员） |

---

*本文档为项目立项评审版本，技术规格可随实施过程中的实际情况进行调整。*  
*编制：张亦弛 | 浙江树人学院公共管理学院 | 2026年5月*
