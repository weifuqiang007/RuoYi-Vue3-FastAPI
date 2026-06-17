import json
import re
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from utils.llm_json_parser import parse_llm_json
from module_learning.dao.reflection_dao import ReflectionDao
from module_learning.dao.record_dao import RecordDao
from module_learning.dao.scenario_dao import ScenarioDao
from module_learning.dao.decision_dao import DecisionDao
from module_learning.entity.do.reflection_do import EduReflectionData, EduReflectionDialogue, EduReflectionDepthHistory
from module_learning.entity.vo.reflection_vo import ReflectionSaveModel
from utils.log_util import logger


REFLECTION_PROMPT = """你是一位引导反思的社会工作教育者，擅长结合专业理论指导学生从"描述经历"走向"反身性反思"。

学生的实践背景：
- 情境描述：{scenario_summary}
- 当前决策上下文：{decision_context}
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


# 流式版 Prompt：先输出可读 Markdown（供逐字回显），最后以 ```json 代码块输出结构化结果（供解析存储）
REFLECTION_STREAM_PROMPT = """你是一位引导反思的社会工作教育者，擅长结合专业理论指导学生从"描述经历"走向"反身性反思"。

学生的实践背景：
- 情境描述：{scenario_summary}
- 当前决策上下文：{decision_context}
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
2. 从上述理论参考中选取 1-2 个最相关的理论，给出具体的指导意见（说明为何相关 + 基于该理论的具体建议）
3. 综合给出整体反思方向建议
4. 根据当前深度，生成 2-3 个推动反思深化的追问

