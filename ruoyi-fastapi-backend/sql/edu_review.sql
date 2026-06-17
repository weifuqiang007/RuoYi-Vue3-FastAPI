-- ============================================================
-- 教师批阅反思研究模块 - 数据库变更脚本（PostgreSQL）
-- 版本: v1.0  日期: 2026-06-17
-- 内容:
--   1) 新建 edu_review          反思批阅主表（AI评论+老师点评）
--   2) 新建 edu_review_dialogue AI评论历史版本表
--   3) edu_task 新增 review_model_id 字段（批阅裁判模型）
--   4) sys_config 预置批阅默认模型参数 edu.review.default_model_id
-- 说明: 反思区/决策区等学生侧四区固定使用 model_id=1；批阅(裁判)模型必须 ≠1，
--       由任务 review_model_id 指定，缺省回落 sys_config 的 edu.review.default_model_id。
-- ============================================================

-- 1. 反思批阅主表 ------------------------------------------------
CREATE TABLE IF NOT EXISTS edu_review (
    review_id           bigserial    PRIMARY KEY,
    record_id           bigint       NOT NULL,
    task_id             bigint,
    student_id          bigint       NOT NULL,
    ai_comment          jsonb,
    ai_comment_text     text,
    ai_comment_version  integer      DEFAULT 0,
    ai_comment_time     timestamp,
    ai_comment_scope    varchar(20)  DEFAULT 'reflection',
    review_model_id     bigint,
    teacher_id          bigint,
    reflection_score    numeric(5,2),
    teacher_comment     text,
    overall_comment     text,
    ai_comment_feedback text,
    review_status       char(1)      DEFAULT '0',
    review_time         timestamp,
    del_flag            char(1)      DEFAULT '0',
    create_by           varchar(64)  DEFAULT '',
    create_time         timestamp    DEFAULT CURRENT_TIMESTAMP,
    update_by           varchar(64)  DEFAULT '',
    update_time         timestamp    DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_edu_review_record UNIQUE (record_id)
);
COMMENT ON TABLE edu_review IS '反思批阅主表（AI评论+老师点评，过程性，与终结性评价edu_evaluation解耦）';
COMMENT ON COLUMN edu_review.review_id IS '批阅记录主键ID';
COMMENT ON COLUMN edu_review.record_id IS '关联的学习记录ID，关联edu_learning_record.record_id，唯一';
COMMENT ON COLUMN edu_review.task_id IS '冗余字段，关联的教学任务ID，关联edu_task.task_id，方便按任务筛选';
COMMENT ON COLUMN edu_review.student_id IS '冗余字段，学生用户ID（=edu_learning_record.user_id），方便按学生筛选';
COMMENT ON COLUMN edu_review.ai_comment IS 'AI评论结构化结果，JSON对象，含summary/depth_assessment/strengths/weaknesses/suggestions/theory_reference/conclusion';
COMMENT ON COLUMN edu_review.ai_comment_text IS 'AI评论纯文本摘要（summary+conclusion），列表展示用';
COMMENT ON COLUMN edu_review.ai_comment_version IS 'AI评论版本号，每重新生成一次+1';
COMMENT ON COLUMN edu_review.ai_comment_time IS '最近一次AI评论生成时间';
COMMENT ON COLUMN edu_review.ai_comment_scope IS '最近生成范围（reflection仅反思 / full含四区）';
COMMENT ON COLUMN edu_review.review_model_id IS '本次AI评论所用的裁判模型ID，关联ai_model.model_id，应与学生侧(model_id=1)不同，避免同模型自评';
COMMENT ON COLUMN edu_review.teacher_id IS '批阅教师用户ID，关联sys_user.user_id';
COMMENT ON COLUMN edu_review.reflection_score IS '老师对反思维度的评分（0-100）';
COMMENT ON COLUMN edu_review.teacher_comment IS '老师针对学生反思结论的点评文字';
COMMENT ON COLUMN edu_review.overall_comment IS '老师总评';
COMMENT ON COLUMN edu_review.ai_comment_feedback IS '老师对AI评论的看法（认同/补充/纠正）';
COMMENT ON COLUMN edu_review.review_status IS '批阅状态（0草稿 1已提交）';
COMMENT ON COLUMN edu_review.review_time IS '老师点评提交时间';
COMMENT ON COLUMN edu_review.del_flag IS '删除标志（0存在 2删除）';
COMMENT ON COLUMN edu_review.create_by IS '创建者用户名';
COMMENT ON COLUMN edu_review.create_time IS '创建时间';
COMMENT ON COLUMN edu_review.update_by IS '最后更新者用户名';
COMMENT ON COLUMN edu_review.update_time IS '最后更新时间';
CREATE INDEX IF NOT EXISTS idx_edu_review_student ON edu_review(student_id);
CREATE INDEX IF NOT EXISTS idx_edu_review_task ON edu_review(task_id);

