import json
import re
from collections.abc import AsyncGenerator
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from module_learning.dao.research_dao import ResearchDao
from module_learning.dao.record_dao import RecordDao
from module_learning.dao.scenario_dao import ScenarioDao
from module_learning.dao.decision_dao import DecisionDao
from module_learning.dao.reflection_dao import ReflectionDao
from module_learning.entity.do.research_do import EduResearchData, EduResearchChapter
from module_learning.entity.vo.research_vo import ResearchChapterSaveModel, ResearchSaveModel
from utils.llm_json_parser import parse_llm_json


RESEARCH_QUESTION_PROMPT = """你是一位行动研究方法专家，正在帮助一位社会工作专业的学生，从其实习经历中凝练研究问题。

学生的实习材料汇总：
情境描述：{scenario_summary}
决策分析：{decision_summary}
反思记录（精华摘录）：{reflection_summary}

任务：基于以上材料，生成 3-5 个适合本科生行动研究的候选研究问题。
输出 JSON：
{{
  "questions": [
    {{"question": "研究问题表述", "rationale": "选择理由", "approach": "研究路径"}}
  ]
}}"""

RESEARCH_QUESTION_STREAM_PROMPT = """你是一位行动研究方法专家，正在帮助一位社会工作专业的学生，从其实习经历中凝练研究问题。
学生的实习材料汇总：
情境描述：{scenario_summary}
决策分析：{decision_summary}
反思记录（精华摘录）：{reflection_summary}

任务：基于以上材料，生成 3-5 个适合本科生行动研究的候选研究问题。

请直接输出给学生看的内容，不要输出 JSON、代码块或额外解释。严格使用下面格式：
1. 研究问题：……
   选择理由：……
   研究路径：……

2. 研究问题：……
   选择理由：……
   研究路径：……
"""

RESEARCH_FRAMEWORK_PROMPT = """你是一位学术论文指导专家，请基于以下研究问题生成论文框架。

研究问题：{selected_question}

学生的实践材料摘要：
{material_summary}

输出 JSON 论文大纲：
{{
  "framework": [
    {{"index": 1, "title": "绪论", "description": "章节说明"}},
    {{"index": 2, "title": "文献综述", "description": "章节说明"}},
    ...
  ]
}}"""

CHAPTER_DRAFT_PROMPT = """你是一位学术论文写作指导专家，请为以下章节提供写作建议和段落草稿。

论文主题：{selected_question}
当前章节：{chapter_title}
已有的其他章节框架：
{framework_summary}

学生的实践材料：
{material_summary}

请输出写作建议和段落草稿（约500字）。"""

RESEARCH_FRAMEWORK_STREAM_PROMPT = """你是一位学术论文指导专家，请基于以下研究问题生成论文框架。

研究问题：{selected_question}

学生的实践材料摘要：
{material_summary}

请直接输出给学生看的论文大纲，不要输出 JSON 或代码块。严格使用以下格式：

1. 绪论
   章节说明：介绍研究背景、问题的提出及研究意义

2. 文献综述
   章节说明：梳理国内外相关理论和研究

3. 研究方法
   章节说明：说明研究设计、数据收集与分析方法

请根据研究问题生成完整的论文框架（通常5-7章）。"""

REFERENCES_PROMPT = """你是一位学术文献检索专家，请基于以下研究问题和材料推荐相关参考文献。

研究问题：{selected_question}

学生的实践材料摘要：
{material_summary}

请推荐 5-8 篇高度相关的学术文献，优先推荐经典文献和近五年内的重要研究。
输出 JSON：
{{
  "references": [
    {{"citation": "作者. 标题. 期刊/出版社, 年份.", "relevance": "与研究的关联说明"}}
  ]
}}"""

REFERENCES_STREAM_PROMPT = """你是一位学术文献检索专家，请基于以下研究问题和材料推荐相关参考文献。

研究问题：{selected_question}

学生的实践材料摘要：
{material_summary}

请推荐 5-8 篇高度相关的学术文献，优先推荐经典文献和近五年内的重要研究。

请直接输出给学生看的内容，不要输出 JSON 或代码块。严格使用以下格式：

1. 作者. 标题. 期刊/出版社, 年份.
   关联说明：这篇文献与你研究中...直接相关

2. 作者. 标题. 期刊/出版社, 年份.
   关联说明：...
"""


