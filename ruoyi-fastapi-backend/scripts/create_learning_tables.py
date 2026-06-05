"""
创建反身性研究模块所需的全部数据库表
直接连接 PostgreSQL 执行 DDL
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from urllib.parse import quote_plus
import asyncpg


async def create_tables():
    # 从 .env.test 读取配置
    db_host = '115.220.6.150'
    db_port = 15432
    db_user = 'weifuqiang'
    db_password = 'weifuqiang'
    db_name = 'ruoyi-fastapi'

    conn = await asyncpg.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name,
    )

    try:
        # ===== 阶段1：教学任务管理 =====
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS edu_task (
                task_id          BIGSERIAL PRIMARY KEY,
                task_name        VARCHAR(200) NOT NULL,
                task_description TEXT,
                teacher_id       BIGINT NOT NULL REFERENCES sys_user(user_id),
                preset_scenario  TEXT,
                scenario_kb_ids  JSONB,
                decision_kb_ids  JSONB,
                reflection_kb_ids JSONB,
                research_kb_ids  JSONB,
                scenario_config  JSONB,
                reflection_config JSONB,
                deadline         TIMESTAMP,
                status           CHAR(1) DEFAULT '0',
                del_flag         CHAR(1) DEFAULT '0',
                create_by        VARCHAR(64) DEFAULT '',
                create_time      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                update_by        VARCHAR(64) DEFAULT '',
                update_time      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await conn.execute("COMMENT ON TABLE edu_task IS '教学任务表'")
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_edu_task_teacher ON edu_task(teacher_id, status)')

        await conn.execute('''
            CREATE TABLE IF NOT EXISTS edu_task_class (
                id          BIGSERIAL PRIMARY KEY,
                task_id     BIGINT NOT NULL REFERENCES edu_task(task_id),
                dept_id     BIGINT NOT NULL,
                create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await conn.execute("COMMENT ON TABLE edu_task_class IS '任务-班级分配表'")
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_edu_task_class_dept ON edu_task_class(dept_id, task_id)')

        # ===== 阶段2：学习记录主表 =====
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS edu_learning_record (
                record_id        BIGSERIAL PRIMARY KEY,
                task_id          BIGINT REFERENCES edu_task(task_id),
                student_id       BIGINT NOT NULL REFERENCES sys_user(user_id),
                current_stage    VARCHAR(20) DEFAULT 'scenario',
                scenario_status  CHAR(1) DEFAULT '0',
                decision_status  CHAR(1) DEFAULT '0',
                reflection_status CHAR(1) DEFAULT '0',
                research_status  CHAR(1) DEFAULT '0',
                scenario_id      BIGINT,
                decision_id      BIGINT,
                reflection_id    BIGINT,
                research_id      BIGINT,
                status           VARCHAR(20) DEFAULT 'ongoing',
                score            DECIMAL(5,2),
                teacher_feedback TEXT,
                start_time       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                submit_time      TIMESTAMP,
                complete_time    TIMESTAMP,
                del_flag         CHAR(1) DEFAULT '0',
                create_by        VARCHAR(64) DEFAULT '',
                create_time      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                update_by        VARCHAR(64) DEFAULT '',
                update_time      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(task_id, student_id)
            )
        ''')
        await conn.execute("COMMENT ON TABLE edu_learning_record IS '学习记录主表（四区联动主控）'")
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_record_student ON edu_learning_record(student_id)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_record_task ON edu_learning_record(task_id)')

        # ===== 阶段3：情境区 =====
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS edu_scenario_data (
                scenario_id      BIGSERIAL PRIMARY KEY,
                record_id        BIGINT NOT NULL REFERENCES edu_learning_record(record_id),
                student_id       BIGINT NOT NULL REFERENCES sys_user(user_id),
                description      TEXT,
                key_events       JSONB,
                identified_problems JSONB,
                category_tags    JSONB,
                status           CHAR(1) DEFAULT '0',
                del_flag         CHAR(1) DEFAULT '0',
                create_time      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                update_time      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await conn.execute("COMMENT ON TABLE edu_scenario_data IS '情境区主数据表'")
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_scenario_record ON edu_scenario_data(record_id)')

        await conn.execute('''
            CREATE TABLE IF NOT EXISTS edu_scenario_dialogue (
                dialogue_id   BIGSERIAL PRIMARY KEY,
                scenario_id   BIGINT NOT NULL REFERENCES edu_scenario_data(scenario_id),
                role          VARCHAR(20) NOT NULL,
                content       TEXT NOT NULL,
                dialogue_type VARCHAR(30),
                create_time   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await conn.execute("COMMENT ON TABLE edu_scenario_dialogue IS '情境区AI对话记录'")

        # ===== 阶段4：决策区 =====
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS edu_decision_data (
                decision_id       BIGSERIAL PRIMARY KEY,
                record_id         BIGINT NOT NULL REFERENCES edu_learning_record(record_id),
                scenario_id       BIGINT NOT NULL REFERENCES edu_scenario_data(scenario_id),
                student_id        BIGINT NOT NULL REFERENCES sys_user(user_id),
                key_event_index   INTEGER,
                key_event_desc    TEXT,
                is_intervened     BOOLEAN,
                action_taken      TEXT,
                reasoning         TEXT,
                psychological_state TEXT,
                alternatives      TEXT,
                expected_outcome  TEXT,
                actual_outcome    TEXT,
                ethics_analysis   JSONB,
                status            CHAR(1) DEFAULT '0',
                del_flag          CHAR(1) DEFAULT '0',
                create_time       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                update_time       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await conn.execute("COMMENT ON TABLE edu_decision_data IS '决策区数据表'")
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_decision_record ON edu_decision_data(record_id)')

        await conn.execute('''
            CREATE TABLE IF NOT EXISTS edu_decision_dialogue (
                dialogue_id    BIGSERIAL PRIMARY KEY,
                decision_id    BIGINT NOT NULL REFERENCES edu_decision_data(decision_id),
                role           VARCHAR(20) NOT NULL,
                content        TEXT NOT NULL,
                dialogue_type  VARCHAR(30),
                create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await conn.execute("COMMENT ON TABLE edu_decision_dialogue IS '决策区AI对话记录'")

        # ===== 阶段5：反思区 =====
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS edu_reflection_data (
                reflection_id   BIGSERIAL PRIMARY KEY,
                record_id       BIGINT NOT NULL REFERENCES edu_learning_record(record_id),
                scenario_id     BIGINT NOT NULL REFERENCES edu_scenario_data(scenario_id),
                student_id      BIGINT NOT NULL REFERENCES sys_user(user_id),
                content         TEXT,
                depth_level     VARCHAR(20) DEFAULT 'descriptive',
                depth_score     DECIMAL(3,2) DEFAULT 0.00,
                linked_theories JSONB,
                version         INTEGER DEFAULT 1,
                status          CHAR(1) DEFAULT '0',
                del_flag        CHAR(1) DEFAULT '0',
                create_time     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                update_time     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CHECK (depth_score >= 0 AND depth_score <= 1.00)
            )
        ''')
        await conn.execute("COMMENT ON TABLE edu_reflection_data IS '反思区主数据表'")
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_reflection_record ON edu_reflection_data(record_id)')

        await conn.execute('''
            CREATE TABLE IF NOT EXISTS edu_reflection_dialogue (
                dialogue_id        BIGSERIAL PRIMARY KEY,
                reflection_id      BIGINT NOT NULL REFERENCES edu_reflection_data(reflection_id),
                role               VARCHAR(20) NOT NULL,
                content            TEXT NOT NULL,
                question_level     VARCHAR(20),
                depth_score_before DECIMAL(3,2),
                depth_score_after  DECIMAL(3,2),
                linked_theories    JSONB,
                create_time        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await conn.execute("COMMENT ON TABLE edu_reflection_dialogue IS '反思区AI对话记录'")

        await conn.execute('''
            CREATE TABLE IF NOT EXISTS edu_reflection_depth_history (
                history_id    BIGSERIAL PRIMARY KEY,
                reflection_id BIGINT NOT NULL REFERENCES edu_reflection_data(reflection_id),
                depth_score   DECIMAL(3,2) NOT NULL,
                depth_level   VARCHAR(20) NOT NULL,
                trigger_type  VARCHAR(30),
                create_time   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await conn.execute("COMMENT ON TABLE edu_reflection_depth_history IS '反思深度演变历史'")
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_depth_reflection ON edu_reflection_depth_history(reflection_id)')

        # ===== 阶段6：研究生成区 =====
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS edu_research_data (
                research_id        BIGSERIAL PRIMARY KEY,
                record_id          BIGINT NOT NULL REFERENCES edu_learning_record(record_id),
                student_id         BIGINT NOT NULL REFERENCES sys_user(user_id),
                material_summary   TEXT,
                candidate_questions JSONB,
                selected_question  TEXT,
                framework          JSONB,
                ref_literature     JSONB,
                status             CHAR(1) DEFAULT '0',
                del_flag           CHAR(1) DEFAULT '0',
                create_time        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                update_time        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await conn.execute("COMMENT ON TABLE edu_research_data IS '研究生成区主数据表'")
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_research_record ON edu_research_data(record_id)')

        await conn.execute('''
            CREATE TABLE IF NOT EXISTS edu_research_chapter (
                chapter_id    BIGSERIAL PRIMARY KEY,
                research_id   BIGINT NOT NULL REFERENCES edu_research_data(research_id),
                chapter_index INTEGER NOT NULL,
                chapter_title VARCHAR(200),
                content       TEXT,
                ai_suggestion TEXT,
                status        CHAR(1) DEFAULT '0',
                create_time   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                update_time   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await conn.execute("COMMENT ON TABLE edu_research_chapter IS '研究区章节表'")
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_chapter_research ON edu_research_chapter(research_id)')

        # ===== 阶段7：教师监控+评价 =====
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS edu_evaluation (
                evaluation_id      BIGSERIAL PRIMARY KEY,
                record_id          BIGINT NOT NULL REFERENCES edu_learning_record(record_id),
                teacher_id         BIGINT NOT NULL REFERENCES sys_user(user_id),
                scenario_score     DECIMAL(5,2),
                decision_score     DECIMAL(5,2),
                reflection_score   DECIMAL(5,2),
                research_score     DECIMAL(5,2),
                total_score        DECIMAL(5,2),
                scenario_feedback  TEXT,
                decision_feedback  TEXT,
                reflection_feedback TEXT,
                research_feedback  TEXT,
                overall_feedback   TEXT,
                is_excellent       BOOLEAN DEFAULT FALSE,
                status             CHAR(1) DEFAULT '0',
                create_time        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                update_time        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(record_id)
            )
        ''')
        await conn.execute("COMMENT ON TABLE edu_evaluation IS '教师评价表'")

        await conn.execute('''
            CREATE TABLE IF NOT EXISTS edu_excellent_case (
                case_id           BIGSERIAL PRIMARY KEY,
                source_record_id  BIGINT,
                task_id           BIGINT NOT NULL,
                scenario_desc     TEXT,
                decision_data     JSONB,
                reflection_data   TEXT,
                research_data     TEXT,
                teacher_comment   TEXT,
                tags              JSONB,
                status            CHAR(1) DEFAULT '0',
                create_time       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                update_time       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await conn.execute("COMMENT ON TABLE edu_excellent_case IS '优秀案例库（匿名化）'")

        print("All 14 tables created successfully!")

        # 验证
        tables = await conn.fetch('''
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public' AND tablename LIKE 'edu_%'
            ORDER BY tablename
        ''')
        print(f"\nedu_ tables ({len(tables)} total):")
        for t in tables:
            print(f"  - {t['tablename']}")

    finally:
        await conn.close()


if __name__ == '__main__':
    asyncio.run(create_tables())
