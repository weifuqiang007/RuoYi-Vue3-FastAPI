from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from module_learning.dao.scenario_dao import ScenarioDao
from module_learning.dao.record_dao import RecordDao
from module_learning.entity.do.scenario_do import EduScenarioData, EduScenarioDialogue
from module_learning.entity.vo.scenario_vo import ScenarioSaveModel


# 情境区AI分析 Prompt
SCENARIO_ANALYZE_PROMPT = """你是一位经验丰富的社会工作督导，擅长帮助实习社工分析实践情境。

任务：根据学生描述的实践场景，完成以下工作：
1. 识别场景中的关键事件节点（2-4个，按时间顺序）
2. 界定其中蕴含的专业问题（2-3个）
3. 判断问题所属的社会工作实践领域
4. 提出追问建议，帮助学生补充关键信息

专业知识参考：
{retrieved_knowledge}

学生场景描述：
{student_scenario}

请以专业但易于理解的语气回复。
输出 JSON 格式：
{{
  "key_events": [
    {{"index": 1, "event": "事件描述"}}
  ],
  "identified_problems": [
    {{"title": "问题标题", "description": "详细描述", "domain": "社工领域"}}
  ],
  "category_tags": ["老年社工", "危机干预"],
  "followup_questions": ["追问1", "追问2"]
}}"""

SCENARIO_FOLLOWUP_PROMPT = """你是一位经验丰富的社会工作督导。

当前学生的场景描述：
{student_scenario}

已识别的关键事件：
{key_events}

对话历史：
{dialogue_history}

你的任务：针对场景中信息不够完整的地方，追问一个最关键的问题。
要求：
- 只问一个问题
- 问题要具体，指向场景中的关键细节
- 语气温和，像督导引导实习生一样
直接输出问题文本即可。"""


