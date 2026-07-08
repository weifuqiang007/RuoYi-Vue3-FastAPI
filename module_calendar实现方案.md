# module_calendar 日历提醒 — 实现方案

> **版本**：V1.0
> **日期**：2026-07-01
> **用途**：在已抽好的 RuoYi-FastAPI 框架模板上，落地第一个**共享业务积木** `module_calendar`（日历 + 提醒），作为律师代理助理产品与反身性研修系统共用的基础能力。
> **关联文档**：
> - 架构总纲：[框架拆分与多端架构方案.md](ruoyi-fastapi-backend/fanshenxingwendang/框架拆分与多端架构/框架拆分与多端架构方案.md)
> - 需求原始记录：[框架集成.md](框架集成.md)
> - 模板仓：https://github.com/weifuqiang007/ruoyi-fastapi-template

---

## 目录

- [一、实现背景](#一实现背景)
- [二、已锁定的四项决策](#二已锁定的四项决策)
- [三、整体实现路径（Phase 0–6）](#三整体实现路径phase-06)
- [四、技术实现方案（选型）](#四技术实现方案选型)
- [五、后端方案（module_calendar）](#五后端方案module_calendar)
- [六、前端方案](#六前端方案)
- [七、具体模块分工](#七具体模块分工)
- [八、框架更新流转机制](#八框架更新流转机制)
- [九、风险与注意点](#九风险与注意点)
- [十、验收标准](#十验收标准)

---

## 一、实现背景

### 1.1 多端目标

需要覆盖：手机 App（安卓 / iOS）、电脑桌面应用（Windows / Mac）、网页端；小程序保留能力但非优先。要求**一套代码、一次打包多端**，方便维护。

### 1.2 两个产品共享一套框架

| 产品 | 终端用户 | 业务模块 |
|---|---|---|
| **律师代理助理**（产品 B） | 律师 / 客户 | `module_lawyer_case`（诉状 OCR + 流程标准化，**第一期不做**） |
| **反身性研修系统**（产品 A） | 教师 / 学生 | `module_learning` / `module_rag`（已在母仓 `g:/zhangyichi`） |

两个产品都需要的通用能力（日历提醒、消息推送）抽成**共享积木**，长在框架模板里。

### 1.3 律师产品的第一条需求

> 她来说任务，一般都是在什么时候提醒我做什么事情。

即：**语音说一句话 → 系统识别出"时间 + 事件" → 到点提醒**。这是 `module_calendar` 要解决的核心。

### 1.4 框架现状（已就绪，可直接加业务）

| 阶段 | 内容 | 状态 |
|---|---|---|
| Phase 1｜清耦合 | 4 个耦合点全部清除，框架↔业务双向解耦 | ✅ 完成 |
| Phase 2｜抽后端模板 | 模板仓 `ruoyi-fastapi-template`（remote `template/main` = 本地分支 `template-backend` = commit `6a1833c`，worktree `G:/ruoyi-fastapi-template`） | ✅ 完成 |
| Phase 3｜共享积木 | `module_calendar` / `module_push` | ⬜ **本文档** |
| Phase 4｜律师后端 | `module_lawyer_case` | ⬜ 后续 |
| Phase 5｜多端前端 | uni-app app + Tauri 桌面 + 后台扩展 | ⬜ 部分有骨架 |
| Phase 6｜反身性融合 | 母仓结构对齐 template | ⬜ 后续 |

**模板仓已含基建**：`module_admin`（RBAC）、`module_ai`（litellm 文本/图片对话）、`module_generator`、`config/get_scheduler.py`（完整 APScheduler + Redis 锁）、`config/get_minio.py`（对象存储）。

**已确认的承重点**：
- 调度器：全局 `scheduler`（AsyncIOScheduler 单例）+ `SchedulerUtil`，`server.py:33` 启动初始化。定时任务走 `sys_job` 表 + leader 锁（多 worker 安全）。
- 钩子接入点：`server.py:175` `LifecycleHooks.discover_and_load()` → `:103` `run_startup`。`module_*/hooks.py` 自动发现。
- 路由范式：`APIRouterPro(prefix='/...', order_num=N, tags=[...], dependencies=[PreAuthDependency()])`，放 `module_xxx/controller/` 自动挂载。
- 建表：`entity/do` 里的 SQLAlchemy 模型被 `find_models` 自动发现，首次启动 `init_create_table()` 自动建表。
- **缺口**：模板**无 WebSocket/SSE** 实时推送；`module_ai` **无 ASR**（语音识别）。

---

## 二、已锁定的四项决策

| # | 决策项 | 结论 |
|---|---|---|
| 1 | **开发位置** | 在 `G:/ruoyi-fastapi-template`（template worktree）开新分支（如 `feat/module_calendar`）编码，完成后合并回 `template/main`。因为 `module_calendar` 是**共享积木**，本就该长在模板里。 |
| 2 | **首个落地目标** | `module_calendar` 日历提醒（既是积木又是律师 MVP 第一条需求）。 |
| 3 | **前端 uni-app 定位** | [ruoyi-fastapi-app/](ruoyi-fastapi-app/) 已是 uni-app+Vue3+tailwind+pinia 骨架，**直接作为律师 App 基底**开发，不先做前端模板化。 |
| 4 | **小助理 / OCR** | 第一期**不做**诉状 OCR 与流程标准化；聚焦日历提醒。 |

---

## 三、整体实现路径（Phase 0–6）

```
Phase 0  锁决策（本文档 §二，已完成）
   │
Phase 3  共享积木 ◄── 本文档重点
   ├─ module_calendar  日历 + 语音提醒（复用 APScheduler + module_ai）
   └─ module_push      移动端推送（uni-push / 极光，日历提醒依赖它）
   │
Phase 4  律师后端
   └─ module_lawyer_case  诉状 OCR + 要素提炼 + 流程标准化（复用 module_ai + MinioUtil）
                          + LawyerRoles（独立角色集，不污染 LearningRoles）
                          + module_lawyer/hooks.py（会员/token 登录准入）
   │
Phase 5  多端前端
   ├─ 手机/网页：ruoyi-fastapi-app (uni-app) → iOS / 安卓 / H5 / 小程序
   ├─ 桌面：同一份 H5 套 Tauri 壳 → Mac + Windows
   └─ 后台管理：ruoyi-fastapi-frontend (Vue3) 加日历/推送管理页
   │
Phase 6  反身性融合
   └─ 母仓 g:/zhangyichi 结构对齐 template（后端提仓根，框架/业务分目录）
      过渡期框架更新走 cherry-pick；对齐后可 git pull 干净合并
```

**横切｜框架更新流转**：`template/main` 改框架/积木 → 律师产品 `pull`/`merge`；反身性母仓 `cherry-pick <提交>`。框架文件与业务文件分目录，不冲突。

---

## 四、技术实现方案（选型）

### 4.1 端矩阵（统一代码、一次打包）

| 端 | 形态 | 技术方案 | 复用度 |
|---|---|---|---|
| 后台管理 | PC 网页控制台 | 现有 Vue3 + ElementPlus（[ruoyi-fastapi-frontend/](ruoyi-fastapi-frontend/)），加日历/推送管理页 | ★★★★★ |
| 终端 App（手机） | 消费级 App | **uni-app(Vue3)** → iOS + 安卓 + H5 + 小程序 | 全新写 |
| 网页端 | 浏览器访问 | = uni-app 编译的 **H5** | 与手机端同一套代码 |
| 电脑端 | 可下载桌面应用 | **Tauri** 打包同一份 H5 → Mac + Windows | 与网页端同一套代码 |

```
               ┌─ iOS App     ┐
uni-app(Vue3) ─┤─ 安卓 App     ├─  ← 一套 Vue3 代码
（业务+API层）  ├─ H5（网页端） │
               └─ 微信小程序   ┘
                       │  同一份 H5 / 共享业务组件
                       ▼
                 Tauri 壳层 ─┬─ Mac 应用
                            └─ Windows 应用
```

**数据多端一致天然成立**：手机/网页/电脑本质是同一套前端 + 同一账号 + 同一后端 API，数据在服务端。

### 4.2 选型理由

- **后端 FastAPI + RuoYi 模板**：模块化（加 `module_xxx` 即挂业务）、自带 RBAC/调度/对象存储/AI 多模型抽象，团队已有经验。
- **uni-app(Vue3)**：一套代码覆盖 iOS/安卓/H5/小程序，律师业务的"端全覆盖"一次解决；与现有 Vue3 后台同栈，学习成本最低。
- **Tauri（而非 Electron）**：体积小一个数量级（~10MB vs ~150MB），适合给律师装机；官方支持 Mac + Windows 双端构建。
- **APScheduler（模板自带）**：提醒触发复用框架调度器 + `sys_job` 持久化 + leader 锁，**多 worker 安全**，不重复触发。
- **litellm（模板自带）**：语音转文字后的"语义结构化"（明天 3 点 → `{start_at, repeat_rule}`）走多模型抽象，不绑死单一厂商。

### 4.3 语音"说任务"的边界（第一期关键取舍）

模板 `module_ai` 无 ASR。**第一期：语音转文字放前端，后端只做语义结构化。**

- 前端：`uni.getRecorderManager` 录音 → 平台 ASR（微信小程序自带语音识别；App 用插件）→ 文本。
- 后端：`event_parser` 把文本喂 `AiChatService`（litellm 结构化输出）→ `{title, start_at, end_at, repeat_rule}` → 落库 + 注册提醒。
- 后续可选：后端补 ASR（whisper / litellm audio 模型），第一期不做。

---

## 五、后端方案（module_calendar）

### 5.1 目录结构

```
module_calendar/
├── __init__.py
├── controller/
│   └── calendar_controller.py      # 必须：APIRouterPro(prefix='/calendar')
├── service/
│   ├── event_service.py            # 事件 CRUD
│   ├── event_parser.py             # 文本/语音→结构化（调 module_ai）
│   ├── reminder_scheduler.py       # 提醒注册/取消/改期（调 SchedulerUtil）
│   └── notification_service.py     # 通知下发（第一期写 sys_notice，预留 push）
├── dao/
│   ├── event_dao.py
│   └── reminder_dao.py
├── entity/
│   ├── do/calendar_do.py           # cal_* 三张表（自动建表）
│   └── vo/calendar_vo.py           # 请求/响应模型
└── hooks.py                        # 可选：仅当用内存 jobstore 才需要 rehydrate
```

> `auto_register_routers` 扫 `module_calendar/controller/*.py` 自动挂载；`find_models` 扫 `entity/do` 自动建表。

### 5.2 数据模型（`entity/do/calendar_do.py`）

业务表前缀 `cal_`（与框架 `sys_` 区分）。

#### 表 1：`cal_event`（日历事件/任务）

| 字段 | 类型 | 说明 |
|---|---|---|
| `event_id` | bigint PK | 主键 |
| `user_id` | bigint → sys_user.user_id | 归属用户（外键） |
| `title` | varchar(255) | 事件标题 |
| `description` | text | 备注 |
| `event_type` | varchar(20) | `reminder` / `task` |
| `start_at` | datetime | 开始时间 |
| `end_at` | datetime | 结束时间（可空） |
| `repeat_rule` | varchar(64) | cron 表达式 / `none` / `daily` / `weekly` |
| `remind_offset_min` | int | 提前提醒分钟数（默认 0） |
| `status` | varchar(20) | `active` / `done` / `cancelled` |
| `ai_parsed_raw` | text | 语音/文本原始输入（便于调优） |
| `created_at` / `updated_at` | datetime | 审计 |

#### 表 2：`cal_reminder`（提醒计划）

| 字段 | 类型 | 说明 |
|---|---|---|
| `reminder_id` | bigint PK | 主键 |
| `event_id` | bigint → cal_event | 关联事件 |
| `user_id` | bigint | 冗余便于查询 |
| `remind_at` | datetime | 下次触发时间 |
| `channel` | varchar(20) | `in_app` / `push` |
| `status` | varchar(20) | `pending` / `fired` / `cancelled` |
| `job_id` | varchar(64) | 对应 scheduler job id（便于取消） |
| `fired_at` | datetime | 实际触发时间 |

#### 表 3：`cal_ai_parse_log`（解析记录，可选，便于调优）

| 字段 | 类型 | 说明 |
|---|---|---|
| `log_id` | bigint PK | 主键 |
| `user_id` | bigint | |
| `raw_input` | text | 输入文本 |
| `parsed_json` | text | 结构化输出 |
| `model` | varchar(64) | 用的模型 |
| `created_at` | datetime | |

### 5.3 提醒触发层（核心：复用 SchedulerUtil，不造轮子）

**关键设计：提醒任务落 `sys_job` 持久化（推荐方案），不自己管定时器。**

- **一次性提醒**（`remind_at` 是具体时刻）→ `scheduler.add_job(trigger=DateTrigger(run_date=remind_at, timezone=APP_TZ), func=fire_reminder, args=[reminder_id], id=job_id)`
- **重复提醒**（`repeat_rule` = cron）→ `MyCronTrigger.from_crontab(expr, timezone=APP_TZ)` 或落 `sys_job` 走框架现有 job 同步机制（**多 worker 安全，推荐**）。

`service/reminder_scheduler.py` 封装：

```python
def schedule_reminder(reminder) -> str:      # 返回 job_id
    """注册提醒到 scheduler（持久化到 sys_job）"""
def cancel_reminder(job_id: str) -> None:     # 取消
def reschedule_on_event_change(event) -> None:  # 改时间→先 cancel 再 schedule
async def fire_reminder(reminder_id: int) -> None:  # 回调：查库→发通知→标记 fired
```

> **多 worker 安全靠框架**：`SchedulerUtil` 的 leader 锁 + SQLAlchemy jobstore 保证提醒集群内只触发一次。**不要**用内存 jobstore 多实例部署，否则重复触发。

### 5.4 语义结构化 `service/event_parser.py`

```python
async def parse_to_event(text: str, user_id: int) -> EventDraft:
    """文本 → 结构化事件草稿（调 module_ai litellm 结构化输出）
    '明天下午3点提醒我开庭' → EventDraft(title='开庭', start_at=..., repeat_rule='none')
    """
```

- 复用 `AiChatService`（litellm），prompt 约束输出 JSON schema（title / start_at / end_at / repeat_rule）。
- 失败兜底：解析失败则原样落 `title`、`start_at=now`，不阻断创建。

### 5.5 通知下发 `service/notification_service.py`

| 阶段 | 实现 |
|---|---|
| 第一期 | 写 `sys_notice`（复用框架通知表）+ 日志；前端进 App / 轮询拉取 |
| 预留 | `channel=in_app/push` 字段已留；`module_push`（极光/uni-push）做完后接上 |
| 后续可选 | 加 WebSocket（模板没有，需新建 `common/websocket.py`），第一期不做 |

### 5.6 接口列表（`controller/calendar_controller.py`）

```python
from common.router import APIRouterPro
from common.dependency import PreAuthDependency

calendar_controller = APIRouterPro(
    prefix='/calendar', order_num=20,
    tags=['日历提醒'], dependencies=[PreAuthDependency()])
```

| 方法 | 路径 | 说明 | 权限 |
|---|---|---|---|
| POST | `/calendar/event/parse` | 语音/文本 → 事件草稿 | `@CheckUserInterfaceAuth('calendar:event:parse')` |
| POST | `/calendar/event` | 创建事件 + 注册提醒 | `calendar:event:add` |
| GET | `/calendar/event/list` | 我的日历列表（支持日期范围） | `calendar:event:list` |
| PUT | `/calendar/event/{id}` | 改时间 → reschedule 提醒 | `calendar:event:edit` |
| DELETE | `/calendar/event/{id}` | 删除 → cancel 提醒 | `calendar:event:remove` |
| GET | `/calendar/reminder/today` | 今日待提醒 | `calendar:reminder:list` |
| PUT | `/calendar/reminder/{id}/done` | 标记完成 | `calendar:reminder:edit` |

> 权限点需在后台 `sys_menu` 配对应 perms 字符串（接口 URL 不变，菜单按需加）。

### 5.7 启动钩子（用 sys_job 持久化则**不需要**）

提醒任务若落 `sys_job`（推荐），重启后框架自动恢复 job，**无需钩子**。
仅当用内存 jobstore 时才需 `module_calendar/hooks.py` rehydrate pending 提醒：

```python
from common.lifecycle import LifecycleHooks

@LifecycleHooks.register_startup('calendar_rehydrate')
async def rehydrate(app) -> None:
    from module_calendar.service.reminder_scheduler import rehydrate_pending
    await rehydrate_pending()   # 把 status=pending 的 cal_reminder 重新注册到 scheduler
```

`server.py:175 discover_and_load()` 会自动发现它。

### 5.8 验证

1. `python app.py` 启动，Swagger 看 `/calendar/*` 是否上线；`cal_*` 表是否自动建出。
2. 用例：建一条"1 分钟后提醒" → 到点 `fire_reminder` 被调用 → `sys_notice` 落库 + `cal_reminder.status=fired`。
3. 回归：admin 登录等框架种子接口不破。
4. 通过后 `feat/module_calendar` 合回 `template/main` 并 push。

---

## 六、前端方案

### 6.1 手机端 / 网页端：uni-app（[ruoyi-fastapi-app/](ruoyi-fastapi-app/)）

**直接在此骨架上开发律师 App**。骨架现状：uni-app+Vue3+tailwind+pinia+vue-i18n，已有 `pages/{common,mine,work}`、`api/system`、`store`、`plugins`。

**第一期新增**：

```
src/
├── api/
│   └── calendar.js              # 封装 /calendar/* 接口
├── pages/
│   └── calendar/
│       ├── index.vue            # 日历月视图 + 当日事件列表
│       ├── new.vue              # 新建事件：录音/输入文本 → 调 parse → 确认
│       └── detail.vue           # 事件详情 / 改期 / 完成
└── utils/
    └── asr.js                   # 录音 → 平台 ASR → 文本（微信小程序自带；App 用插件）
```

**关键交互（语音说任务）**：
1. 长按录音按钮 → `uni.getRecorderManager` 录音。
2. ASR 转文字（平台能力 / 插件）。
3. `POST /calendar/event/parse` → 后端结构化返回草稿。
4. 用户确认时间 → `POST /calendar/event` → 提醒注册成功。

**多端打包**（package.json 已有脚本）：
- `pnpm dev:app` / `pnpm build:app` → Android / iOS
- `pnpm dev:h5` / `pnpm build:h5` → 网页端
- `pnpm dev:mp-weixin` / `pnpm build:mp-weixin` → 微信小程序

### 6.2 桌面端：Tauri（新建）

**同一份 H5 套 Tauri 壳**，复用 uni-app 的 `build:h5` 产物。

```
ruoyi-fastapi-app/desktop/        # 新建 Tauri 工程（或独立仓 lawyer-desktop）
├── src-tauri/
│   ├── tauri.conf.json           # 指向 ../dist/build/h5 为前端资源
│   ├── Cargo.toml
│   └── main.rs
└── README.md
```

- `tauri build` → 产出 Mac（`.dmg`）+ Windows（`.msi`/`.exe`）安装包。
- 体积 ~10MB 量级，适合给律师装机。
- 数据同步：桌面端同样调后端 `/calendar/*` API，与手机端同一账号同一数据源。

### 6.3 后台管理：Vue3（[ruoyi-fastapi-frontend/](ruoyi-fastapi-frontend/)）

骨架现状：`src/views/{system,ai,rag,monitor,tool,learning,edu,dashboard}` + 对应 `src/api`。日历管理页加到 `system` 或新建 `calendar`：

```
src/
├── api/calendar.js
└── views/calendar/
    ├── event/index.vue           # 全平台事件审计（管理员视角）
    └── reminder/index.vue        # 提醒执行记录 / 失败重试
```

> 后台是**管理员**视角（查所有人的事件、看提醒投递情况），终端 App 是**律师**视角（自己的日历）。两个产品定位不同，参见架构总纲。

### 6.4 数据同步机制

- **天然一致**：手机/网页/桌面本质同一前端 + 同一账号 + 同一后端 API，数据在服务端，无额外同步逻辑。
- **离线编辑**（后期）：可加本地缓存（uni-app 本地存储 / Tauri sqlite），上线后再做冲突合并。第一期不做。

---

## 七、具体模块分工

### 7.1 共享积木（长在模板，两产品共用）

| 模块 | 状态 | 职责 | 依赖 |
|---|---|---|---|
| `module_calendar` | 🟡 本文档 | 日历事件 + 语音/文本提醒，定时触发 | `SchedulerUtil`、`module_ai`（结构化）、`sys_notice` |
| `module_push` | ⬜ 待建 | 移动端推送（uni-push / 极光） | uni-app 端 + 后端下发；`module_calendar` 依赖它 |

### 7.2 产品业务模块

| 模块 | 归属 | 职责 | 备注 |
|---|---|---|---|
| `module_lawyer_case` | 律师产品 | 诉状 OCR + 要素提炼 + 流程标准化 | **第一期不做**；复用 `module_ai` + `MinioUtil` |
| `module_lawyer/hooks.py` | 律师产品 | 会员/token 登录准入 | 经 `LoginPolicyHooks` 自注册 |
| `LawyerRoles` | 律师产品 | 律师角色集（lawyer/client） | **不要**塞进反身性的 `LearningRoles` |
| `module_learning` | 反身性 | 四区学习/任务/批阅/反思 | 已在母仓，复用 calendar/push |
| `module_rag` | 反身性 | 专业库 RAG | 已在母仓 |

### 7.3 角色边界（务必分清）

- `admin` —— **框架系统角色**（role_id=1 超管，内置）。
- `teacher` / `student` —— **反身性业务角色**（`LearningRoles`）。
- `lawyer` / `client` —— **律师业务角色**（未来 `LawyerRoles`）。
- **三套角色互不污染**，各产品建自己的角色常量类。

### 7.4 前端分工

| 端 | 代码位置 | 服务对象 |
|---|---|---|
| 后台管理 | [ruoyi-fastapi-frontend/](ruoyi-fastapi-frontend/)（Vue3+ElementPlus） | 平台运营/管理员 |
| 终端 App（手机/网页） | [ruoyi-fastapi-app/](ruoyi-fastapi-app/)（uni-app+Vue3） | 律师/客户 |
| 桌面 | `ruoyi-fastapi-app/desktop/`（Tauri，新建） | 律师桌面 |

---

## 八、框架更新流转机制

| 场景 | 流转方式 |
|---|---|
| 模板 `template/main` 改框架/积木 | → 律师产品 `git pull`/`merge`（框架文件与业务文件分目录，不冲突） |
| 模板改框架/积木 | → 反身性母仓 `g:/zhangyichi`：`git cherry-pick <提交>`（母仓后端在 `ruoyi-fastapi-backend/` 子目录，结构不同） |
| Phase 6 母仓结构对齐后 | 母仓也可 `git pull` 干净合并，不再 cherry-pick |

---

## 九、风险与注意点

| 风险 | 应对 |
|---|---|
| ⚠️ 多 worker 重复触发提醒 | 用 `sys_job`（SQLAlchemy jobstore + 框架 leader 锁），**禁用内存 jobstore 多实例** |
| ⚠️ 时区错位 | `DateTrigger` / cron 统一用框架 `AppConfig` 时区，全链路不混用本地时区 |
| ⚠️ ASR 边界 | 第一期语音转文字放前端（微信小程序自带、App 插件），后端不引入音频依赖 |
| ⚠️ 通知能力缺口 | 第一期写 `sys_notice`（站内），`module_push` 做完后接入；实时推送（WebSocket）后置 |
| ⚠️ 角色污染 | 三套角色（admin / LearningRoles / LawyerRoles）严格分层，律师角色不进 LearningRoles |
| ⚠️ 解析失败 | `event_parser` 失败兜底为原样落库（`title` + `start_at=now`），不阻断创建 |

---

## 十、验收标准

**第一期 module_calendar 完成标准**：

- [ ] 后端：`module_calendar` 加目录即挂载，`/calendar/*` 上 Swagger，`cal_*` 三表自动建出。
- [ ] 提醒：建一条"1 分钟后提醒"，到点 `fire_reminder` 触发，`sys_notice` 落库，`cal_reminder.status` 变 `fired`。
- [ ] 重复提醒：建一条 cron 重复任务，重启后端后仍按计划触发（验证 `sys_job` 持久化）。
- [ ] 语义解析：前端录音/输入"明天下午 3 点提醒我开庭" → 后端解析出正确 `start_at`，落 `cal_event`。
- [ ] 回归：admin 登录等框架种子接口全绿。
- [ ] 多 worker：两实例同跑，提醒只触发一次。
- [ ] 合并：`feat/module_calendar` 合回 `template/main` 并 push；反身性母仓 cherry-pick 验证可同步。
- [ ] 前端：uni-app 日历页可建事件、查看今日提醒；后台管理页可审计事件/提醒记录。

---

*下一步：执行 §五的后端落地（第 0 步开分支 + 第 1 步建模型）。前端在接口联调阶段介入。*
