# 基于 RuoYi-Vue3-FastAPI 的二次开发 PRD

# 生成式AI驱动的反身性学习闭环系统 —— 开发实施文档

| 项目信息 | |
|---|---|
| 文档版本 | v1.0 |
| 编写日期 | 2026年5月25日 |
| 基础框架 | RuoYi-Vue3-FastAPI v1.9.0 |
| 数据库 | PostgreSQL 15+ |
| 项目仓库 | /Users/weifuqiang/Desktop/zhangyichi/RuoYi-Vue3-FastAPI (dev 分支) |

---

## 一、基础框架分析

### 1.1 为什么选择 RuoYi-Vue3-FastAPI

| 维度 | PRD 需求 | 框架现状 | 匹配度 |
|---|---|---|---|
| 前端 | Vue 3 + Element Plus | Vue 3 + Element Plus | 完全一致 |
| 后端 | Python FastAPI | FastAPI + SQLAlchemy (async) | 完全一致 |
| 数据库 | PostgreSQL 15+ | PostgreSQL 已支持（asyncpg 驱动） | 完全一致 |
| 缓存 | Redis | Redis 已集成 | 完全一致 |
| 认证 | JWT + RBAC | OAuth2 + JWT + 完整 RBAC | 完全一致 |
| AI模块 | 多LLM + 流式对话 | AI模型管理 + AI对话（SSE流式） | 可直接扩展 |
| 代码生成 | - | 内置代码生成器 | 加速CRUD开发 |
| 权限管理 | 三角色分流 | 角色/菜单/按钮级权限 | 开箱即用 |
| 容器化 | Docker Compose | Docker Compose（PG版本已有） | 完全一致 |

### 1.2 框架核心模块可复用情况

| 框架模块 | 可复用度 | 改造说明 |
|---|---|---|
| 用户管理（sys_user） | 高 | 扩展角色（student/teacher/admin），新增审核流程 |
| 角色管理（sys_role） | 高 | 配置三个角色及对应菜单权限 |
| 菜单管理（sys_menu） | 高 | 新增四区学习、教师管理、知识库等菜单 |
| 部门管理（sys_dept） | 高 | 映射为学院→系→班级的组织架构 |
| 字典管理（sys_dict） | 高 | 管理场景分类、反思深度等级等枚举数据 |
| 通知公告（sys_notice） | 中 | 改造为任务发布通知、评价反馈通知 |
| AI模型管理 | 高 | 直接复用，新增 DeepSeek Provider |
| AI对话 | 高 | 复用SSE流式输出，改造为四区专用AI引擎 |
| 代码生成器 | 高 | 快速生成知识库、任务等CRUD模块 |

### 1.3 框架开发模式（必须遵循）

若依框架有固定的分层架构，新增业务模块必须遵循：

```
module_{module_name}/
├── controller/          # API路由层 — 使用 APIRouterPro 自动注册
│   └── {table}_controller.py
├── dao/                 # 数据访问层 — 纯SQLAlchemy查询
│   └── {table}_dao.py
├── entity/
│   ├── do/             # 数据对象 — SQLAlchemy ORM模型
│   │   └── {table}_do.py
│   └── vo/             # 值对象 — Pydantic模型（请求/响应）
│       └── {table}_vo.py
└── service/             # 业务逻辑层
    └── {table}_service.py
```

前端对应结构：
```
src/
├── api/{module}/        # API调用
│   └── {feature}.js
└── views/{module}/      # 页面组件
    └── {feature}/
        └── index.vue
```

---

## 二、第一阶段：基础改造 + 情境区 + 决策区

**目标**：在若依框架上完成角色体系改造，实现情境区和决策区的完整功能。

**预计工期**：4-6 周

---

### Phase 1.1：环境搭建与角色体系改造

#### 1.1.1 后端环境配置

| 任务 | 具体内容 |
|---|---|
| 数据库初始化 | 创建 PostgreSQL 数据库 `ruoyi-fastapi`，执行 `sql/ruoyi-fastapi-pg.sql` 初始化脚本 |
| 环境配置 | 配置 `.env.dev`：PostgreSQL 连接信息、Redis 连接信息 |
| 依赖安装 | `pip3 install -r requirements-pg.txt` |
| 启动验证 | `ruoyi app run --env=dev` 启动后端，确认基础功能正常 |
| 前端配置 | `npm install` + `npm run dev`，确认前端可正常访问 |

#### 1.1.2 角色体系改造

**改造思路**：利用若依现有的角色管理（sys_role）+ 菜单权限（sys_menu）体系，不需要修改 User 模型的 role 字段结构，而是通过若依的角色分配机制实现三角色分流。

##### 数据库新增表

```sql
-- 学生信息扩展表（关联 sys_user）
CREATE TABLE edu_student_profile (
    profile_id    BIGSERIAL PRIMARY KEY,
    user_id       BIGINT NOT NULL REFERENCES sys_user(user_id),  -- 关联若依用户
    student_no    VARCHAR(30),                                    -- 学号
    class_id      BIGINT REFERENCES sys_dept(dept_id),           -- 所属班级（复用部门体系）
    major         VARCHAR(100),                                   -- 专业
    grade         VARCHAR(20),                                    -- 年级
    created_by    VARCHAR(64) DEFAULT '',
    create_time   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_by     VARCHAR(64) DEFAULT '',
    update_time   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE edu_student_profile IS '学生信息扩展表';

-- 教师信息扩展表（关联 sys_user）
CREATE TABLE edu_teacher_profile (
    profile_id    BIGSERIAL PRIMARY KEY,
    user_id       BIGINT NOT NULL REFERENCES sys_user(user_id),
    teacher_no    VARCHAR(30),                                    -- 工号
    department_id BIGINT REFERENCES sys_dept(dept_id),           -- 所属院系
    title         VARCHAR(50),                                    -- 职称
    research_area VARCHAR(200),                                   -- 研究方向
    created_by    VARCHAR(64) DEFAULT '',
    create_time   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_by     VARCHAR(64) DEFAULT '',
    update_time   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE edu_teacher_profile IS '教师信息扩展表';

-- 注册审核表
CREATE TABLE edu_registration_audit (
    audit_id      BIGSERIAL PRIMARY KEY,
    user_id       BIGINT NOT NULL REFERENCES sys_user(user_id),
    apply_role    VARCHAR(30) NOT NULL,                           -- 申请的角色标识
    real_name     VARCHAR(50),
    org_name      VARCHAR(200),                                   -- 所属单位
    audit_status  CHAR(1) DEFAULT '0',                            -- 0待审核 1已通过 2已拒绝
    audit_remark  VARCHAR(500),                                   -- 审核备注
    audited_by    BIGINT,                                         -- 审核人
    audited_time  TIMESTAMP,
    created_time  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE edu_registration_audit IS '注册审核表';
```