-- 2. AI评论历史版本表 --------------------------------------------
CREATE TABLE IF NOT EXISTS edu_review_dialogue (
    dialogue_id     bigserial    PRIMARY KEY,
    review_id       bigint       NOT NULL,
    record_id       bigint       NOT NULL,
    ai_comment      jsonb        NOT NULL,
    ai_comment_text text,
    version         integer      NOT NULL,
    scope           varchar(20)  DEFAULT 'reflection',
    model_id        bigint,
    create_time     timestamp    DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE edu_review_dialogue IS '反思批阅-AI评论历史版本';
COMMENT ON COLUMN edu_review_dialogue.dialogue_id IS '历史记录主键ID';
COMMENT ON COLUMN edu_review_dialogue.review_id IS '关联的批阅记录ID，关联edu_review.review_id';
COMMENT ON COLUMN edu_review_dialogue.record_id IS '冗余字段，关联的学习记录ID，方便按record查历史';
COMMENT ON COLUMN edu_review_dialogue.ai_comment IS '该版本的AI评论结构化结果';
COMMENT ON COLUMN edu_review_dialogue.ai_comment_text IS '该版本AI评论纯文本摘要';
COMMENT ON COLUMN edu_review_dialogue.version IS '版本号';
COMMENT ON COLUMN edu_review_dialogue.scope IS '生成范围（reflection仅反思 / full含四区）';
COMMENT ON COLUMN edu_review_dialogue.model_id IS '生成该版本所用模型ID，关联ai_model.model_id';
COMMENT ON COLUMN edu_review_dialogue.create_time IS '生成时间';
CREATE INDEX IF NOT EXISTS idx_edu_review_dialogue_record ON edu_review_dialogue(record_id, version);

-- 3. edu_task 新增批阅模型字段 -----------------------------------
ALTER TABLE edu_task ADD COLUMN IF NOT EXISTS review_model_id bigint;
COMMENT ON COLUMN edu_task.review_model_id IS '批阅(裁判)AI模型ID，关联ai_model.model_id；为NULL时回落系统默认批阅模型(sys_config: edu.review.default_model_id)；必须与学生侧(model_id=1)不同，避免同模型自评';

-- 4. sys_config 预置批阅默认模型参数 -----------------------------
--    ⚠️ config_value 当前占位为 2，上线前必须改成数据库中实际存在且 ≠1（学生侧）的 ai_model.model_id
INSERT INTO sys_config (config_name, config_key, config_value, config_type, create_by, create_time, remark)
SELECT '批阅默认模型ID', 'edu.review.default_model_id', '2', 'Y', 'admin', CURRENT_TIMESTAMP,
       '反思批阅裁判模型默认ID。任务未单独配置review_model_id时回落此项。必须配置成一个可用且≠1（学生侧四区模型）的ai_model.model_id'
WHERE NOT EXISTS (SELECT 1 FROM sys_config WHERE config_key = 'edu.review.default_model_id');

-- 5. 菜单注册 ---------------------------------------------------
--    教师批阅工作台，component 指向前端 src/views/learning/review/index.vue（RuoYi 动态路由按此加载）。
--    ⚠️ parent_id 请改成你库中「学习/反身性研究」父目录的实际 menu_id；
--       执行后还需在「角色-菜单」(sys_role_menu) 中把 menu_id=4170 分配给 teacher / admin 角色。
INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, remark)
SELECT 4170, '教师批阅', 0, 5, 'review', 'learning/review/index', NULL, 1, 0, 'C', '0', '0', 'learning:review:list', 'edit', 'admin', CURRENT_TIMESTAMP, '教师批阅反思研究工作台'
WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE menu_id = 4170);
