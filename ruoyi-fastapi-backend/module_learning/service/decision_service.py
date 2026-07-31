from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from module_learning.dao.decision_dao import DecisionDao
from module_learning.dao.record_dao import RecordDao
from module_learning.entity.do.decision_do import EduDecisionData, EduDecisionDialogue
from module_learning.entity.vo.decision_vo import DecisionSaveModel
from utils.log_util import logger


DECISION_ETHICS_PROMPT = """你是一位社会工作伦理专家，正在指导一位实习社工分析其在实践中的伦理决策。

当前关键事件：
{key_event_desc}

学生的决策记录：
- 是否介入：{is_intervened}
- 具体行动：{action_taken}
- 行动理由：{reasoning}
- 心理活动：{psychological_state}

相关伦理知识参考：
{retrieved_ethics_knowledge}

任务：
1. 识别这个决策涉及的伦理维度
2. 引用相关的伦理守则条款
3. 分析这个决策的伦理合理性
4. 提出需要进一步思考的伦理问题

语气要引导性，而非评判性。
输出 JSON 格式：
{{
  "ethics_dimensions": [
    {{"name": "伦理维度名称", "description": "与本决策的关联", "stance": "支持/张力"}}
  ],
  "relevant_codes": [
    {{"code": "守则条款", "source": "来源", "relevance": "关联说明"}}
  ],
  "analysis": "综合伦理分析文本",
  "further_questions": ["需进一步思考的问题1", "问题2"]
}}"""