##### 若依角色配置

在 `sys_role` 表中插入三个角色：

| role_name | role_key | role_sort | data_scope | 说明 |
|---|---|---|---|---|
| 学生 | student | 3 | 5（本人数据） | 只能查看和操作自己的数据 |
| 教师 | teacher | 2 | 4（本部门及以下） | 可查看本班级所有学生数据 |
| 管理员 | admin | 1 | 1（全部数据） | 已存在，无需新建 |

##### 菜单规划

```
根菜单
├── 学习中心（student 角色可见）
│   ├── 我的学习任务
│   ├── 情境描述（情境区）
│   ├── 决策分析（决策区）
│   ├── 反思日志（反思区）
│   └── 研究生成（研究生成区）
├── 教学管理（teacher 角色可见）
│   ├── 班级管理
│   ├── 任务发布
│   ├── 学生进度
│   ├── 内容审核
│   ├── 评价反馈
│   └── 知识库管理
├── 系统管理（admin 角色可见，若依已有）
│   ├── 用户管理（增加审核功能）
│   ├── 角色管理
│   ├── 菜单管理
│   ├── 部门管理
│   └── ...
└── AI管理（若依已有，扩展）
    ├── 模型管理
    └── 对话管理
```

#### 1.1.3 注册审核流程改造

##### 改造文件清单

| 操作 | 文件 | 说明 |
|---|---|---|
| 修改 | `ruoyi-fastapi-backend/module_admin/controller/user_controller.py` | 注册接口增加角色选择和审核状态 |
| 修改 | `ruoyi-fastapi-backend/module_admin/service/user_service.py` | 注册逻辑：创建用户 + 写入审核表 + 分配待审核角色 |
| 新建 | `ruoyi-fastapi-backend/module_admin/controller/audit_controller.py` | 审核管理API |
| 新建 | `ruoyi-fastapi-backend/module_admin/service/audit_service.py` | 审核业务逻辑 |
| 新建 | `ruoyi-fastapi-backend/module_admin/entity/do/audit_do.py` | 审核表ORM模型 |
| 新建 | `ruoyi-fastapi-backend/module_admin/entity/vo/audit_vo.py` | 审核Pydantic模型 |
| 修改 | `ruoyi-fastapi-frontend/src/views/system/user/index.vue` | 用户管理增加审核操作列 |
| 新建 | `ruoyi-fastapi-frontend/src/views/system/audit/index.vue` | 审核管理页面 |
| 修改 | `ruoyi-fastapi-frontend/src/views/register.vue` | 注册页增加角色选择 |

##### 注册流程

```
用户填写注册信息（用户名/密码/邮箱 + 选择角色：student/teacher + 真实姓名/单位）
    ↓
后端创建 sys_user 记录（状态为停用 is_active='1'）
    ↓
写入 edu_registration_audit 表（audit_status='0' 待审核）
    ↓
返回提示"注册成功，请等待管理员审核"
    ↓
管理员在审核管理页面查看 → 通过/拒绝
    ↓
通过 → 激活用户（is_active='0'） + 分配对应角色（sys_user_role）
拒绝 → 记录拒绝原因，用户无法登录
```

##### 登录拦截

在 `module_admin/service/user_service.py` 的 `login` 方法中增加审核状态检查：

```python
# 检查用户是否已通过审核
audit = await AuditDao.get_pending_audit_by_user_id(query_db, user.user_id)
if audit and audit.audit_status == '0':
    raise ServiceException(f'账号待审核，请等待管理员审批')
if audit and audit.audit_status == '2':
    raise ServiceException(f'账号审核未通过：{audit.audit_remark or "请联系管理员"}')
```

---

### Phase 1.2：知识库基础设施建设

#### 1.2.1 向量数据库集成

**新增 Docker 服务**：在 `docker-compose.pg.yml` 中新增 Milvus 向量数据库。

```yaml
# docker-compose.pg.yml 新增
milvus-etcd:
  image: quay.io/coreos/etcd:v3.5.5
  environment:
    - ETCD_AUTO_COMPACTION_MODE=revision
    - ETCD_AUTO_COMPACTION_RETENTION=1000
  volumes:
    - milvus-etcd:/etcd

milvus-minio:
  image: minio/minio:latest
  environment:
    MINIO_ACCESS_KEY: minioadmin
    MINIO_SECRET_KEY: minioadmin
  volumes:
    - milvus-minio:/minio_data
  command: minio server /minio_data

milvus-standalone:
  image: milvusdb/milvus:v2.3.4
  environment:
    ETCD_ENDPOINTS: milvus-etcd:2379
    MINIO_ADDRESS: milvus-minio:9000
  ports:
    - "19530:19530"
  volumes:
    - milvus-data:/var/lib/milvus
  depends_on:
    - milvus-etcd
    - milvus-minio
```

#### 1.2.2 RAG 模块开发

**新建模块**：`ruoyi-fastapi-backend/module_rag/`

