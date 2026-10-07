-- ============================================================
-- 知识对话 + 文档书目元数据 增量迁移（PostgreSQL）
-- 日期：2026-10-07
--
-- 说明：
--   1. 三张新表 kb_chat_session / kb_chat_message / kb_chat_citation
--      由应用启动时的 Base.metadata.create_all 自动创建（见 module_ai/entity/do/knowledge_chat_do.py）。
--   2. 本文件补齐已有表需要的新增列：
--      - rag_document 的书目元数据列（create_all 不会修改已存在表）
--      - kb_chat_message.retrieval_status（V1.1 新增，对已存在的 kb_chat_message 表生效）
--   3. 菜单“知识对话”见 ruoyi-fastapi-pg.sql 中的 sys_menu id 4204。
-- ============================================================

ALTER TABLE kb_chat_message ADD COLUMN IF NOT EXISTS retrieval_status VARCHAR(20);
COMMENT ON COLUMN kb_chat_message.retrieval_status IS '检索状态（matched 有命中 no_match 零命中 failed 检索失败 not_attempted 未检索）';

ALTER TABLE rag_document ADD COLUMN IF NOT EXISTS source_type VARCHAR(20);
COMMENT ON COLUMN rag_document.source_type IS '文献类型（textbook 教材 article 文章 other 其他）';

ALTER TABLE rag_document ADD COLUMN IF NOT EXISTS title VARCHAR(255);
COMMENT ON COLUMN rag_document.title IS '正式文献标题，区别于上传文件名 doc_name';

ALTER TABLE rag_document ADD COLUMN IF NOT EXISTS authors JSONB;
COMMENT ON COLUMN rag_document.authors IS '作者列表，JSON数组如["张三"]';

ALTER TABLE rag_document ADD COLUMN IF NOT EXISTS publication_year INTEGER;
COMMENT ON COLUMN rag_document.publication_year IS '出版/发表年份';

ALTER TABLE rag_document ADD COLUMN IF NOT EXISTS edition VARCHAR(50);
COMMENT ON COLUMN rag_document.edition IS '版次';

ALTER TABLE rag_document ADD COLUMN IF NOT EXISTS publisher_or_journal VARCHAR(255);
COMMENT ON COLUMN rag_document.publisher_or_journal IS '出版社/期刊名';

ALTER TABLE rag_document ADD COLUMN IF NOT EXISTS doi_or_url VARCHAR(500);
COMMENT ON COLUMN rag_document.doi_or_url IS 'DOI或URL';