class DecisionService:

    @classmethod
    async def save(cls, db: AsyncSession, data: DecisionSaveModel, student_id: int) -> dict:
        """保存决策记录"""
        record = await RecordDao.get_by_id(db, data.record_id)
        if not record:
            raise ValueError('学习记录不存在')

        # 查找已有记录或创建
        decisions = await DecisionDao.get_by_record_id(db, data.record_id)
        existing = None
        if data.key_event_index is not None:
            for d in decisions:
                if d.key_event_index == data.key_event_index:
                    existing = d
                    break

        if existing:
            # 更新
            update_fields = data.model_dump(exclude_unset=True, exclude={'record_id', 'scenario_id'})
            for k, v in update_fields.items():
                setattr(existing, k, v)
            existing.update_time = datetime.now()
            await DecisionDao.update(db, existing)
            return {'decision_id': existing.decision_id}
        else:
            # 新建
            decision = EduDecisionData(
                record_id=data.record_id,
                scenario_id=data.scenario_id,
                student_id=student_id,
                key_event_index=data.key_event_index,
                key_event_desc=data.key_event_desc,
                is_intervened=data.is_intervened,
                action_taken=data.action_taken,
                reasoning=data.reasoning,
                psychological_state=data.psychological_state,
                alternatives=data.alternatives,
                expected_outcome=data.expected_outcome,
                actual_outcome=data.actual_outcome,
            )
            decision = await DecisionDao.create(db, decision)

            # 更新 record 的 decision_id
            record.decision_id = decision.decision_id
            record.decision_status = '1'
            record.update_time = datetime.now()
            await RecordDao.update(db, record)

            return {'decision_id': decision.decision_id}

    @classmethod
    async def ethics_analyze(cls, db: AsyncSession, decision_id: int, model_id: int = 1) -> dict:
        """AI伦理分析"""
        decision = await DecisionDao.get_by_id(db, decision_id)
        if not decision:
            raise ValueError('决策记录不存在')

        logger.info('[决策区] 开始伦理分析, decision_id=%s', decision_id)

        # 1. RAG 检索伦理知识
        try:
            knowledge_context = await cls._retrieve_ethics_knowledge(db, decision)
            logger.info('[决策区] 知识检索完成, decision_id=%s, 知识长度=%d', decision_id, len(knowledge_context))
        except Exception as e:
            logger.warning('[决策区] 知识检索失败, decision_id=%s, error=%s', decision_id, e)
            knowledge_context = '（伦理知识检索暂不可用）'

        # 2. 构建 Prompt 并调用 LLM
        prompt = DECISION_ETHICS_PROMPT.format(
            key_event_desc=decision.key_event_desc or '',
            is_intervened='是' if decision.is_intervened else '否',
            action_taken=decision.action_taken or '',
            reasoning=decision.reasoning or '',
            psychological_state=decision.psychological_state or '',
            retrieved_ethics_knowledge=knowledge_context,
        )

        from module_learning.service.llm_call import AiCall
        try:
            result = await AiCall.call_llm_json(db, model_id, prompt)
            logger.info('[决策区] LLM分析完成, decision_id=%s', decision_id)
        except Exception as e:
            logger.error('[决策区] LLM调用失败, decision_id=%s, error=%s', decision_id, e)
            raise ValueError(f'AI分析生成失败，请稍后重试。原因：{e}')

        # 3. 保存分析结果
        decision.ethics_analysis = result
        decision.update_time = datetime.now()
        await DecisionDao.update(db, decision)

        # 4. 保存对话记录
        await DecisionDao.add_dialogue(db, EduDecisionDialogue(
            decision_id=decision_id,
            role='assistant',
            content=str(result),
            dialogue_type='ethics_analyze',
        ))

        return result

    @classmethod
    async def get_list(cls, db: AsyncSession, record_id: int) -> list:
        """获取决策记录列表"""
        decisions = await DecisionDao.get_by_record_id(db, record_id)
        result = []
        for d in decisions:
            dialogues = await DecisionDao.get_dialogues(db, d.decision_id)
            result.append({
                'decision_id': d.decision_id,
                'record_id': d.record_id,
                'scenario_id': d.scenario_id,
                'key_event_index': d.key_event_index,
                'key_event_desc': d.key_event_desc,
                'is_intervened': d.is_intervened,
                'action_taken': d.action_taken,
                'reasoning': d.reasoning,
                'psychological_state': d.psychological_state,
                'alternatives': d.alternatives,
                'expected_outcome': d.expected_outcome,
                'actual_outcome': d.actual_outcome,
                'ethics_analysis': d.ethics_analysis,
                'status': d.status,
                'update_time': str(d.update_time) if d.update_time else None,
                'create_time': str(d.create_time) if d.create_time else None,
                'dialogues': [
                    {'role': dd.role, 'content': dd.content, 'dialogue_type': dd.dialogue_type}
                    for dd in dialogues
                ],
            })
        return result

    @classmethod
    async def confirm(cls, db: AsyncSession, record_id: int) -> dict:
        """确认决策完成"""
        decisions = await DecisionDao.get_by_record_id(db, record_id)
        if not decisions:
            raise ValueError('至少需要完成一条决策记录才能进入反思区')
        return {'record_id': record_id, 'decision_count': len(decisions)}

    @classmethod
    async def _retrieve_ethics_knowledge(cls, db: AsyncSession, decision: EduDecisionData) -> str:
        """RAG 检索伦理知识"""
        try:
            record = await RecordDao.get_by_id(db, decision.record_id)
            if not record or not record.task_id:
                return '（暂无伦理知识库配置）'
            from module_learning.dao.task_dao import TaskDao
            task = await TaskDao.get_by_id(db, record.task_id) # 3
            if not task or not task.decision_kb_ids:
                return '（暂无伦理知识库配置）'

            from module_rag.service.context_builder import RagContextBuilder

            query_text = f'{decision.key_event_desc or ""} {decision.action_taken or ""} {decision.reasoning or ""}'
            context = await RagContextBuilder.build(
                db=db,
                query_text=query_text,
                kb_ids=task.decision_kb_ids,
                top_k=5,
                max_chars_per_chunk=500,
            )
            logger.info('[决策区] RAG检索到 {} 条伦理知识', len(context.results))
            return context.text or '（未检索到足够相关的伦理知识）'
        except Exception as e:
            logger.warning('[决策区] 伦理知识检索异常: %s', e)
            return '（伦理知识检索暂不可用）'