```
module_rag/
├── controller/
│   └── rag_controller.py         # RAG管理API（上传文档、检索测试）
├── dao/
│   └── document_dao.py           # 文档元数据CRUD
├── entity/
│   ├── do/
│   │   └── document_do.py        # 知识文档ORM模型
│   └── vo/
│       └── document_vo.py        # Pydantic模型
└── service/
    ├── document_service.py       # 文档管理服务
    ├── embedding_service.py      # 向量化服务
    └── retrieval_service.py      # 检索服务
```

##### 数据库新增表

```sql
-- 知识文档表
CREATE TABLE edu_knowledge_document (
    doc_id        BIGSERIAL PRIMARY KEY,
    title         VARCHAR(200) NOT NULL,
    source_type   VARCHAR(30) NOT NULL,          -- courseware/textbook/paper/case/policy/other
    file_path     VARCHAR(500),
    file_hash     VARCHAR(64),                    -- 文件去重
    chunk_count   INTEGER DEFAULT 0,
    status        CHAR(1) DEFAULT '0',            -- 0待处理 1处理中 2已完成 3失败
    uploaded_by   BIGINT,
    create_time   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    remark        VARCHAR(500)
);
COMMENT ON TABLE edu_knowledge_document IS '知识文档表';

-- 知识文档标签关联表
CREATE TABLE edu_knowledge_tag (
    tag_id        BIGSERIAL PRIMARY KEY,
    tag_name      VARCHAR(50) NOT NULL UNIQUE,
    tag_type      VARCHAR(30),                    -- theory/domain/method/ethics
    create_time   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE edu_knowledge_tag IS '知识标签表';

CREATE TABLE edu_knowledge_document_tag (
    doc_id        BIGINT REFERENCES edu_knowledge_document(doc_id),
    tag_id        BIGINT REFERENCES edu_knowledge_tag(tag_id),
    PRIMARY KEY (doc_id, tag_id)
);
COMMENT ON TABLE edu_knowledge_document_tag IS '文档-标签关联表';
```

##### 向量数据库 Collection 设计

**Milvus Collection: edu_knowledge_chunks**

| 字段 | 类型 | 说明 |
|---|---|---|
| chunk_id | VARCHAR(64) | 主键 |
| doc_id | INT64 | 所属文档ID |
| content | VARCHAR(2000) | 文本块内容 |
| embedding | FLOAT_VECTOR(1024) | bge-large-zh 向量 |
| chunk_index | INT32 | 文档内序号 |
| source_type | VARCHAR(30) | 来源类型 |

##### 核心功能

```
知识入库流程：
  教师上传文档（PDF/Word/TXT）
      ↓
  异步任务：文档解析 → 智能分块（500-1000字，重叠100字）→ bge-large-zh向量化 → 存入Milvus
      ↓
  更新文档状态为"已完成"

知识检索流程：
  用户输入（场景描述/反思文本/研究问题）
      ↓
  输入向量化 → Milvus相似度检索 Top-10 → 可选Cross-Encoder精排 Top-5
      ↓
  将检索结果注入大模型Prompt → 生成专业回答
```

#### 1.2.3 Python 依赖新增

```
# requirements-pg.txt 新增
pymilvus>=2.3.0
langchain>=0.1.0
langchain-community>=0.0.10
sentence-transformers>=2.2.0
PyMuPDF>=1.23.0
python-docx>=1.0.0
python-pptx>=0.6.21
```

---

### Phase 1.3：情境区（Scenario Zone）开发

#### 1.3.1 功能目标

学生描述实践场景，AI辅助识别关键问题、标注事件节点、关联专业理论。

#### 1.3.2 数据库新增表

```sql
-- 教学任务表
CREATE TABLE edu_task (
    task_id       BIGSERIAL PRIMARY KEY,
    teacher_id    BIGINT NOT NULL REFERENCES sys_user(user_id),
    title         VARCHAR(200) NOT NULL,
    description   TEXT,
    scenario_config  JSONB,                       -- 情境区AI配置（提示词、引导策略等）
    decision_config   JSONB,                      -- 决策区AI配置
    reflection_config JSONB,                      -- 反思区AI配置
    research_config   JSONB,                      -- 研究区AI配置
    deadline      TIMESTAMP,
    status        CHAR(1) DEFAULT '0',             -- 0草稿 1已发布 2已关闭
    create_time   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE edu_task IS '教学任务表';

-- 任务-班级关联表
CREATE TABLE edu_task_class (
    task_id       BIGINT REFERENCES edu_task(task_id),
    dept_id       BIGINT REFERENCES sys_dept(dept_id),   -- 复用部门表作为班级
    PRIMARY KEY (task_id, dept_id)
);
COMMENT ON TABLE edu_task_class IS '任务-班级关联表';

-- 学习记录主表（四区联动核心）
CREATE TABLE edu_learning_record (
    record_id     BIGSERIAL PRIMARY KEY,
    task_id       BIGINT NOT NULL REFERENCES edu_task(task_id),
    student_id    BIGINT NOT NULL REFERENCES sys_user(user_id),
    current_zone  VARCHAR(20) DEFAULT 'scenario',  -- scenario/decision/reflection/research
    status        CHAR(1) DEFAULT '0',              -- 0进行中 1已提交 2已评价
    create_time   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    submit_time   TIMESTAMP,
    UNIQUE(task_id, student_id)                     -- 一个任务一条记录
);
COMMENT ON TABLE edu_learning_record IS '学习记录主表';

-- 情境区数据表
CREATE TABLE edu_scenario_data (
    scenario_id     BIGSERIAL PRIMARY KEY,
    record_id       BIGINT NOT NULL REFERENCES edu_learning_record(record_id),
    student_id      BIGINT NOT NULL REFERENCES sys_user(user_id),
    description     TEXT NOT NULL,                    -- 场景描述文本
    key_events      JSONB,                           -- 标注的关键事件节点
    identified_problems JSONB,                       -- AI识别的问题列表
    category_tags   JSONB,                           -- 场景分类标签
    followup_history JSONB,                          -- AI追问历史
    ai_analysis     JSONB,                           -- AI分析结果（问题界定、理论推荐等）
    status          CHAR(1) DEFAULT '0',              -- 0草稿 1已确认
    create_time     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE edu_scenario_data IS '情境区数据表';

-- 情境区AI对话记录表
CREATE TABLE edu_scenario_dialogue (
    dialogue_id   BIGSERIAL PRIMARY KEY,
    scenario_id   BIGINT NOT NULL REFERENCES edu_scenario_data(scenario_id),
    role          VARCHAR(20) NOT NULL,               -- user / assistant
    content       TEXT NOT NULL,
    token_count   INTEGER,
    create_time   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE edu_scenario_dialogue IS '情境区AI对话记录表';
```

