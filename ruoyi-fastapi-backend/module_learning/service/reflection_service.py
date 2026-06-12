import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

from sqlalchemy.ext.asyncio import AsyncSession

from module_learning.dao.reflection_dao import ReflectionDao
from module_learning.dao.record_dao import RecordDao
from module_learning.dao.scenario_dao import ScenarioDao
from module_learning.dao.decision_dao import DecisionDao
from module_learning.entity.do.reflection_do import EduReflectionData, EduReflectionDialogue, EduReflectionDepthHistory
from module_learning.entity.vo.reflection_vo import ReflectionSaveModel


REFLECTION_PROMPT = """你是一位引导反思的社会工作教育者，擅长结合专业理论指导学生从"描述经历"走向"反身性反思"。

学生的实践背景：
- 情境描述：{scenario_summary}
- 关键决策：{decision_summary}
- 历史反思记录（最近2次）：{reflection_history}

反思深度评估规则：
- 描述性（0.20-0.40）：仅复述事件经过和个人感受
- 分析性（0.41-0.70）：开始分析事件原因、互动模式、策略选择
- 反身性（0.71-1.00）：审视自身价值观、立场、权力关系对实践的影响

当前学生的反思文本：
{reflection_text}

相关专业理论参考（来自知识库检索）：
{retrieved_knowledge}

任务：
1. 评估当前反思的深度（给出分数和等级）
2. 从上述理论参考中选取 1-2 个最相关的理论，给出**具体的指导意见**：
   - 说明该理论为什么与学生的反思相关（relevance）
   - 给出基于该理论的具体反思建议（suggestion），帮助学生从当前层次向下一层次深化
3. 综合以上理论指导，给出一个整体的反思方向建议（reflection_direction）
4. 根据当前深度，生成 2-3 个推动反思深化的追问

输出 JSON（严格按此格式）：
{{
  "depth_score": 0.65,
  "depth_level": "analytical",
  "theory_guidance": [
    {{
      "theory_name": "赋权理论",
      "theory_source": "Solomon (1976)",
      "relevance": "该理论与你反思中提到的...直接相关，因为...",
      "suggestion": "建议你从服务对象的能力和优势出发，重新审视你在...中的角色定位，思考..."
    }}
  ],
  "reflection_direction": "基于以上理论，建议你从...角度继续反思，重点关注...",
  "questions": [
    {{"level": "reflexive", "question": "追问内容", "purpose": "引导目的"}}
  ]
}}"""

QUICK_EVAL_PROMPT = """评估以下反思文本的深度层次，只需输出 JSON，不要其他内容：
- 描述性（0.20-0.40）：只复述经历
- 分析性（0.41-0.70）：分析原因和互动模式
- 反身性（0.71-1.00）：审视自身价值观和权力位置

文本：{text}

输出：{{"depth_score": 0.65, "depth_level": "analytical"}}"""

EVALUATE_THROTTLE_SECONDS = 30


