-- =============================================================================
-- 知识库权限控制 - 数据库迁移（PostgreSQL，对应实际部署）
-- 对应「知识库权限控制设计方案.md」§2.1 / §4.7
-- 执行前请备份 rag_knowledge_base 表。幂等：可重复执行（列存在则跳过）。
-- =============================================================================

-- 1. 新增三列（若不存在）
ALTER TABLE rag_knowledge_base
  ADD COLUMN IF NOT EXISTS kb_scope       VARCHAR(20) NOT NULL DEFAULT 'personal'
    COMMENT '可见范围：public/school/class/personal';
ALTER TABLE rag_knowledge_base
  ADD COLUMN IF NOT EXISTS scope_dept_id  BIGINT NULL
    COMMENT '作用域部门ID：school=学校dept_id；class=班级dept_id；其余为NULL';
ALTER TABLE rag_knowledge_base
  ADD COLUMN IF NOT EXISTS owner_user_id  BIGINT NULL
    COMMENT '所有者用户ID（personal=学生本人；其余=创建者）';

-- 2. 存量数据回填：旧 KB 默认归为创建者个人级
UPDATE rag_knowledge_base
   SET kb_scope = 'personal',
       owner_user_id = COALESCE(owner_user_id, user_id)
 WHERE kb_scope IS NULL OR kb_scope = '';

-- 3. 索引（scope_dept_id + kb_scope 联合索引收益最大；owner_user_id 用于个人库查询）
CREATE INDEX IF NOT EXISTS idx_rag_kb_scope_dept   ON rag_knowledge_base (kb_scope, scope_dept_id);
CREATE INDEX IF NOT EXISTS idx_rag_kb_owner        ON rag_knowledge_base (owner_user_id);

-- =============================================================================
-- 备注：
-- - COMMENT 语法需 PostgreSQL 9.1+（本部署满足）。MySQL 用 ALTER ... COMMENT '...' 形式。
-- - 「同校」判定在代码层用 CONCAT(',', ancestors, ',') LIKE '%,school,%'（见 kb_scope_policy.dept_ids_under_school），
--   故 sys_dept 无需新增 dept_category 字段，框架表保持纯净。
-- =============================================================================
