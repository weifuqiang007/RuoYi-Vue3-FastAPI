"""知识对话服务纯逻辑单元测试（不依赖数据库）。"""

from types import SimpleNamespace

from module_ai.entity.do.knowledge_chat_do import KbChatSession
from module_ai.service.knowledge_chat_service import KnowledgeChatService


def test_parse_kb_ids_filters_invalid_and_dedups() -> None:
    """前端字符串ID应被解析为去重的整数列表，非法项被忽略。"""
    result = KnowledgeChatService.parse_kb_ids(['12', '18', '12', 'abc', None, '', '7'])
    assert result == [12, 18, 7]


def test_page_label_only_for_pdf_positive_page() -> None:
    """页码标签仅对 PDF 正页码生成。"""
    assert KnowledgeChatService._page_label(3) == 'PDF 第 3 页'
    assert KnowledgeChatService._page_label(0) is None
    assert KnowledgeChatService._page_label(None) is None


def test_locator_type_prefers_page_then_section() -> None:
    """定位类型：有页码→page，有章节→section，否则 none。"""
    assert KnowledgeChatService._locator_type({'page': 2, 'heading_path': ['第三章']}) == 'page'
    assert KnowledgeChatService._locator_type({'page': 0, 'heading_path': ['第三章']}) == 'section'
    assert KnowledgeChatService._locator_type({'page': 0, 'heading_path': []}) == 'none'


def test_session_dict_maps_orm_to_frontend_contract() -> None:
    """会话 ORM 字段应映射为前端驼峰契约。"""
    session = SimpleNamespace(
        session_id='abc123',
        title='',
        kb_ids=[12, 18],
        create_time='2026-10-07 12:00:00',
        update_time='2026-10-07 13:00:00',
    )
    result = KnowledgeChatService.session_dict(session)
    assert result['sessionId'] == 'abc123'
    assert result['title'] == '新会话'
    assert result['kbIds'] == [12, 18]
    assert result['createdAt'] == '2026-10-07 12:00:00'
    assert result['updatedAt'] == '2026-10-07 13:00:00'


def test_session_do_has_expected_table_name() -> None:
    """会话表名与约束一致，供建表 SQL 校验。"""
    assert KbChatSession.__tablename__ == 'kb_chat_session'