输出要求（重要）：
先输出**可读的 Markdown**（给学生看的理论指导），包含：深度评估、关联理论（理论名/来源/关联/建议）、反思方向、追问；
最后**另起一行**，以下面的 JSON 代码块结尾（用于系统解析，不要省略）：
```json
{{
  "depth_score": 0.65,
  "depth_level": "analytical",
  "theory_guidance": [
    {{
      "theory_name": "赋权理论",
      "theory_source": "Solomon (1976)",
      "relevance": "该理论与学生反思中提到的...直接相关",
      "suggestion": "建议学生从...角度深化反思"
    }}
  ],
  "reflection_direction": "基于以上理论，建议从...角度继续反思",
  "questions": [
    {{"level": "reflexive", "question": "追问内容", "purpose": "引导目的"}}
  ]
}}
```"""


class ReflectionService:

    @classmethod
    async def save(cls, db: AsyncSession, data: ReflectionSaveModel, student_id: int, model_id: int = 1) -> dict:
        """保存反思文本，带防抖深度评估。按 decision_id 查找或创建反思。"""
        # 从 decision 反查 record_id 和 scenario_id
        decision = await DecisionDao.get_by_id(db, data.decision_id)
        if not decision:
            raise ValueError('决策记录不存在')
        record_id = decision.record_id
        scenario_id = decision.scenario_id

        # 查找或创建 reflection（按 decision_id 1:1）
        reflection = await ReflectionDao.get_by_decision_id(db, data.decision_id)
        if not reflection:
            reflection = EduReflectionData(
                record_id=record_id,
                decision_id=data.decision_id,
                scenario_id=scenario_id,
                student_id=student_id,
            )
            reflection = await ReflectionDao.create(db, reflection)
            # 首次保存：回填 record.reflection_id（advance_stage 前置校验依赖此字段）
            # 并标记反思进行中
            record = await RecordDao.get_by_id(db, record_id)
            if record:
                record.reflection_id = reflection.reflection_id
                if record.reflection_status != '1':
                    record.reflection_status = '1'
                record.update_time = datetime.now()
                await RecordDao.update(db, record)

        # 更新内容
        reflection.content = data.content
        reflection.version = (reflection.version or 0) + 1

        # 兜底回填 record.reflection_id：历史数据可能为空（advance_stage 前置校验依赖此字段）
        if reflection.reflection_id:
            record = await RecordDao.get_by_id(db, record_id)
            if record and not record.reflection_id:
                record.reflection_id = reflection.reflection_id
                if record.reflection_status == '0':
                    record.reflection_status = '1'
                record.update_time = datetime.now()
                await RecordDao.update(db, record)

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
            'decision_id': reflection.decision_id,
            'depth_score': float(reflection.depth_score) if reflection.depth_score else None,
            'depth_level': reflection.depth_level,
        }

    @classmethod
    async def generate_questions(cls, db: AsyncSession, reflection_id: int, model_id: int = 1) -> dict:
        """AI生成结构化提问（核心接口），注入该条决策的完整上下文"""
        reflection = await ReflectionDao.get_by_id(db, reflection_id)
        if not reflection:
            raise ValueError('反思数据不存在')

        # 准备上下文：注入该条决策的完整上下文
        scenario_summary = await cls._get_scenario_summary(db, reflection.record_id)
        decision_context = await cls._get_decision_context(db, reflection.decision_id)
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
            decision_context=decision_context,
            reflection_history=reflection_history or '（无历史）',
            reflection_text=reflection.content or '（学生尚未输入反思内容）',
            retrieved_knowledge=retrieved_knowledge or '（暂无相关理论参考）',
        )

        from module_learning.service.llm_call import AiCall
        logger.info('[反思区] 开始调用LLM, reflection_id=%s, decision_id=%s, model_id=%s',
                    reflection_id, reflection.decision_id, model_id)
        result = await AiCall.call_llm_json(db, model_id, prompt)
        logger.info('[反思区] LLM返回结果: depth_score=%s, depth_level=%s',
                    result.get('depth_score'), result.get('depth_level'))

        await cls._persist_guidance(db, reflection, result)
        return result

    @classmethod
    async def generate_questions_stream(cls, db: AsyncSession, reflection_id: int, model_id: int = 1):
        """
        流式生成理论指导（SSE）。
        流程：校验 → yield status → AiCall.call_llm_stream 逐字转发 → 结束后解析为结构化结果并落库 → yield result。
        兼容现有前端流式约定：消息类型 status / content / result / error。
        """
        reflection = await ReflectionDao.get_by_id(db, reflection_id)
        if not reflection:
            yield json.dumps({'type': 'error', 'message': '反思数据不存在'}, ensure_ascii=False) + '\n'
            return

        # 准备上下文（与非流式一致）
        # 获取场景的摘要和描述。
        scenario_summary = await cls._get_scenario_summary(db, reflection.record_id)
        # 获取决策的描述和上下文。
        decision_context = await cls._get_decision_context(db, reflection.decision_id)
        dialogues = await ReflectionDao.get_dialogues(db, reflection_id)
        reflection_history = '\n'.join([
            f"{'AI' if d.role == 'assistant' else '学生'}：{d.content[:100]}"
            for d in dialogues[-4:]
        ]) if dialogues else '（无历史对话）'
        retrieved_knowledge = await cls._retrieve_theory_knowledge(db, reflection)

        prompt = REFLECTION_STREAM_PROMPT.format(
            scenario_summary=scenario_summary,
            decision_context=decision_context,
            reflection_history=reflection_history or '（无历史）',
            reflection_text=reflection.content or '（学生尚未输入反思内容）',
            retrieved_knowledge=retrieved_knowledge or '（暂无相关理论参考）',
        )
        logger.info('[反思区] 启动流式生成，reflection_id=%s, decision_id=%s, model_id=%s,promot=%s', reflection_id, reflection.decision_id, model_id, prompt)

        yield json.dumps({'type': 'status', 'message': 'AI 正在结合理论生成指导...'}, ensure_ascii=False) + '\n'

        from module_learning.service.llm_call import AiCall
        full_text = ''
        try:
            async for raw in AiCall.call_llm_stream(db, model_id, prompt):
                try:
                    chunk = json.loads(raw)
                except Exception:
                    continue
                ctype = chunk.get('type')
                if ctype == 'content' and chunk.get('content'):
                    full_text += chunk['content']
                    yield json.dumps({'type': 'content', 'content': chunk['content']}, ensure_ascii=False) + '\n'
                elif ctype == 'error':
                    yield json.dumps({'type': 'error', 'message': chunk.get('error', '生成失败')}, ensure_ascii=False) + '\n'
                    return
        except Exception as e:
            logger.error('[反思区] 流式生成异常: %s', e, exc_info=True)
            yield json.dumps({'type': 'error', 'message': f'生成失败：{e}'}, ensure_ascii=False) + '\n'
            return

        # 流结束后：解析为结构化结果并落库
        json_fence_open = full_text.count('```json')
        fence_total = full_text.count('```')
        logger.info(f'[反思区诊断] 流式LLM输出完成, full_text长度={len(full_text)}, 含```json标记数={json_fence_open}, 含```围栏总数={fence_total} (奇数=有不闭合的fence=被截断)')
        logger.info(f'[反思区诊断] full_text尾部800字(看结尾json块是否完整闭合):\n{full_text[-800:]}')
        result = cls._parse_streamed_guidance(full_text)
        try:
            await cls._persist_guidance(db, reflection, result)
        except Exception as e:
            logger.error('[反思区] 流式结果落库失败: %s', e, exc_info=True)
            yield json.dumps({'type': 'error', 'message': '生成成功但保存失败，请重试'}, ensure_ascii=False) + '\n'
            return

        yield json.dumps({'type': 'result', 'data': result}, ensure_ascii=False) + '\n'

    @classmethod
    def _parse_streamed_guidance(cls, full_text: str) -> dict:
        """
        解析流式输出为结构化结果。
        优先级：① 提取结尾 ```json 代码块 ② 整体 parse_llm_json ③ 兜底（保留文本为 reflection_direction）。
        """
        # ① 优先取最后一个 ```json 代码块（用 ``` 围栏作边界，不可用 \{.*?\}——
        #    非贪婪会停在第一个 } 处，把含嵌套对象的 JSON 截断成非法片段）
        blocks = re.findall(r'```json\s*(.*?)```', full_text, re.DOTALL)
        logger.info(f'[反思区诊断] 步骤①: 正则找到 {len(blocks)} 个 ```json 闭合代码块')
        candidate = blocks[-1].strip() if blocks else full_text
        if blocks:
            logger.info(f'[反思区诊断] 步骤①候选块(取最后一块)前200字:\n{candidate[:200]}')
        try:
            parsed = parse_llm_json(candidate)
            if isinstance(parsed, dict) and parsed:
                tg = parsed.get('theory_guidance') or []
                rd_len = len(parsed.get('reflection_direction') or '')
                logger.info(f'[反思区诊断] 步骤①解析成功 ✓ → theory_guidance数量={len(tg)}, depth_score={parsed.get("depth_score")}, reflection_direction长度={rd_len}')
                return parsed
            logger.warning(f'[反思区诊断] 步骤① parse_llm_json 返回非dict或空: {type(parsed).__name__}')
        except Exception as e:
            logger.warning(f'[反思区诊断] 步骤① parse_llm_json 抛异常: {e}')

        # ② 整体尝试
        try:
            parsed = parse_llm_json(full_text)
            if isinstance(parsed, dict) and parsed:
                logger.info('[反思区诊断] 步骤②(整体)解析成功 ✓')
                return parsed
            logger.warning(f'[反思区诊断] 步骤② parse_llm_json 返回非dict或空: {type(parsed).__name__}')
        except Exception as e:
            logger.warning(f'[反思区诊断] 步骤② parse_llm_json 抛异常: {e}')

        # ③ 兜底：抽取分数，正文作为方向说明，保证不报错
        logger.warning('[反思区诊断] ★★★ 命中兜底分支(③) ★★★ — Bug1/2/3根源! '
                       'theory_guidance=[], reflection_direction=full_text前500字(含Markdown语法)')
        logger.warning(f'[反思区诊断] 兜底原因推测: LLM结尾json块缺失/不闭合/被正文其他```json干扰/含非法字符。full_text前400字:\n{full_text[:400]}')
        score_match = re.search(r'([0-9]*\.?[0-9]+)', full_text)
        score = float(score_match.group(1)) if score_match else 0.3
        if score > 1:
            score = score / 100 if score <= 100 else 0.3
        level = 'reflexive' if score >= 0.71 else ('analytical' if score >= 0.41 else 'descriptive')
        return {
            'depth_score': score,
            'depth_level': level,
            'theory_guidance': [],
            'reflection_direction': full_text.strip()[:500] or '（未生成可读内容）',
            'questions': [],
        }

    @classmethod
    async def _persist_guidance(cls, db: AsyncSession, reflection: EduReflectionData, result: dict):
        """将 AI 理论指导结果落库（对话记录 + 反思数据 + 深度历史）。非流式与流式共用。"""
        old_score = float(reflection.depth_score) if reflection.depth_score else 0.0
        new_score = result.get('depth_score', old_score)

        # 兼容新旧格式：优先用 theory_guidance，降级用 theories
        theory_guidance = result.get('theory_guidance', [])
        theories = result.get('theories', [])

        await ReflectionDao.add_dialogue(db, EduReflectionDialogue(
            reflection_id=reflection.reflection_id,
            role='assistant',
            content=json.dumps(result, ensure_ascii=False),
            question_level=result.get('depth_level', ''),
            depth_score_before=old_score,
            depth_score_after=new_score,
            linked_theories=theory_guidance if theory_guidance else theories,
        ))

        reflection.depth_score = new_score
        reflection.depth_level = result.get('depth_level', reflection.depth_level)
        reflection.linked_theories = theory_guidance if theory_guidance else theories
        reflection.update_time = datetime.now()
        await ReflectionDao.update(db, reflection)

        await ReflectionDao.add_depth_history(db, EduReflectionDepthHistory(
            reflection_id=reflection.reflection_id,
            depth_score=new_score,
            depth_level=result.get('depth_level', ''),
            trigger_type='ai_question',
        ))

    @classmethod
    async def confirm(cls, db: AsyncSession, record_id: int, user_id: int) -> dict:
        """确认反思完成，校验所有决策都有反思内容"""
        # 获取该 record 下所有决策
        decisions = await DecisionDao.get_by_record_id(db, record_id)
        if not decisions:
            raise ValueError('没有决策记录，请先完成决策区')

        # 检查每个决策是否都有反思
        missing = []
        for d in decisions:
            reflection = await ReflectionDao.get_by_decision_id(db, d.decision_id)
            if not reflection or not reflection.content:
                missing.append(d.key_event_desc or f'关键事件{d.key_event_index}')

        if missing:
            raise ValueError(f'以下关键事件尚未反思：{", ".join(missing)}')

        # 标记所有反思为已确认
        for d in decisions:
            reflection = await ReflectionDao.get_by_decision_id(db, d.decision_id)
            if reflection:
                reflection.status = '1'
                reflection.update_time = datetime.now()
                await ReflectionDao.update(db, reflection)

        # 更新学习记录状态
        record = await RecordDao.get_by_id(db, record_id)
        if record:
            record.reflection_status = '2'
            record.update_time = datetime.now()
            await RecordDao.update(db, record)

        return {'record_id': record_id, 'status': 'confirmed'}

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
    async def get_by_decision(cls, db: AsyncSession, decision_id: int) -> dict | None:
        """获取单个决策的反思详情"""
        reflection = await ReflectionDao.get_by_decision_id(db, decision_id)
        if not reflection:
            return None
        return await cls._reflection_to_dict(db, reflection)

    @classmethod
    async def get_list_by_record(cls, db: AsyncSession, record_id: int) -> list:
        """获取 record 下所有反思列表（用于前端 Tabs 展示）"""
        reflections = await ReflectionDao.get_list_by_record_id(db, record_id)
        result = []
        for r in reflections:
            detail = await cls._reflection_to_dict(db, r)
            result.append(detail)
        return result

    @classmethod
    async def _reflection_to_dict(cls, db: AsyncSession, reflection: EduReflectionData) -> dict:
        """将反思记录转为前端响应字典"""
        # 查找关联的关键事件描述
        key_event_desc = ''
        if reflection.decision_id:
            decision = await DecisionDao.get_by_id(db, reflection.decision_id)
            if decision:
                key_event_desc = decision.key_event_desc or ''

        dialogues = await ReflectionDao.get_dialogues(db, reflection.reflection_id)
        return {
            'reflection_id': reflection.reflection_id,
            'record_id': reflection.record_id,
            'decision_id': reflection.decision_id,
            'scenario_id': reflection.scenario_id,
            'student_id': reflection.student_id,
            'key_event_desc': key_event_desc,
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
        """获取情境摘要"""
        scenario = await ScenarioDao.get_by_record_id(db, record_id)
        if not scenario:
            return '（无情境数据）'
        problems = scenario.identified_problems or []
        #todo 这里为什么取前三个呢？全部取出来不行吗？
        titles = [p.get('title', '') for p in problems[:3]] if problems else []
        #todo 这里为什么要取description的前200个字呢？全部取出来不行吗？
        return f"场景：{(scenario.description or '')[:200]}...\n核心问题：{', '.join(titles)}"

    @classmethod
    async def _get_decision_context(cls, db: AsyncSession, decision_id: int) -> str:
        """获取单条决策的完整上下文（替代原 _get_decision_summary 聚合方法）"""
        decision = await DecisionDao.get_by_id(db, decision_id)
        if not decision:
            return '（无决策记录）'

        lines = [
            f"关键事件：{decision.key_event_desc or '（未描述）'}",
            f"是否介入：{'介入' if decision.is_intervened else '未介入'}",
            f"具体行动：{decision.action_taken or '（未描述）'}",
            f"行动理由：{decision.reasoning or '（未描述）'}",
        ]
        if decision.psychological_state:
            lines.append(f"心理状态：{decision.psychological_state}")
        if decision.ethics_analysis:
            # 从 JSONB 中提取摘要
            analysis = decision.ethics_analysis
            if isinstance(analysis, dict):
                analysis_text = analysis.get('analysis', '')
                if analysis_text:
                    lines.append(f"AI伦理分析摘要：{analysis_text[:200]}")
            elif isinstance(analysis, str):
                lines.append(f"AI伦理分析：{analysis[:200]}")

        return '\n'.join(lines)

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