class ReflectionService:

    @classmethod
    async def save(cls, db: AsyncSession, data: ReflectionSaveModel, student_id: int, model_id: int = 1) -> dict:
        """保存反思文本，带防抖深度评估"""
        record = await RecordDao.get_by_id(db, data.record_id)
        if not record:
            raise ValueError('学习记录不存在')

        # 查找或创建 reflection
        reflection = await ReflectionDao.get_by_record_id(db, data.record_id)
        if not reflection:
            # 需要关联 scenario
            scenario = await ScenarioDao.get_by_record_id(db, data.record_id)
            scenario_id = scenario.scenario_id if scenario else 0
            reflection = EduReflectionData(
                record_id=data.record_id,
                scenario_id=scenario_id,
                student_id=student_id,
            )
            reflection = await ReflectionDao.create(db, reflection)
            # 回填 record
            record.reflection_id = reflection.reflection_id
            record.reflection_status = '1'
            record.update_time = datetime.now()
            await RecordDao.update(db, record)

        # 更新内容
        reflection.content = data.content
        reflection.version = (reflection.version or 0) + 1

        # 防抖深度评估
        should_evaluate = await cls._should_evaluate(db, reflection.reflection_id)
        if should_evaluate and data.content.strip():
            try:
                depth_result = await cls._quick_depth_evaluate(db, data.content, model_id)
                reflection.depth_score = depth_result.get('depth_score', 0.3)
                reflection.depth_level = depth_result.get('depth_level', 'descriptive')
                # 记录深度历史
                await ReflectionDao.add_depth_history(db, EduReflectionDepthHistory(
                    reflection_id=reflection.reflection_id,
                    depth_score=reflection.depth_score,
                    depth_level=reflection.depth_level,
                    trigger_type='save',
                ))
            except Exception:
                pass

        reflection.update_time = datetime.now()
        await ReflectionDao.update(db, reflection)
        return {
            'reflection_id': reflection.reflection_id,
            'depth_score': float(reflection.depth_score) if reflection.depth_score else None,
            'depth_level': reflection.depth_level,
        }

    @classmethod
    async def generate_questions(cls, db: AsyncSession, reflection_id: int, model_id: int = 1) -> dict:
        """AI生成结构化提问（核心接口）"""
        reflection = await ReflectionDao.get_by_id(db, reflection_id)
        if not reflection:
            raise ValueError('反思数据不存在')

        # 准备上下文
        scenario_summary = await cls._get_scenario_summary(db, reflection.record_id)
        decision_summary = await cls._get_decision_summary(db, reflection.record_id)
        dialogues = await ReflectionDao.get_dialogues(db, reflection_id)
        reflection_history = '\n'.join([
            f"{'AI' if d.role == 'assistant' else '学生'}：{d.content[:100]}"
            for d in dialogues[-4:]
        ]) if dialogues else '（无历史对话）'

        # RAG 检索理论
        retrieved_knowledge = await cls._retrieve_theory_knowledge(db, reflection)
        logger.info('[反思区] RAG检索结果长度: %d', len(retrieved_knowledge or ''))

        prompt = REFLECTION_PROMPT.format(
            scenario_summary=scenario_summary,
            decision_summary=decision_summary,
            reflection_history=reflection_history or '（无历史）',
            reflection_text=reflection.content or '（学生尚未输入反思内容）',
            retrieved_knowledge=retrieved_knowledge or '（暂无相关理论参考）',
        )

        from module_learning.service.llm_call import AiCall
        logger.info('[反思区] 开始调用LLM, reflection_id=%s, model_id=%s', reflection_id, model_id)
        result = await AiCall.call_llm_json(db, model_id, prompt)
        logger.info('[反思区] LLM返回结果: depth_score=%s, depth_level=%s',
                    result.get('depth_score'), result.get('depth_level'))

        # 保存 AI 对话记录
        old_score = float(reflection.depth_score) if reflection.depth_score else 0.0
        new_score = result.get('depth_score', old_score)

        # 兼容新旧格式：优先用 theory_guidance，降级用 theories
        theory_guidance = result.get('theory_guidance', [])
        theories = result.get('theories', [])

        await ReflectionDao.add_dialogue(db, EduReflectionDialogue(
            reflection_id=reflection_id,
            role='assistant',
            content=json.dumps(result, ensure_ascii=False),
            question_level=result.get('depth_level', ''),
            depth_score_before=old_score,
            depth_score_after=new_score,
            linked_theories=theory_guidance if theory_guidance else theories,
        ))

        # 更新反思数据
        reflection.depth_score = new_score
        reflection.depth_level = result.get('depth_level', reflection.depth_level)
        reflection.linked_theories = theory_guidance if theory_guidance else theories
        reflection.update_time = datetime.now()
        await ReflectionDao.update(db, reflection)

        # 记录深度历史
        await ReflectionDao.add_depth_history(db, EduReflectionDepthHistory(
            reflection_id=reflection_id,
            depth_score=new_score,
            depth_level=result.get('depth_level', ''),
            trigger_type='ai_question',
        ))

        return result

    @classmethod
    async def confirm(cls, db: AsyncSession, record_id: int, user_id: int) -> dict:
        """确认反思完成"""
        reflection = await ReflectionDao.get_by_record_id(db, record_id)
        if not reflection or not reflection.content:
            raise ValueError('请先保存反思内容')
        reflection.status = '1'
        reflection.update_time = datetime.now()
        await ReflectionDao.update(db, reflection)

        # 更新学习记录状态
        record = await RecordDao.get_by_id(db, record_id)
        if record:
            record.reflection_status = '2'
            record.update_time = datetime.now()
            await RecordDao.update(db, record)

        return {'reflection_id': reflection.reflection_id, 'status': 'confirmed'}

    @classmethod
    async def get_depth(cls, db: AsyncSession, reflection_id: int) -> dict:
        """获取当前深度评估"""
        reflection = await ReflectionDao.get_by_id(db, reflection_id)
        if not reflection:
            raise ValueError('反思数据不存在')
        return {
            'depth_score': float(reflection.depth_score) if reflection.depth_score else 0.0,
            'depth_level': reflection.depth_level,
        }

    @classmethod
    async def get_depth_history(cls, db: AsyncSession, reflection_id: int) -> list:
        """深度变化曲线数据"""
        history = await ReflectionDao.get_depth_history(db, reflection_id)
        return [
            {
                'history_id': h.history_id,
                'depth_score': float(h.depth_score),
                'depth_level': h.depth_level,
                'trigger_type': h.trigger_type,
                'create_time': str(h.create_time) if h.create_time else None,
            }
            for h in history
        ]

    @classmethod
    async def get_detail(cls, db: AsyncSession, record_id: int) -> dict | None:
        """反思区完整数据"""
        reflection = await ReflectionDao.get_by_record_id(db, record_id)
        if not reflection:
            return None
        dialogues = await ReflectionDao.get_dialogues(db, reflection.reflection_id)
        return {
            'reflection_id': reflection.reflection_id,
            'record_id': reflection.record_id,
            'content': reflection.content,
            'depth_level': reflection.depth_level,
            'depth_score': float(reflection.depth_score) if reflection.depth_score else 0.0,
            'linked_theories': reflection.linked_theories,
            'version': reflection.version,
            'status': reflection.status,
            'dialogues': [
                {
                    'dialogue_id': d.dialogue_id,
                    'role': d.role,
                    'content': d.content,
                    'question_level': d.question_level,
                    'depth_score_before': float(d.depth_score_before) if d.depth_score_before else None,
                    'depth_score_after': float(d.depth_score_after) if d.depth_score_after else None,
                    'linked_theories': d.linked_theories,
                    'create_time': str(d.create_time) if d.create_time else None,
                }
                for d in dialogues
            ],
            'create_time': str(reflection.create_time) if reflection.create_time else None,
            'update_time': str(reflection.update_time) if reflection.update_time else None,
        }

    @classmethod
    async def _should_evaluate(cls, db: AsyncSession, reflection_id: int) -> bool:
        """防抖检查"""
        last = await ReflectionDao.get_latest_depth(db, reflection_id)
        if not last:
            return True
        elapsed = (datetime.now() - last.create_time).total_seconds()
        return elapsed >= EVALUATE_THROTTLE_SECONDS

    @classmethod
    async def _quick_depth_evaluate(cls, db: AsyncSession, content: str, model_id: int) -> dict:
        """快速深度评估"""
        from module_learning.service.llm_call import AiCall
        prompt = QUICK_EVAL_PROMPT.format(text=content[:500])
        return await AiCall.call_llm_json(db, model_id, prompt)

    @classmethod
    async def _get_scenario_summary(cls, db: AsyncSession, record_id: int) -> str:
        scenario = await ScenarioDao.get_by_record_id(db, record_id)
        if not scenario:
            return '（无情境数据）'
        problems = scenario.identified_problems or []
        titles = [p.get('title', '') for p in problems[:3]] if problems else []
        return f"场景：{(scenario.description or '')[:200]}...\n核心问题：{', '.join(titles)}"

    @classmethod
    async def _get_decision_summary(cls, db: AsyncSession, record_id: int) -> str:
        decisions = await DecisionDao.get_by_record_id(db, record_id)
        if not decisions:
            return '（无决策记录）'
        summaries = []
        for d in decisions[:3]:
            summaries.append(
                f"- 节点「{(d.key_event_desc or '')[:30]}」："
                f"{'介入' if d.is_intervened else '未介入'}，{(d.action_taken or '')[:50]}"
            )
        return '\n'.join(summaries)

    @classmethod
    async def _retrieve_theory_knowledge(cls, db: AsyncSession, reflection: EduReflectionData) -> str:
        """RAG 检索理论"""
        try:
            record = await RecordDao.get_by_id(db, reflection.record_id)
            if not record or not record.task_id:
                logger.warning('[反思区] record无task_id, record_id=%s', reflection.record_id)
                return '（暂无理论库配置）'
            from module_learning.dao.task_dao import TaskDao
            task = await TaskDao.get_by_id(db, record.task_id)
            if not task or not task.reflection_kb_ids:
                logger.warning('[反思区] task无reflection_kb_ids, task_id=%s', record.task_id)
                return '（暂无理论库配置）'

            from module_rag.service.embedding_service import EmbeddingService
            from module_rag.service.retrieval_service import RetrievalService

            query_text = reflection.content or ''
            if not query_text.strip():
                return ''
            query_embedding = await EmbeddingService.embed_single(query_text)
            chunks = await RetrievalService.hybrid_search(
                db=db,
                query_text=query_text,
                query_embedding=query_embedding,
                kb_ids=task.reflection_kb_ids,
                top_k=4,
            )
            logger.info('[反思区] RAG检索到 %d 条理论片段, kb_ids=%s', len(chunks), task.reflection_kb_ids)
            return '\n\n'.join([f'【{c["content"][:200]}】' for c in chunks])
        except Exception as e:
            logger.error('[反思区] RAG理论检索异常: %s', e, exc_info=True)
            return '（理论检索暂不可用）'
