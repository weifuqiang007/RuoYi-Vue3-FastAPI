-- ============================================================
-- 知识对话双模式改造（V1.2）增量迁移（PostgreSQL）
-- 日期：2026-10-08
--
-- 新增：
--   kb_chat_message.answer_mode / request_kb_ids
--   kb_chat_citation.evidence_type / supports / application_note
--   kb_chat_session.last_answer_mode
-- 说明：新表仍由 Base.metadata.create_all 创建，本文件仅补齐已有表的新列。
-- ============================================================

ALTER TABLE kb_chat_message ADD COLUMN IF NOT EXISTS answer_mode VARCHAR(20) DEFAULT 'professional';
COMMENT ON COLUMN kb_chat_message.answer_mode IS '回答模式（professional 专业研讨 public 日常求助）';

ALTER TABLE kb_chat_message ADD COLUMN IF NOT EXISTS request_kb_ids JSONB;
COMMENT ON COLUMN kb_chat_message.request_kb_ids IS '本轮请求的知识库ID列表，JSON数组如[1,2]，用于幂等冲突检测';

ALTER TABLE kb_chat_citation ADD COLUMN IF NOT EXISTS evidence_type VARCHAR(20);
COMMENT ON COLUMN kb_chat_citation.evidence_type IS '依据类别（direct 直接依据 background 背景参考）';

ALTER TABLE kb_chat_citation ADD COLUMN IF NOT EXISTS supports JSONB;
COMMENT ON COLUMN kb_chat_citation.supports IS '正文支持关系，JSON数组如[{"statement":"...","relation":"background"}]';

ALTER TABLE kb_chat_citation ADD COLUMN IF NOT EXISTS application_note TEXT;
COMMENT ON COLUMN kb_chat_citation.application_note IS '适用限制说明';

ALTER TABLE kb_chat_session ADD COLUMN IF NOT EXISTS last_answer_mode VARCHAR(20);
COMMENT ON COLUMN kb_chat_session.last_answer_mode IS '最近一次已接受请求的回答模式（professional/public），旧会话为NULL按professional';
