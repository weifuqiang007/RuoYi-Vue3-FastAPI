from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from module_learning.dao.research_dao import ResearchDao
from module_learning.dao.record_dao import RecordDao
from module_learning.dao.scenario_dao import ScenarioDao
from module_learning.dao.decision_dao import DecisionDao
from module_learning.dao.reflection_dao import ReflectionDao
from module_learning.entity.do.research_do import EduResearchData, EduResearchChapter
from module_learning.entity.vo.research_vo import ResearchChapterSaveModel


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


class ResearchService:

    @classmethod
    async def init_research(cls, db: AsyncSession, record_id: int, student_id: int, model_id: int = 1) -> dict:
        """初始化研究区，汇总前三区材料"""
        record = await RecordDao.get_by_id(db, record_id)
        if not record:
            raise ValueError('学习记录不存在')

        # 汇总材料
        scenario = await ScenarioDao.get_by_record_id(db, record_id)
        decisions = await DecisionDao.get_by_record_id(db, record_id)
        reflection = await ReflectionDao.get_by_record_id(db, record_id)

        material_summary = f"情境：{(scenario.description or '')[:300] if scenario else '无'}\n"
        material_summary += f"决策数：{len(decisions)}\n"
        material_summary += f"反思：{(reflection.content or '')[:300] if reflection else '无'}"

        # 查找或创建
        research = await ResearchDao.get_by_record_id(db, record_id)
        if not research:
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
        else:
            research.material_summary = material_summary
            research.update_time = datetime.now()
            await ResearchDao.update(db, research)

        return {
            'research_id': research.research_id,
            'material_summary': material_summary,
        }

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