#### 1.3.3 后端开发

**新建模块**：`ruoyi-fastapi-backend/module_learning/`

```
module_learning/
├── controller/
│   ├── scenario_controller.py      # 情境区API
│   └── task_controller.py          # 任务API
├── dao/
│   ├── scenario_dao.py
│   ├── task_dao.py
│   └── record_dao.py
├── entity/
│   ├── do/
│   │   ├── scenario_do.py
│   │   ├── task_do.py
│   │   └── record_do.py
│   └── vo/
│       ├── scenario_vo.py
│       ├── task_vo.py
│       └── record_vo.py
└── service/
    ├── scenario_service.py
    ├── task_service.py
    └── record_service.py
```

##### 情境区 API 设计

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/learning/scenario/create` | 创建情境描述（关联学习记录） |
| PUT | `/learning/scenario/update` | 更新情境描述文本 |
| POST | `/learning/scenario/analyze` | AI分析情境（识别问题+推荐理论） |
| POST | `/learning/scenario/followup` | AI追问（补充关键信息） |
| POST | `/learning/scenario/highlight` | 标注关键事件节点 |
| PUT | `/learning/scenario/confirm` | 确认情境描述完成，流转到决策区 |
| GET | `/learning/scenario/detail/{id}` | 获取情境详情 |

##### 情境区 AI Prompt 设计

复用若依现有的 AI 对话架构（`module_ai`），改造为情境区专用引擎。

```python
# 情境区系统提示词模板
SCENARIO_SYSTEM_PROMPT = """你是一位经验丰富的社会工作督导，擅长帮助实习社工分析实践情境。

任务：根据学生描述的实践场景，完成以下工作：
1. 识别场景中的关键事件节点（标注为 1、2、3...）
2. 界定其中蕴含的专业问题（2-3个），每个问题需说明：
   - 问题描述
   - 涉及的社会工作实践领域
   - 相关的专业理论视角
3. 提出追问建议（2-3个），帮助学生补充关键信息

专业知识参考：
{retrieved_knowledge}

输出格式要求（JSON）：
{{
    "key_events": ["事件1", "事件2", ...],
    "problems": [
        {{
            "title": "问题标题",
            "description": "问题说明",
            "domain": "实践领域",
            "theories": ["理论1", "理论2"]
        }}
    ],
    "followup_questions": ["追问1", "追问2", ...],
    "category_tags": ["标签1", "标签2"]
}}
"""
```

#### 1.3.4 前端开发

**新增页面文件**：

```
src/views/learning/
├── task-list/
│   └── index.vue                   # 学习任务列表
├── scenario/
│   ├── index.vue                   # 情境区主页面
│   └── components/
│       ├── DescriptionEditor.vue   # 场景描述编辑器
│       ├── AIChatPanel.vue         # AI对话面板（复用若依AI对话组件）
│       ├── ProblemPanel.vue        # 问题识别面板
│       ├── KeyEventTagger.vue      # 关键事件标注组件
│       └── TheoryCard.vue          # 理论推荐卡片
```

##### 前端交互设计

```
情境区页面布局：
┌─────────────────────────────────────────────────────┐
│  学习任务：XXX    当前阶段：情境描述 [1/4]             │
├──────────────────────────┬──────────────────────────┤
│                          │                          │
│   场景描述编辑器          │   AI 对话面板             │
│   （富文本编辑区）        │   （流式对话）            │
│                          │                          │
│   [AI辅助提问] [AI分析]   │   → AI追问建议            │
│                          │   → 问题识别结果          │
│                          │   → 理论关联推荐          │
├──────────────────────────┴──────────────────────────┤
│  关键事件节点标注区                                    │
│  ● 事件1 ─── ● 事件2 ─── ● 事件3                     │
├─────────────────────────────────────────────────────┤
│  识别的专业问题：                                     │
│  □ 问题1: 服务对象阻抗...  □ 问题2: 伦理决策...       │
├─────────────────────────────────────────────────────┤
│            [保存草稿]  [确认完成，进入决策区 →]         │
└─────────────────────────────────────────────────────┘
```

---

### Phase 1.4：决策区（Decision Zone）开发

#### 1.4.1 功能目标

基于情境区识别的关键问题，学生进行伦理决策分析，AI提供伦理守则参照和替代方案建议。

#### 1.4.2 数据库新增表

```sql
-- 决策区数据表
CREATE TABLE edu_decision_data (
    decision_id      BIGSERIAL PRIMARY KEY,
    record_id        BIGINT NOT NULL REFERENCES edu_learning_record(record_id),
    scenario_id      BIGINT NOT NULL REFERENCES edu_scenario_data(scenario_id),
    student_id       BIGINT NOT NULL REFERENCES sys_user(user_id),
    key_event        TEXT NOT NULL,                    -- 关键节点描述
    is_intervened    BOOLEAN,                         -- 是否介入
    action_taken     TEXT,                            -- 具体行动
    reasoning        TEXT,                            -- 行动理由
    psychological_state TEXT,                         -- 心理活动
    alternatives     TEXT,                            -- 替代方案
    expected_outcome TEXT,                            -- 预期结果
    actual_outcome   TEXT,                            -- 实际结果（事后补充）
    ethics_analysis  JSONB,                           -- AI伦理分析结果
    create_time      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE edu_decision_data IS '决策区数据表';

-- 决策区AI对话记录表
CREATE TABLE edu_decision_dialogue (
    dialogue_id   BIGSERIAL PRIMARY KEY,
    decision_id   BIGINT NOT NULL REFERENCES edu_decision_data(decision_id),
    role          VARCHAR(20) NOT NULL,
    content       TEXT NOT NULL,
    token_count   INTEGER,
    create_time   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE edu_decision_dialogue IS '决策区AI对话记录表';
```

#### 1.4.3 后端开发

在 `module_learning/` 中扩展：

```
module_learning/
├── controller/
│   ├── scenario_controller.py
│   ├── decision_controller.py      # 新增：决策区API
│   └── task_controller.py
├── dao/
│   ├── scenario_dao.py
│   ├── decision_dao.py             # 新增
│   ├── task_dao.py
│   └── record_dao.py
├── entity/
│   ├── do/
│   │   ├── scenario_do.py
│   │   ├── decision_do.py          # 新增
│   │   ├── task_do.py
│   │   └── record_do.py
│   └── vo/
│       ├── scenario_vo.py
│       ├── decision_vo.py          # 新增
│       ├── task_vo.py
│       └── record_vo.py
└── service/
    ├── scenario_service.py
    ├── decision_service.py         # 新增
    ├── task_service.py
    └── record_service.py
```

##### 决策区 API 设计

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/learning/decision/create` | 创建决策记录 |
| PUT | `/learning/decision/update` | 更新决策内容 |
| POST | `/learning/decision/ethics` | AI伦理分析（检索伦理守则+评估决策） |
| POST | `/learning/decision/alternatives` | AI生成替代方案 |
| POST | `/learning/decision/compare` | AI对比不同决策路径后果 |
| PUT | `/learning/decision/confirm` | 确认决策完成，流转到反思区 |
| GET | `/learning/decision/list/{record_id}` | 获取某学习记录的所有决策 |

##### 决策区 AI Prompt 设计

```python
DECISION_SYSTEM_PROMPT = """你是一位社会工作伦理教育专家，擅长帮助学生进行伦理决策分析。

任务：根据学生的决策记录和实践情境，完成以下工作：
1. 识别决策中涉及的伦理维度（如自决权、保护义务、保密原则等）
2. 引用相关的社会工作伦理守则条款
3. 评估决策的合理性
4. 提出替代视角和方案
5. 建议进一步思考的问题

参考的社会工作伦理守则：
{retrieved_ethics}

历史案例参考：
{retrieved_cases}

学生决策记录：
{decision_data}

相关情境描述：
{scenario_data}

请以专业但鼓励的语气回复，帮助学生看到自身决策的多面性。
"""
```

#### 1.4.4 前端开发

```
src/views/learning/
├── decision/
│   ├── index.vue                   # 决策区主页面
│   └── components/
│       ├── DecisionTimeline.vue    # 关键节点时间线
│       ├── DecisionForm.vue        # 决策记录表单
│       ├── EthicsPanel.vue         # 伦理参照面板
│       ├── AlternativeCompare.vue  # 方案对比视图
│       └── HistoryReference.vue    # 历史案例参考
```

##### 决策区页面布局

```
决策区页面布局：
┌─────────────────────────────────────────────────────┐
│  学习任务：XXX    当前阶段：决策分析 [2/4]             │
├─────────────────────────────────────────────────────┤
│  关键事件时间线：                                     │
│  ● 张大爷自我封闭 ── ● 沟通口角 ── ● 情绪失控         │
│  （当前正在分析：节点3）                               │
├──────────────────────────┬──────────────────────────┤
│                          │                          │
│   决策记录表单            │   AI 伦理分析面板         │
│   □ 是否介入：☑是        │   伦理维度：              │
│   具体行动：_______       │   1. 自决权 vs 保护义务   │
│   行动理由：_______       │   2. 专业关系边界         │
│   心理活动：_______       │                          │
│   替代方案：_______       │   相关守则条款：           │
│   预期结果：_______       │   NASW 1.02 自决权        │
│                          │                          │
│   [AI伦理分析] [AI替代方案]│  建议进一步思考：          │
│                          │  → 如果拒绝你会怎么做？    │
├──────────────────────────┴──────────────────────────┤
│            [← 返回情境区]  [保存草稿]  [确认，进入反思区 →] │
└─────────────────────────────────────────────────────┘
```

---

### Phase 1.5：四区状态机引擎

#### 1.5.1 状态流转设计

```
学习记录状态流转：

  ┌──────────┐  创建记录  ┌──────────┐
  │   无记录   │ ────────→ │  情境区   │
  └──────────┘           │ (editing) │
                          └────┬─────┘
                               │ 确认情境
                               ↓
                          ┌──────────┐
                          │  决策区   │
                          │ (editing) │
                          └────┬─────┘
                               │ 确认决策
                               ↓
                          ┌──────────┐
                          │  反思区   │  ←── 第二阶段
                          │ (editing) │
                          └────┬─────┘
                               │ 确认反思
                               ↓
                          ┌──────────┐
                          │ 研究生成区│  ←── 第二阶段
                          │ (editing) │
                          └────┬─────┘
                               │ 提交成果
                               ↓
                          ┌──────────┐
                          │  已提交   │
                          │(submitted)│
                          └────┬─────┘
                               │ 教师评价
                               ↓
                          ┌──────────┐
                          │  已评价   │
                          │(reviewed) │
                          └──────────┘
```

**关键规则**：
- 学生可自由回溯到前序区域修改（如反思区修改内容后返回情境区补充）
- 回溯修改不重置后序区域的状态，但 AI 分析结果会标记为"待更新"
- 每个区域有"草稿"和"已确认"两种状态

#### 1.5.2 后端实现

在 `module_learning/service/record_service.py` 中实现：

```python
class LearningRecordService:
    # 允许的区段流转关系
    ZONE_TRANSITIONS = {
        'scenario': ['decision'],           # 情境区 → 决策区
        'decision': ['scenario', 'reflection'],  # 决策区 → 情境区/反思区
        'reflection': ['decision', 'research'],   # 反思区 → 决策区/研究区
        'research': ['reflection'],          # 研究区 → 反思区
    }

    @classmethod
    async def transition_zone(cls, db, record_id, target_zone, student_id):
        """区段流转"""
        record = await RecordDao.get_by_id(db, record_id)
        # 校验：必须是自己的记录
        if record.student_id != student_id:
            raise ServiceException("无权操作他人的学习记录")
        # 校验：目标区段是否在允许的流转范围内
        if target_zone not in cls.ZONE_TRANSITIONS.get(record.current_zone, []):
            raise ServiceException(f"不允许从 {record.current_zone} 直接跳转到 {target_zone}")
        # 校验：前序区域是否已完成
        await cls._check_prerequisite(db, record, target_zone)
        # 执行流转
        await RecordDao.update_zone(db, record_id, target_zone)
```

---

## 三、第二阶段：反思区 + 研究生成区 + 教师管理端

**目标**：完成四区闭环，建设教师管理端，实现完整的教与学流程。

**预计工期**：6-8 周

---

### Phase 2.1：反思区（Reflection Zone）开发

#### 2.1.1 功能目标

这是系统的**核心创新模块**。通过AI驱动的三层递进提问策略，引导学生从"描述经历"走向"反身性反思"。

#### 2.1.2 数据库新增表

```sql
-- 反思区数据表
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
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE edu_reflection_data IS '反思区数据表';

-- 反思区AI对话记录表（核心：结构化提问链）
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

-- 反思深度演变记录表（追踪学生思维变化轨迹）
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

#### 2.1.3 反思深度评估算法

```python
# 反思深度评估维度和评分规则
REFLECTION_DEPTH_RUBRIC = {
    "descriptive": {
        "score_range": (0.20, 0.40),
        "indicators": [
            "仅复述事件经过",
            "描述个人感受但缺乏分析",
            "未涉及原因或动机",
            "停留在表面观察"
        ]
    },
    "analytical": {
        "score_range": (0.50, 0.70),
        "indicators": [
            "开始分析事件原因和互动模式",
            "讨论策略选择的依据",
            "关注到服务对象的行为模式",
            "尝试用专业知识解释现象"
        ]
    },
    "reflexive": {
        "score_range": (0.80, 1.00),
        "indicators": [
            "审视自身价值观对实践的影响",
            "反思自身权力位置和专业角色",
            "认识到自身经验对判断的塑造",
            "从服务对象视角重新理解情境",
            "形成对专业实践本质的新认识"
        ]
    }
}
```

#### 2.1.4 AI结构化提问策略

```python
REFLECTION_SYSTEM_PROMPT = """你是一位引导反思的社会工作教育者。

当前学生信息：
- 学习任务：{task_title}
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
2. 基于当前层次，生成2-3个推动反思深化的追问（从下一层次出发）
3. 关联1-2个相关的社会工作理论或社会学概念
4. 提供理论依据说明为什么这种关联成立

专业知识参考：
{retrieved_knowledge}

重要原则：
- 追问必须具有针对性，不要泛泛而谈
- 每个追问都要有明确目标——推动学生进入更深一层的反思
- 当学生已达到反身性层次时，帮助其巩固和深化
- 避免一次性给出过多理论，避免让学生感到压力
- 语气要温暖鼓励，而非评判
"""
```

#### 2.1.5 后端 API 设计

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/learning/reflection/create` | 创建反思记录 |
| PUT | `/learning/reflection/update` | 更新反思内容 |
| POST | `/learning/reflection/questions` | AI生成结构化提问 |
| GET | `/learning/reflection/depth/{id}` | 获取反思深度评估 |
| GET | `/learning/reflection/depth-history/{id}` | 获取深度变化曲线数据 |
| PUT | `/learning/reflection/confirm` | 确认反思完成，流转到研究区 |

#### 2.1.6 前端开发

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

##### 反思区页面布局

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
│                          │   📗 赋权理论              │
│                          │   📗 反压迫实践            │
│                          │                          │
│                          │   [推送追问] [换一组问题]    │
├──────────────────────────┴──────────────────────────┤
│  [← 返回决策区]  [保存草稿]  [确认，进入研究生成区 →]   │
└─────────────────────────────────────────────────────┘
```

---

### Phase 2.2：研究生成区（Research Generation Zone）开发

#### 2.2.1 数据库新增表

```sql
-- 研究生成区数据表
CREATE TABLE edu_research_data (
    research_id      BIGSERIAL PRIMARY KEY,
    record_id        BIGINT NOT NULL REFERENCES edu_learning_record(record_id),
    scenario_id      BIGINT NOT NULL REFERENCES edu_scenario_data(scenario_id),
    student_id       BIGINT NOT NULL REFERENCES sys_user(user_id),
    research_question TEXT,                            -- 研究问题
    question_candidates JSONB,                        -- AI生成的研究问题候选列表
    framework        JSONB,                           -- 论文框架（结构化大纲）
    draft_content    TEXT,                            -- 论文初稿内容
    references       JSONB,                           -- 推荐文献列表
    logic_check      JSONB,                           -- AI逻辑审查结果
    status           CHAR(1) DEFAULT '0',              -- 0草稿 1已提交
    create_time      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    submit_time      TIMESTAMP
);
COMMENT ON TABLE edu_research_data IS '研究生成区数据表';

-- 研究生成区AI对话记录表
CREATE TABLE edu_research_dialogue (
    dialogue_id   BIGSERIAL PRIMARY KEY,
    research_id   BIGINT NOT NULL REFERENCES edu_research_data(research_id),
    role          VARCHAR(20) NOT NULL,
    content       TEXT NOT NULL,
    action_type   VARCHAR(30),                        -- question_gen/framework_gen/draft_help/logic_check/refine
    token_count   INTEGER,
    create_time   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE edu_research_dialogue IS '研究生成区AI对话记录表';
```

#### 2.2.2 后端 API 设计

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/learning/research/create` | 创建研究记录 |
| POST | `/learning/research/questions` | AI生成候选研究问题 |
| POST | `/learning/research/framework` | AI生成论文框架 |
| POST | `/learning/research/draft` | AI辅助段落撰写 |
| POST | `/learning/research/logic-check` | AI逻辑审查 |
| POST | `/learning/research/refine` | AI语言润色 |
| POST | `/learning/research/references` | AI推荐文献 |
| PUT | `/learning/research/submit` | 提交最终成果 |

#### 2.2.3 前端开发

```
src/views/learning/
├── research/
│   ├── index.vue                       # 研究生成区主页面
│   └── components/
│       ├── MaterialSummary.vue         # 材料汇总面板
│       ├── QuestionGenerator.vue       # 研究问题生成器
│       ├── FrameworkEditor.vue         # 论文框架编辑器（拖拽排序）
│       ├── DraftEditor.vue             # 论文撰写编辑器
│       ├── ReferenceList.vue           # 文献推荐列表
│       └── LogicCheckReport.vue        # 逻辑审查报告
```

---

### Phase 2.3：教师管理端开发

#### 2.3.1 教学任务管理

##### 数据库（已在 Phase 1.3 创建 edu_task 表）

##### 后端 API 设计

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/teacher/task/create` | 创建教学任务 |
| PUT | `/teacher/task/update` | 修改任务 |
| PUT | `/teacher/task/publish` | 发布任务（指定班级） |
| PUT | `/teacher/task/close` | 关闭任务 |
| GET | `/teacher/task/list` | 教师的任务列表 |
| GET | `/teacher/task/detail/{id}` | 任务详情 |

##### 前端开发

```
src/views/teaching/
├── task/
│   ├── index.vue                   # 任务列表
│   └── detail.vue                  # 任务详情/编辑
├── progress/
│   ├── index.vue                   # 班级进度看板
│   ├── student-detail.vue          # 学生个人详情
│   └── components/
│       ├── ProgressDashboard.vue   # 四区完成率看板
│       ├── DepthTrendChart.vue     # 反思深度趋势图
│       └── ZoneHeatmap.vue         # 四区活跃度热力图
├── review/
│   ├── index.vue                   # 内容审核列表
│   └── detail.vue                  # 审核详情
├── evaluation/
│   ├── index.vue                   # 评价管理
│   └── detail.vue                  # 评价详情（含批注）
├── knowledge/
│   ├── index.vue                   # 知识库管理
│   └── upload.vue                  # 文档上传
└── dashboard/
    └── index.vue                   # 教学数据看板
```

#### 2.3.2 学生进度监控

| 功能 | 说明 |
|---|---|
| 班级看板 | 显示班级全体学生的四区完成率、平均反思深度、高频问题 |
| 个人详情 | 查看单个学生的完整学习过程（情境→决策→反思→研究） |
| 对话记录 | 查看学生与AI的互动记录，了解学生的思考过程 |
| 深度趋势 | 可视化展示学生的反思深度变化曲线 |
| 警报提醒 | 反思内容涉及高风险情境时，系统自动标记提醒教师 |

#### 2.3.3 评价反馈系统

##### 数据库新增表

```sql
-- 教师评价表
CREATE TABLE edu_evaluation (
    evaluation_id  BIGSERIAL PRIMARY KEY,
    record_id      BIGINT NOT NULL REFERENCES edu_learning_record(record_id),
    teacher_id     BIGINT NOT NULL REFERENCES sys_user(user_id),
    student_id     BIGINT NOT NULL REFERENCES sys_user(user_id),
    score          DECIMAL(5,2),                       -- 总评分
    scenario_score DECIMAL(5,2),                       -- 情境区评分
    decision_score DECIMAL(5,2),                       -- 决策区评分
    reflection_score DECIMAL(5,2),                     -- 反思区评分
    research_score DECIMAL(5,2),                       -- 研究区评分
    feedback       TEXT,                               -- 文字反馈
    is_excellent   BOOLEAN DEFAULT FALSE,              -- 是否标记为优秀案例
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(record_id, teacher_id)
);
COMMENT ON TABLE edu_evaluation IS '教师评价表';

-- 教师批注表
CREATE TABLE edu_annotation (
    annotation_id  BIGSERIAL PRIMARY KEY,
    evaluation_id  BIGINT NOT NULL REFERENCES edu_evaluation(evaluation_id),
    zone           VARCHAR(20) NOT NULL,                -- scenario/decision/reflection/research
    target_id      BIGINT NOT NULL,                     -- 对应区域的数据ID
    quote_text     TEXT,                                -- 引用的学生原文片段
    comment        TEXT NOT NULL,                       -- 教师批注内容
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE edu_annotation IS '教师批注表';
```

#### 2.3.4 警报系统

##### 数据库新增表

```sql
-- 风险警报表
CREATE TABLE edu_alert (
    alert_id       BIGSERIAL PRIMARY KEY,
    student_id     BIGINT NOT NULL REFERENCES sys_user(user_id),
    record_id      BIGINT REFERENCES edu_learning_record(record_id),
    zone           VARCHAR(20),                         -- 触发区域
    alert_type     VARCHAR(30) NOT NULL,                -- safety/ethical/privacy/emotional
    alert_level    CHAR(1) NOT NULL,                    -- 0低 1中 2高
    trigger_content TEXT,                               -- 触发警报的原文片段
    trigger_rule   VARCHAR(200),                        -- 触发的规则描述
    status         CHAR(1) DEFAULT '0',                 -- 0未处理 1已处理 2已忽略
    handled_by     BIGINT,                              -- 处理人
    handle_remark  TEXT,                                -- 处理备注
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    handle_time    TIMESTAMP
);
COMMENT ON TABLE edu_alert IS '风险警报表';
```

##### 警报触发规则

```python
ALERT_RULES = {
    "safety": {
        "level": "2",  # 高
        "keywords": ["自杀", "自残", "伤害", "暴力", "虐待", "性侵"],
        "description": "涉及人身安全相关内容"
    },
    "ethical": {
        "level": "1",  # 中
        "keywords": ["违反伦理", "泄密", "收礼", "双重关系"],
        "description": "涉及伦理违规风险"
    },
    "emotional": {
        "level": "1",  # 中
        "keywords": ["崩溃", "受不了", "绝望", "恐惧", "无助"],
        "description": "学生情绪异常"
    },
    "privacy": {
        "level": "0",  # 低
        "keywords": ["身份证号", "手机号", "家庭住址", "病历"],
        "description": "可能涉及隐私信息泄露"
    }
}
```

---

### Phase 2.4：评价报告系统

#### 2.4.1 数据库新增表

```sql
-- 班级统计报告表（定时生成）
CREATE TABLE edu_class_report (
    report_id      BIGSERIAL PRIMARY KEY,
    teacher_id     BIGINT NOT NULL REFERENCES sys_user(user_id),
    dept_id        BIGINT NOT NULL REFERENCES sys_dept(dept_id),
    task_id        BIGINT REFERENCES edu_task(task_id),
    report_type    VARCHAR(20) NOT NULL,                -- task_summary/period_summary
    statistics     JSONB NOT NULL,                      -- 统计数据（完成率、深度分布等）
    generate_time  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE edu_class_report IS '班级统计报告表';
```

#### 2.4.2 统计指标

| 维度 | 指标 |
|---|---|
| 参与情况 | 四区完成率、平均用时、活跃时段分布 |
| 反思质量 | 平均反思深度、深度等级分布、深度变化趋势 |
| 问题分布 | 高频识别问题TOP10、高频理论关联TOP10 |
| 伦理决策 | 决策类型分布、伦理冲突高频词 |
| 研究产出 | 研究问题分类、论文框架类型分布 |

---

## 四、技术实施要点

### 4.1 AI 调用架构

复用若依 `module_ai` 的现有架构，在其基础上扩展：

```
若依 AI 模块现有架构：
  module_ai/
  ├── controller/
  │   ├── ai_model_controller.py     # 模型管理（已有）
  │   └── ai_chat_controller.py      # AI对话（已有，SSE流式）
  ├── entity/
  ├── service/
  │   ├── ai_model_service.py
  │   └── ai_chat_service.py         # 基于agno框架的对话服务
  └── ...

扩展方案：
  新增 module_learning/service/ai_engine.py  # 四区AI调度引擎
    - 复用 ai_chat_service.py 的流式输出机制
    - 复用 ai_model_service.py 的模型管理
    - 新增：Prompt模板管理、RAG检索注入、深度评分
```

### 4.2 大模型选型

| 用途 | 推荐模型 | 说明 |
|---|---|---|
| 通用对话与分析 | DeepSeek-V3 API | 国内合规，中文能力强，性价比优 |
| Embedding | bge-large-zh-v1.5（本地部署） | 中文文本向量化开源SOTA |
| 重排序 | bge-reranker-large | Cross-Encoder精排 |

### 4.3 依赖新增汇总

```
# Python 后端新增依赖（添加到 requirements-pg.txt）
pymilvus>=2.3.0
langchain>=0.1.0
langchain-community>=0.0.10
sentence-transformers>=2.2.0
PyMuPDF>=1.23.0
python-docx>=1.0.0
python-pptx>=0.6.21
FlagEmbedding>=1.2.0
```

### 4.4 Docker 部署架构

```
docker-compose.pg.yml 扩展：
├── nginx           （已有）
├── ruoyi-backend   （已有）
├── ruoyi-frontend  （已有）
├── postgresql      （已有）
├── redis           （已有）
├── milvus-standalone （新增：向量数据库）
├── milvus-etcd      （新增：Milvus依赖）
└── milvus-minio     （新增：Milvus存储）
```

---

## 五、开发排期总览

### 第一阶段（4-6 周）

| 周次 | Phase | 核心交付 |
|---|---|---|
| 第1周 | Phase 1.1 | 环境搭建完成 + 角色体系改造 + 注册审核流程 |
| 第2周 | Phase 1.2 | Milvus集成 + RAG模块基础功能 + 知识文档入库 |
| 第3-4周 | Phase 1.3 | 情境区完整功能（前后端 + AI分析 + RAG检索） |
| 第5-6周 | Phase 1.4 | 决策区完整功能 + 四区状态机引擎 |

### 第二阶段（6-8 周）

| 周次 | Phase | 核心交付 |
|---|---|---|
| 第7-9周 | Phase 2.1 | 反思区完整功能 + 深度评估算法 + 提问策略 |
| 第10-11周 | Phase 2.2 | 研究生成区完整功能 |
| 第12-14周 | Phase 2.3 | 教师管理端（任务管理 + 进度监控 + 评价反馈） |
| 第15周 | Phase 2.4 | 警报系统 + 评价报告 + 知识库内容导入 |

---

## 六、与原 PRD 的对照说明

| 原 PRD 模块 | 本文档对应 | 状态 |
|---|---|---|
| 知识库管理模块 | Phase 1.2 | RAG模块 + Milvus |
| 情境区（Scenario Zone） | Phase 1.3 | 完整实现 |
| 决策区（Decision Zone） | Phase 1.4 | 完整实现 |
| 反思区（Reflection Zone） | Phase 2.1 | 完整实现（含深度评估算法） |
| 研究生成区（Research Generation） | Phase 2.2 | 完整实现 |
| 教师管理端 | Phase 2.3 | 完整实现 |
| 数据安全与合规 | 全程贯穿 | 复用若依RBAC + 数据隔离 + AI合规标注 |
| 部署方案 | Phase 1.1 | 扩展 docker-compose.pg.yml |