class ScenarioService:

    @classmethod
    async def save(cls, db: AsyncSession, data: ScenarioSaveModel, student_id: int) -> dict:
        """保存/更新情境描述"""
        record = await RecordDao.get_by_id(db, data.record_id)
        if not record:
            raise ValueError('学习记录不存在')

        # 查找或创建 scenario
        scenario = await ScenarioDao.get_by_record_id(db, data.record_id)
        if not scenario:
            scenario = EduScenarioData(
                record_id=data.record_id,
                student_id=student_id,
            )
            scenario = await ScenarioDao.create(db, scenario)
            # 回填 record
            record.scenario_id = scenario.scenario_id
            record.scenario_status = '1'
            record.update_time = datetime.now()
            await RecordDao.update(db, record)

        # 更新字段
        if data.description is not None:
            scenario.description = data.description
        if data.key_events is not None:
            scenario.key_events = data.key_events
        if data.identified_problems is not None:
            scenario.identified_problems = data.identified_problems
        if data.category_tags is not None:
            scenario.category_tags = data.category_tags
        scenario.update_time = datetime.now()
        await ScenarioDao.update(db, scenario)

        return {'scenario_id': scenario.scenario_id}

    @classmethod
    async def analyze(cls, db: AsyncSession, scenario_id: int, model_id: int = 1) -> dict:
        """AI首次分析情境"""
        scenario = await ScenarioDao.get_by_id(db, scenario_id)
        if not scenario:
            raise ValueError('情境数据不存在')

        # RAG 检索（如果有配置知识库）
        knowledge_context = await cls._retrieve_knowledge(db, scenario)

        # 构建 Prompt
        prompt = SCENARIO_ANALYZE_PROMPT.format(
            retrieved_knowledge=knowledge_context,
            student_scenario=scenario.description or '',
        )

        # 调用 LLM
        from module_learning.service.llm_call import AiCall
        result = await AiCall.call_llm_json(db, model_id, prompt)

        # 保存分析结果到 scenario
        if 'key_events' in result:
            scenario.key_events = result['key_events']
        if 'identified_problems' in result:
            scenario.identified_problems = result['identified_problems']
        if 'category_tags' in result:
            scenario.category_tags = result['category_tags']
        scenario.update_time = datetime.now()
        await ScenarioDao.update(db, scenario)

        # 保存 AI 对话记录
        await ScenarioDao.add_dialogue(db, EduScenarioDialogue(
            scenario_id=scenario_id,
            role='assistant',
            content=str(result),
            dialogue_type='analyze',
        ))

        return result

    @classmethod
    async def followup(cls, db: AsyncSession, scenario_id: int, user_message: str | None, model_id: int = 1) -> str:
        """AI追问"""
        scenario = await ScenarioDao.get_by_id(db, scenario_id)
        if not scenario:
            raise ValueError('情境数据不存在')

        # 保存用户消息
        if user_message:
            await ScenarioDao.add_dialogue(db, EduScenarioDialogue(
                scenario_id=scenario_id,
                role='user',
                content=user_message,
                dialogue_type='followup',
            ))

        # 获取对话历史
        dialogues = await ScenarioDao.get_dialogues(db, scenario_id)
        history = '\n'.join([
            f"{'AI' if d.role == 'assistant' else '学生'}：{d.content[:200]}"
            for d in dialogues[-6:]
        ])

        prompt = SCENARIO_FOLLOWUP_PROMPT.format(
            student_scenario=scenario.description or '',
            key_events=str(scenario.key_events or [])[:500],
            dialogue_history=history or '（无历史对话）',
        )

        from module_learning.service.llm_call import AiCall
        result = await AiCall.call_llm_non_stream(db, model_id, prompt)

        # 保存 AI 追问
        await ScenarioDao.add_dialogue(db, EduScenarioDialogue(
            scenario_id=scenario_id,
            role='assistant',
            content=result,
            dialogue_type='followup',
        ))

        return result

    @classmethod
    async def confirm(cls, db: AsyncSession, record_id: int, student_id: int) -> dict:
        """确认情境完成"""
        scenario = await ScenarioDao.get_by_record_id(db, record_id)
        if not scenario or not scenario.description:
            raise ValueError('请先保存场景描述')
        scenario.status = '1'
        scenario.update_time = datetime.now()
        await ScenarioDao.update(db, scenario)
        return {'scenario_id': scenario.scenario_id, 'status': 'confirmed'}

    @classmethod
    async def get_detail(cls, db: AsyncSession, record_id: int) -> dict | None:
        """获取情境区完整数据"""
        scenario = await ScenarioDao.get_by_record_id(db, record_id)
        if not scenario:
            return None
        dialogues = await ScenarioDao.get_dialogues(db, scenario.scenario_id)
        return {
            'scenario_id': scenario.scenario_id,
            'record_id': scenario.record_id,
            'description': scenario.description,
            'key_events': scenario.key_events,
            'identified_problems': scenario.identified_problems,
            'category_tags': scenario.category_tags,
            'status': scenario.status,
            'dialogues': [
                {
                    'dialogue_id': d.dialogue_id,
                    'role': d.role,
                    'content': d.content,
                    'dialogue_type': d.dialogue_type,
                    'create_time': str(d.create_time) if d.create_time else None,
                }
                for d in dialogues
            ],
            'create_time': str(scenario.create_time) if scenario.create_time else None,
            'update_time': str(scenario.update_time) if scenario.update_time else None,
        }

    @classmethod
    async def _retrieve_knowledge(cls, db: AsyncSession, scenario: EduScenarioData) -> str:
        """RAG 检索相关知识"""
        try:
            # 获取任务配置的知识库
            record = await RecordDao.get_by_id(db, scenario.record_id)
            if not record or not record.task_id:
                return '（暂无知识库配置）'
            from module_learning.dao.task_dao import TaskDao
            task = await TaskDao.get_by_id(db, record.task_id)
            if not task or not task.scenario_kb_ids:
                return '（暂无知识库配置）'

            from module_rag.service.embedding_service import EmbeddingService
            from module_rag.service.retrieval_service import RetrievalService

            query_embedding = await EmbeddingService.embed_single(scenario.description)
            chunks = await RetrievalService.hybrid_search(
                db=db,
                query_text=scenario.description,
                query_embedding=query_embedding,
                kb_ids=task.scenario_kb_ids,
                top_k=5,
            )
            return '\n\n'.join([
                f'【参考{i+1}】{c["content"][:300]}'
                for i, c in enumerate(chunks)
            ])
        except Exception:
            return '（知识检索暂不可用）'
