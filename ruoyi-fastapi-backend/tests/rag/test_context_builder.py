from module_rag.service.context_builder import RagContextBuilder


def test_context_builder_emits_traceable_citations():
    context = RagContextBuilder.from_results([
        {
            'chunk_id': 10,
            'doc_id': 20,
            'kb_id': 30,
            'content': '研究者需要审视自身立场。',
            'score': 0.88,
            'metadata': {
                'doc_name': '行动研究.md',
                'page': 3,
                'heading_path': ['第三章', '反身性'],
            },
        }
    ])

    assert '[1] 来源：行动研究.md · 第3页 · 第三章 > 反身性' in context.text
    assert context.citations[0]['chunk_id'] == 10
    assert context.citations[0]['heading_path'] == ['第三章', '反身性']