class ResearchService:

    @classmethod
    async def init_research(cls, db: AsyncSession, record_id: int, student_id: int, model_id: int = 1, force: bool = False) -> dict:
        """初始化研究区。
        - force=False（页面加载）：已存在则直接返回完整数据用于回显，不覆盖；
        - force=True（点击"重新汇总"）：强制重新聚合前三区材料并更新 DB。
        """
        record = await RecordDao.get_by_id(db, record_id)
        if not record:
            raise ValueError('学习记录不存在')

        research = await ResearchDao.get_by_record_id(db, record_id)

        # 页面加载且已存在：直接返回完整数据，不覆盖用户保存的内容
        if research and not force:
            return await cls.get_detail(db, record_id) or {
                'research_id': research.research_id,
            }

        # 重新聚合前三区材料
        material_summary = await cls._aggregate_material(db, record_id)

        if research:
            # 已存在（force=True）：只更新 material_summary，保留其余字段
            research.material_summary = material_summary
            research.update_time = datetime.now()
            await ResearchDao.update(db, research)
        else:
            # 首次创建
            research = EduResearchData(
                record_id=record_id,
                student_id=student_id,
                material_summary=material_summary,
            )
            research = await ResearchDao.create(db, research)
            # 回填 record
            record.research_id = research.research_id
            record.research_status = '1'
            record.update_time = datetime.now()
            await RecordDao.update(db, record)

        return await cls.get_detail(db, record_id) or {
            'research_id': research.research_id,
            'material_summary': material_summary,
        }

    @classmethod
    async def _aggregate_material(cls, db: AsyncSession, record_id: int) -> str:
        """聚合前三区（情境/决策/反思）完整材料，不做截断"""
        scenario = await ScenarioDao.get_by_record_id(db, record_id)
        decisions = await DecisionDao.get_by_record_id(db, record_id)
        reflections = await ReflectionDao.get_list_by_record_id(db, record_id)

        sections = []

        # 情境：完整描述
        scenario_text = (scenario.description or '').strip() if scenario else ''
        sections.append('【情境】\n' + (scenario_text or '（无情境数据）'))

        # 决策：每条列出关键事件、采取行动、理由、实际结果
        if decisions:
            decision_lines = [f'共 {len(decisions)} 条决策记录：']
            for i, d in enumerate(decisions, 1):
                parts = [f'\n【决策{i}】']
                event = cls._clean_text(d.key_event_desc)
                if event:
                    parts.append(f'关键事件：{event}')
                action = cls._clean_text(d.action_taken)
                if action:
                    parts.append(f'采取行动：{action}')
                reasoning = cls._clean_text(d.reasoning)
                if reasoning:
                    parts.append(f'行动理由：{reasoning}')
                outcome = cls._clean_text(d.actual_outcome)
                if outcome:
                    parts.append(f'实际结果：{outcome}')
                decision_lines.append('\n'.join(parts))
            sections.append('【决策】' + '\n'.join(decision_lines))
        else:
            sections.append('【决策】\n（无决策记录）')

        # 反思：取最新一条完整内容
        if reflections:
            latest = reflections[0]
            reflection_text = (latest.content or '').strip()
            sections.append('【反思】\n' + (reflection_text or '（反思内容为空）'))
        else:
            sections.append('【反思】\n（无反思记录）')

        return '\n\n'.join(sections)

    @staticmethod
    def _clean_text(raw) -> str:
        """清洗字段文本：解析JSON残留、去除断裂的JSON片段，返回纯文本"""
        if not raw:
            return ''
        text = str(raw).strip()
        if not text:
            return ''
        # 尝试解析为完整 JSON（key_event_desc 可能存了 {"event":"..."} ）
        try:
            obj = json.loads(text)
            if isinstance(obj, dict):
                for key in ('event', 'description', 'title', 'content'):
                    if obj.get(key):
                        return str(obj[key]).strip()
                return str(obj).strip()
        except (json.JSONDecodeError, TypeError):
            pass
        # 处理断裂的 JSON 残留（如 {"event":"xxx 被截断）
        json_prefix = re.search(r'^\s*\{\s*"?[一-龥\w]+"?\s*:\s*"?(.*)$', text, re.S)
        if json_prefix:
            cleaned = json_prefix.group(2).strip().rstrip('"}').strip()
            if cleaned:
                return cleaned
        return text

    @classmethod
    async def save(cls, db: AsyncSession, data: ResearchSaveModel) -> dict:
        """保存研究区整体数据（选定研究问题、材料汇总、所有章节内容）"""
        research = await ResearchDao.get_by_id(db, data.research_id)
        if not research:
            raise ValueError('研究数据不存在')

        if data.selected_question is not None:
            research.selected_question = data.selected_question
        if data.material_summary is not None:
            research.material_summary = data.material_summary
        research.update_time = datetime.now()
        await ResearchDao.update(db, research)

        # 保存所有章节内容
        saved_chapters = []
        if data.chapters:
            for ch_data in data.chapters:
                chapter_index = ch_data.get('chapter_index')
                content = ch_data.get('content')
                if chapter_index is None:
                    continue
                chapter = await ResearchDao.get_chapter_by_index(db, data.research_id, chapter_index)
                if chapter:
                    if content is not None:
                        chapter.content = content
                    chapter.update_time = datetime.now()
                    await ResearchDao.update_chapter(db, chapter)
                    saved_chapters.append(chapter_index)

        return {'research_id': research.research_id, 'saved': True, 'saved_chapters': saved_chapters}

    @classmethod
    async def generate_questions(cls, db: AsyncSession, research_id: int, model_id: int = 1) -> dict:
        """AI生成候选研究问题"""
        research = await ResearchDao.get_by_id(db, research_id)
        if not research:
            raise ValueError('研究数据不存在')

        prompt = RESEARCH_QUESTION_PROMPT.format(
            scenario_summary=research.material_summary or '',
            decision_summary='',
            reflection_summary='',
        )

        from module_learning.service.llm_call import AiCall
        result = await AiCall.call_llm_json(db, model_id, prompt)

        research.candidate_questions = result.get('questions', [])
        research.update_time = datetime.now()
        await ResearchDao.update(db, research)

        return result

    @classmethod
    async def generate_questions_stream(cls, db: AsyncSession, research_id: int, model_id: int = 1) -> AsyncGenerator[str, None]:
        """AI流式生成候选研究问题，并在完成后保存结构化结果。"""
        research = await ResearchDao.get_by_id(db, research_id)
        if not research:
            yield json.dumps({'type': 'error', 'message': '研究数据不存在'}, ensure_ascii=False) + '\n'
            return

        prompt = RESEARCH_QUESTION_STREAM_PROMPT.format(
            scenario_summary=research.material_summary or '',
            decision_summary='',
            reflection_summary='',
        )

        from module_learning.service.llm_call import AiCall

        full_text = ''
        yield json.dumps({'type': 'status', 'message': 'AI 正在生成候选研究问题...'}, ensure_ascii=False) + '\n'
        async for chunk in AiCall.call_llm_stream(db, model_id, prompt):
            try:
                parsed = json.loads(chunk.strip())
                if parsed.get('type') == 'content' and parsed.get('content'):
                    content = parsed['content']
                    full_text += content
                    for char in content:
                        yield json.dumps({'type': 'content', 'content': char}, ensure_ascii=False) + '\n'
                else:
                    yield chunk
            except (json.JSONDecodeError, AttributeError):
                yield chunk

        try:
            questions = cls._parse_streamed_questions(full_text)
            research.candidate_questions = questions
            research.update_time = datetime.now()
            await ResearchDao.update(db, research)
            yield json.dumps({
                'type': 'result',
                'data': {
                    'questions': questions,
                    'candidate_questions': questions,
                    'raw_text': full_text,
                },
            }, ensure_ascii=False) + '\n'
        except Exception as e:
            yield json.dumps({'type': 'error', 'message': f'候选问题解析失败：{str(e)}'}, ensure_ascii=False) + '\n'

    @staticmethod
    def _parse_streamed_questions(text: str) -> list[dict]:
        """Parse the readable streamed format into the persisted question schema."""
        try:
            parsed = parse_llm_json(text)
            if isinstance(parsed, dict) and isinstance(parsed.get('questions'), list):
                return parsed['questions']
        except Exception:
            pass

        blocks = re.split(r'(?:^|\n)\s*(?=\d+[\.、]\s*)', text.strip())
        questions = []
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            question_match = re.search(r'研究问题[:：]\s*(.+?)(?=\n\s*(?:选择理由|研究路径)[:：]|\Z)', block, re.S)
            rationale_match = re.search(r'选择理由[:：]\s*(.+?)(?=\n\s*研究路径[:：]|\Z)', block, re.S)
            approach_match = re.search(r'研究路径[:：]\s*(.+)', block, re.S)

            if question_match:
                questions.append({
                    'question': question_match.group(1).strip(),
                    'rationale': rationale_match.group(1).strip() if rationale_match else '',
                    'approach': approach_match.group(1).strip() if approach_match else '',
                })

        if questions:
            return questions

        cleaned = text.strip()
        return [{'question': cleaned, 'rationale': '', 'approach': ''}] if cleaned else []

    @classmethod
    async def generate_framework(cls, db: AsyncSession, research_id: int, selected_question: str, model_id: int = 1) -> dict:
        """AI生成论文框架"""
        research = await ResearchDao.get_by_id(db, research_id)
        if not research:
            raise ValueError('研究数据不存在')

        research.selected_question = selected_question
        research.update_time = datetime.now()

        prompt = RESEARCH_FRAMEWORK_PROMPT.format(
            selected_question=selected_question,
            material_summary=research.material_summary or '',
        )

        from module_learning.service.llm_call import AiCall
        result = await AiCall.call_llm_json(db, model_id, prompt)

        framework = result.get('framework', [])
        research.framework = framework
        await ResearchDao.update(db, research)

        # 创建章节记录
        for item in framework:
            existing = await ResearchDao.get_chapter_by_index(db, research_id, item.get('index', 0))
            if not existing:
                await ResearchDao.create_chapter(db, EduResearchChapter(
                    research_id=research_id,
                    chapter_index=item.get('index', 0),
                    chapter_title=item.get('title', ''),
                ))

        return result

    @classmethod
    async def generate_framework_stream(cls, db: AsyncSession, research_id: int, selected_question: str, model_id: int = 1) -> AsyncGenerator[str, None]:
        """AI流式生成论文框架"""
        research = await ResearchDao.get_by_id(db, research_id)
        if not research:
            yield json.dumps({'type': 'error', 'message': '研究数据不存在'}, ensure_ascii=False) + '\n'
            return

        research.selected_question = selected_question
        research.update_time = datetime.now()

        prompt = RESEARCH_FRAMEWORK_STREAM_PROMPT.format(
            selected_question=selected_question,
            material_summary=research.material_summary or '',
        )

        from module_learning.service.llm_call import AiCall

        full_text = ''
        yield json.dumps({'type': 'status', 'message': 'AI 正在生成论文框架...'}, ensure_ascii=False) + '\n'
        async for chunk in AiCall.call_llm_stream(db, model_id, prompt):
            try:
                parsed = json.loads(chunk.strip())
                if parsed.get('type') == 'content' and parsed.get('content'):
                    content = parsed['content']
                    full_text += content
                    for char in content:
                        yield json.dumps({'type': 'content', 'content': char}, ensure_ascii=False) + '\n'
                else:
                    yield chunk
            except (json.JSONDecodeError, AttributeError):
                yield chunk

        try:
            framework = cls._parse_streamed_framework(full_text)
            research.framework = framework
            await ResearchDao.update(db, research)

            # 创建章节记录
            for item in framework:
                existing = await ResearchDao.get_chapter_by_index(db, research_id, item.get('index', 0))
                if not existing:
                    await ResearchDao.create_chapter(db, EduResearchChapter(
                        research_id=research_id,
                        chapter_index=item.get('index', 0),
                        chapter_title=item.get('title', ''),
                    ))

            # 重新查询获取含 chapter_id 的完整章节列表
            chapters = await ResearchDao.get_chapters(db, research_id)
            chapter_list = [
                {
                    'chapter_id': c.chapter_id,
                    'chapter_index': c.chapter_index,
                    'chapter_title': c.chapter_title,
                    'content': c.content,
                    'ai_suggestion': c.ai_suggestion,
                    'status': c.status,
                }
                for c in chapters
            ]

            yield json.dumps({
                'type': 'result',
                'data': {
                    'framework': framework,
                    'chapters': chapter_list,
                },
            }, ensure_ascii=False) + '\n'
        except Exception as e:
            yield json.dumps({'type': 'error', 'message': f'框架解析失败：{str(e)}'}, ensure_ascii=False) + '\n'

    @staticmethod
    def _parse_streamed_framework(text: str) -> list[dict]:
        """Parse the readable streamed framework format into structure."""
        try:
            parsed = parse_llm_json(text)
            if isinstance(parsed, dict) and isinstance(parsed.get('framework'), list):
                return parsed['framework']
        except Exception:
            pass

        blocks = re.split(r'(?:^|\n)\s*(?=\d+[\.、]\s*)', text.strip())
        framework = []
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            title_match = re.match(r'\d+[\.、]\s*(.+?)(?:\n|$)', block)
            desc_match = re.search(r'章节说明[:：]\s*(.+?)(?=\n\s*\d+[\.、]|\Z)', block, re.S)
            if title_match:
                framework.append({
                    'index': len(framework) + 1,
                    'title': title_match.group(1).strip(),
                    'description': desc_match.group(1).strip() if desc_match else '',
                })

        if framework:
            return framework

        cleaned = text.strip()
        return [{'index': 1, 'title': '论文大纲', 'description': cleaned}] if cleaned else []

    @classmethod
    async def save_chapter(cls, db: AsyncSession, data: ResearchChapterSaveModel, student_id: int) -> dict:
        """保存章节内容"""
        chapter = await ResearchDao.get_chapter_by_index(db, data.research_id, data.chapter_index)
        if chapter:
            chapter.content = data.content
            chapter.update_time = datetime.now()
            await ResearchDao.update_chapter(db, chapter)
        else:
            chapter = EduResearchChapter(
                research_id=data.research_id,
                chapter_index=data.chapter_index,
                content=data.content,
            )
            await ResearchDao.create_chapter(db, chapter)
        return {'research_id': data.research_id, 'chapter_index': data.chapter_index}

    @classmethod
    async def chapter_draft(cls, db: AsyncSession, research_id: int, chapter_index: int, model_id: int = 1) -> str:
        """AI辅助撰写章节"""
        research = await ResearchDao.get_by_id(db, research_id)
        if not research:
            raise ValueError('研究数据不存在')

        chapter = await ResearchDao.get_chapter_by_index(db, research_id, chapter_index)
        chapter_title = chapter.chapter_title if chapter else f'第{chapter_index}章'

        framework_summary = ''
        if research.framework:
            framework_summary = '\n'.join([
                f"- {f.get('title', '')}: {f.get('description', '')}"
                for f in research.framework
            ])

        prompt = CHAPTER_DRAFT_PROMPT.format(
            selected_question=research.selected_question or '',
            chapter_title=chapter_title,
            framework_summary=framework_summary,
            material_summary=research.material_summary or '',
        )

        from module_learning.service.llm_call import AiCall
        result = await AiCall.call_llm_non_stream(db, model_id, prompt)

        # 保存AI建议
        if chapter:
            chapter.ai_suggestion = result
            chapter.update_time = datetime.now()
            await ResearchDao.update_chapter(db, chapter)

        return result

    @classmethod
    async def chapter_draft_stream(cls, db: AsyncSession, research_id: int, chapter_index: int, model_id: int = 1) -> AsyncGenerator[str, None]:
        """AI流式辅助撰写章节"""
        research = await ResearchDao.get_by_id(db, research_id)
        if not research:
            yield json.dumps({'type': 'error', 'message': '研究数据不存在'}, ensure_ascii=False) + '\n'
            return

        chapter = await ResearchDao.get_chapter_by_index(db, research_id, chapter_index)
        chapter_title = chapter.chapter_title if chapter else f'第{chapter_index}章'

        framework_summary = ''
        if research.framework:
            framework_summary = '\n'.join([
                f"- {f.get('title', '')}: {f.get('description', '')}"
                for f in research.framework
            ])

        prompt = CHAPTER_DRAFT_PROMPT.format(
            selected_question=research.selected_question or '',
            chapter_title=chapter_title,
            framework_summary=framework_summary,
            material_summary=research.material_summary or '',
        )

        from module_learning.service.llm_call import AiCall

        full_text = ''
        yield json.dumps({'type': 'status', 'message': f'AI 正在为「{chapter_title}」撰写草稿...'}, ensure_ascii=False) + '\n'
        async for chunk in AiCall.call_llm_stream(db, model_id, prompt):
            try:
                parsed = json.loads(chunk.strip())
                if parsed.get('type') == 'content' and parsed.get('content'):
                    content = parsed['content']
                    full_text += content
                    for char in content:
                        yield json.dumps({'type': 'content', 'content': char}, ensure_ascii=False) + '\n'
                else:
                    yield chunk
            except (json.JSONDecodeError, AttributeError):
                yield chunk

        # 保存AI建议
        if chapter:
            chapter.ai_suggestion = full_text
            chapter.update_time = datetime.now()
            await ResearchDao.update_chapter(db, chapter)

        yield json.dumps({
            'type': 'result',
            'data': {
                'chapter_index': chapter_index,
                'ai_suggestion': full_text,
            },
        }, ensure_ascii=False) + '\n'

    @classmethod
    async def recommend_references(cls, db: AsyncSession, research_id: int, model_id: int = 1) -> dict:
        """AI推荐参考文献"""
        research = await ResearchDao.get_by_id(db, research_id)
        if not research:
            raise ValueError('研究数据不存在')

        prompt = REFERENCES_PROMPT.format(
            selected_question=research.selected_question or '',
            material_summary=research.material_summary or '',
        )

        from module_learning.service.llm_call import AiCall
        result = await AiCall.call_llm_json(db, model_id, prompt)

        references = result.get('references', [])
        research.ref_literature = references
        research.update_time = datetime.now()
        await ResearchDao.update(db, research)

        return result

    @classmethod
    async def recommend_references_stream(cls, db: AsyncSession, research_id: int, model_id: int = 1) -> AsyncGenerator[str, None]:
        """AI流式推荐参考文献"""
        research = await ResearchDao.get_by_id(db, research_id)
        if not research:
            yield json.dumps({'type': 'error', 'message': '研究数据不存在'}, ensure_ascii=False) + '\n'
            return

        prompt = REFERENCES_STREAM_PROMPT.format(
            selected_question=research.selected_question or '',
            material_summary=research.material_summary or '',
        )

        from module_learning.service.llm_call import AiCall

        full_text = ''
        yield json.dumps({'type': 'status', 'message': 'AI 正在推荐相关文献...'}, ensure_ascii=False) + '\n'
        async for chunk in AiCall.call_llm_stream(db, model_id, prompt):
            try:
                parsed = json.loads(chunk.strip())
                if parsed.get('type') == 'content' and parsed.get('content'):
                    content = parsed['content']
                    full_text += content
                    for char in content:
                        yield json.dumps({'type': 'content', 'content': char}, ensure_ascii=False) + '\n'
                else:
                    yield chunk
            except (json.JSONDecodeError, AttributeError):
                yield chunk

        try:
            references = cls._parse_streamed_references(full_text)
            research.ref_literature = references
            research.update_time = datetime.now()
            await ResearchDao.update(db, research)
            yield json.dumps({
                'type': 'result',
                'data': {
                    'references': references,
                },
            }, ensure_ascii=False) + '\n'
        except Exception as e:
            yield json.dumps({'type': 'error', 'message': f'文献解析失败：{str(e)}'}, ensure_ascii=False) + '\n'

    @staticmethod
    def _parse_streamed_references(text: str) -> list[dict]:
        """Parse the readable streamed references format into structure."""
        try:
            parsed = parse_llm_json(text)
            if isinstance(parsed, dict) and isinstance(parsed.get('references'), list):
                return parsed['references']
        except Exception:
            pass

        blocks = re.split(r'(?:^|\n)\s*(?=\d+[\.、]\s*)', text.strip())
        references = []
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            lines = block.split('\n')
            citation = re.sub(r'^\d+[\.、]\s*', '', lines[0].strip())
            rel_match = re.search(r'关联说明[:：]\s*(.+)', block, re.S)
            if citation:
                references.append({
                    'citation': citation,
                    'relevance': rel_match.group(1).strip() if rel_match else '',
                })

        if references:
            return references

        cleaned = text.strip()
        return [{'citation': cleaned, 'relevance': ''}] if cleaned else []

    @classmethod
    async def get_detail(cls, db: AsyncSession, record_id: int) -> dict | None:
        """研究区完整数据"""
        research = await ResearchDao.get_by_record_id(db, record_id)
        if not research:
            return None
        chapters = await ResearchDao.get_chapters(db, research.research_id)
        return {
            'research_id': research.research_id,
            'record_id': research.record_id,
            'material_summary': research.material_summary,
            'candidate_questions': research.candidate_questions,
            'selected_question': research.selected_question,
            'framework': research.framework,
            'ref_literature': research.ref_literature,
            'status': research.status,
            'chapters': [
                {
                    'chapter_id': c.chapter_id,
                    'chapter_index': c.chapter_index,
                    'chapter_title': c.chapter_title,
                    'content': c.content,
                    'ai_suggestion': c.ai_suggestion,
                    'status': c.status,
                }
                for c in chapters
            ],
            'create_time': str(research.create_time) if research.create_time else None,
        }

    @classmethod
    async def submit(cls, db: AsyncSession, record_id: int, student_id: int) -> dict:
        """提交研究成果"""
        from module_learning.service.record_service import RecordService
        return await RecordService.advance_stage(db, record_id, student_id)
