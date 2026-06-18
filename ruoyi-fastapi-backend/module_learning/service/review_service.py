from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.dao.edu_dao import EduDao
from module_admin.entity.do.dept_do import SysDept
from module_admin.entity.do.edu_do import EduStudentProfile
from module_admin.entity.do.user_do import SysUser
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_learning.dao.decision_dao import DecisionDao
from module_learning.dao.record_dao import RecordDao
from module_learning.dao.reflection_dao import ReflectionDao
from module_learning.dao.research_dao import ResearchDao
from module_learning.dao.review_dao import ReviewDao
from module_learning.dao.scenario_dao import ScenarioDao
from module_learning.dao.task_dao import TaskDao
from module_learning.entity.do.review_do import EduReview, EduReviewDialogue
from module_learning.entity.vo.review_vo import TeacherCommentModel
from utils.log_util import logger
from utils.page_util import PageUtil

# 批阅(裁判)模型的系统默认回落配置项 key（写在 sys_config 表，值必须 ≠ 学生侧 model_id=1）
REVIEW_DEFAULT_MODEL_CONFIG_KEY = 'edu.review.default_model_id'

REVIEW_PROMPT = """你是一位资深的社会工作/教育领域教师，负责批阅学生的「反身性研究」反思成果。
请基于专业知识库理论，对学生的反思研究进行客观、专业的评论。你的评论将作为参考提供给批阅教师，由教师最终点评。

【学生反思研究材料】
{review_context}

【可参考的专业理论/伦理守则】
{retrieved_knowledge}

【评论要求】
1. summary：用1段话概括学生反思研究的整体质量。
2. depth_assessment：评估学生反思达到的深度等级（descriptive描述性/analytical分析性/reflexive反身性）及分数（0.00-1.00），并说明判断依据。
3. strengths：列出2-3条值得肯定之处。
4. weaknesses：列出2-3条需要改进之处。
5. suggestions：给出2-3条具体、可操作的改进方向。
6. theory_reference：结合上述理论，指出学生反思中体现或缺失的理论运用点。
7. conclusion：对学生得出的结论本身给出评论（结论是否成立、依据是否充分），供老师点评参考。

【输出格式】严格只输出如下JSON，不要输出任何其它内容：
{{
  "summary": "...",
  "depth_assessment": {{"depth_level": "analytical", "score": 0.65, "comment": "..."}},
  "strengths": ["...", "..."],
  "weaknesses": ["...", "..."],
  "suggestions": ["...", "..."],
  "theory_reference": [{{"theory_name": "...", "how_applied": "..."}}],
  "conclusion": "..."
}}
"""


class ReviewService:
    """反思批阅服务 —— 教师查看学生反思研究成果、AI(裁判模型)生成评论、教师针对结论点评"""

    # ============================================================
    # 列表
    # ============================================================
    @classmethod
    async def get_records(cls, db: AsyncSession, current_user: CurrentUserModel,
                          filters: dict | None = None, page_num: int = 1, page_size: int = 10) -> dict:
        """教师批阅列表（按所管学生范围过滤，admin 不限）。"""
        student_ids = await cls._managed_student_ids(db, current_user)
        rows_data = await ReviewDao.get_review_list(db, student_ids, filters)
        rows = [cls._review_list_row_to_dict(row) for row in rows_data]
        return PageUtil.get_page_obj(rows, page_num, page_size).model_dump()

    @classmethod
    def _review_list_row_to_dict(cls, row) -> dict:
        record, task, student_name, class_name, review = row[0], row[1], row[2], row[3], row[4]
        return {
            'record_id': record.record_id,
            'task_id': record.task_id,
            'task_name': task.task_name if task else None,
            'creator_type': task.creator_type if task else None,
            'student_id': record.user_id,
            'student_name': student_name,
            'class_name': class_name,
            'current_stage': record.current_stage,
            'status': record.status,
            'submit_time': str(record.submit_time) if record.submit_time else None,
            'reflection_status': record.reflection_status,
            'ai_commented': bool(review and (review.ai_comment_version or 0) > 0),
            'ai_comment_version': review.ai_comment_version if review else 0,
            'review_status': review.review_status if review else None,
            'teacher_comment_brief': (review.teacher_comment[:50] if review and review.teacher_comment else None),
        }

    # ============================================================
    # 详情（聚合四区 + 反思列表 + 批阅数据）
    # ============================================================
    @classmethod
    async def get_detail(cls, db: AsyncSession, record_id: int,
                         current_user: CurrentUserModel) -> dict | None:
        record = await RecordDao.get_by_id(db, record_id)
        if not record:
            return None
        await cls._check_teacher_permission(db, record, current_user)

        task = await TaskDao.get_by_id(db, record.task_id) if record.task_id else None
        student_name, class_name = await cls._get_student_info(db, record.user_id)

        result = {
            'record': {
                'record_id': record.record_id,
                'task_id': record.task_id,
                'task_name': task.task_name if task else None,
                'student_id': record.user_id,
                'student_name': student_name,
                'class_name': class_name,
                'current_stage': record.current_stage,
                'status': record.status,
                'submit_time': str(record.submit_time) if record.submit_time else None,
            },
            'scenario': {},
            'decisions': [],
            'reflections': [],
            'research': {},
            'review': {},
        }

        scenario = await ScenarioDao.get_by_record_id(db, record_id)
        if scenario:
            result['scenario'] = {
                'description': scenario.description,
                'key_events': scenario.key_events,
                'identified_problems': scenario.identified_problems,
            }

        decisions = await DecisionDao.get_by_record_id(db, record_id)
        result['decisions'] = [
            {
                'decision_id': d.decision_id,
                'key_event_desc': d.key_event_desc,
                'action_taken': d.action_taken,
                'reasoning': d.reasoning,
                'ethics_analysis': d.ethics_analysis,
            }
            for d in decisions
        ]

        reflections = await ReflectionDao.get_list_by_record_id(db, record_id)
        result['reflections'] = [
            {
                'reflection_id': r.reflection_id,
                'decision_id': r.decision_id,
                'content': r.content,
                'depth_level': r.depth_level,
                'depth_score': float(r.depth_score) if r.depth_score else 0.0,
                'linked_theories': r.linked_theories,
            }
            for r in reflections
        ]

        research = await ResearchDao.get_by_record_id(db, record_id)
        if research:
            result['research'] = {
                'selected_question': research.selected_question,
                'framework': research.framework,
            }

        review = await ReviewDao.get_by_record_id(db, record_id)
        if review:
            result['review'] = cls._review_to_dict(review)

        return result

    # ============================================================
    # 生成/重新生成 AI 评论（裁判模型）
    # ============================================================
    @classmethod
    async def generate_ai_comment(cls, db: AsyncSession, record_id: int,
                                  scope: str = 'reflection',
                                  current_user: CurrentUserModel | None = None) -> dict:
        """
        生成/重新生成 AI 评论。current_user=None 时跳过权限校验（供后台自动触发使用）。
        裁判模型严格取 task.review_model_id → sys_config 默认回落，禁止用学生侧 model_id=1。
        """
        record = await RecordDao.get_by_id(db, record_id)
        if not record:
            raise ValueError('学习记录不存在')
        if current_user is not None:
            await cls._check_teacher_permission(db, record, current_user)

        task = await TaskDao.get_by_id(db, record.task_id) if record.task_id else None
        review_model_id = await cls._resolve_review_model(db, task)

        context = await cls._build_review_context(db, record, scope)
        knowledge = await cls._retrieve_review_knowledge(db, task, context)
        prompt = REVIEW_PROMPT.format(
            review_context=context,
            retrieved_knowledge=knowledge or '（暂无理论参考）',
        )

        from module_learning.service.llm_call import AiCall
        logger.info('[批阅] 生成AI评论 record_id=%s model_id=%s scope=%s', record_id, review_model_id, scope)
        try:
            ai_comment = await AiCall.call_llm_json(db, review_model_id, prompt)
        except Exception as e:
            logger.exception('[批阅] LLM调用失败 record_id=%s', record_id)
            raise ValueError('AI评论生成失败，请稍后重试')

        ai_comment_text = cls._ai_comment_to_text(ai_comment)
        now = datetime.now()

        review = await ReviewDao.get_by_record_id(db, record_id)
        if not review:
            review = EduReview(
                record_id=record_id,
                task_id=record.task_id,
                student_id=record.user_id,
                ai_comment_version=0,
            )
            review = await ReviewDao.create(db, review)

        review.ai_comment = ai_comment
        review.ai_comment_text = ai_comment_text
        review.ai_comment_version = (review.ai_comment_version or 0) + 1
        review.ai_comment_time = now
        review.ai_comment_scope = scope
        review.review_model_id = review_model_id
        review.update_time = now
        await ReviewDao.update(db, review)

        await ReviewDao.create_dialogue(db, EduReviewDialogue(
            review_id=review.review_id,
            record_id=record_id,
            ai_comment=ai_comment,
            ai_comment_text=ai_comment_text,
            version=review.ai_comment_version,
            scope=scope,
            model_id=review_model_id,
        ))

        return {
            'ai_comment': ai_comment,
            'version': review.ai_comment_version,
            'generate_time': str(now),
            'review_model_id': review_model_id,
        }

    # ============================================================
    # 老师点评
    # ============================================================
    @classmethod
    async def submit_comment(cls, db: AsyncSession, record_id: int, data: TeacherCommentModel,
                             current_user: CurrentUserModel) -> dict:
        record = await RecordDao.get_by_id(db, record_id)
        if not record:
            raise ValueError('学习记录不存在')
        await cls._check_teacher_permission(db, record, current_user)
        if data.submit and not (data.teacher_comment and data.teacher_comment.strip()):
            raise ValueError('提交点评时必须填写针对反思结论的点评')

        review = await ReviewDao.get_by_record_id(db, record_id)
        now = datetime.now()
        if not review:
            review = EduReview(
                record_id=record_id,
                task_id=record.task_id,
                student_id=record.user_id,
                ai_comment_version=0,
            )
            review = await ReviewDao.create(db, review)

        review.teacher_id = current_user.user.user_id
        review.reflection_score = data.reflection_score
        review.teacher_comment = data.teacher_comment
        review.overall_comment = data.overall_comment
        review.ai_comment_feedback = data.ai_comment_feedback
        review.review_status = '1' if data.submit else '0'
        if data.submit:
            review.review_time = now
        review.update_by = current_user.user.user_name or ''
        review.update_time = now
        await ReviewDao.update(db, review)

        # 联动终结性评价表（仅回写反思维度，不计算总分、不改 record 状态）
        await cls._sync_to_evaluation(db, record, review)

        return {'review_id': review.review_id, 'review_status': review.review_status}

    # ============================================================
    # AI 评论历史
    # ============================================================
    @classmethod
    async def get_ai_comment_history(cls, db: AsyncSession, record_id: int,
                                     current_user: CurrentUserModel) -> list:
        record = await RecordDao.get_by_id(db, record_id)
        if not record:
            return []
        await cls._check_teacher_permission(db, record, current_user)
        history = await ReviewDao.get_dialogue_history(db, record_id)
        return [
            {
                'version': h.version,
                'ai_comment': h.ai_comment,
                'ai_comment_text': h.ai_comment_text,
                'scope': h.scope,
                'model_id': h.model_id,
                'generate_time': str(h.create_time) if h.create_time else None,
            }
            for h in history
        ]

    # ============================================================
    # 后台任务：学生提交后自动生成首版 AI 评论
    # ============================================================
    @classmethod
    async def _auto_comment_task(cls, record_id: int):
        """学生提交研究成果(submitted)后自动生成首版AI评论。独立 session，不影响学生提交响应，失败仅记日志。"""
        from config.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            try:
                await cls.generate_ai_comment(db, record_id, scope='reflection', current_user=None)
                await db.commit()
                logger.info('[批阅] 自动生成AI评论成功 record_id=%s', record_id)
            except Exception as e:
                await db.rollback()
                logger.exception('[批阅] 自动生成AI评论失败 record_id=%s', record_id)

    # ============================================================
    # 权限 & 数据范围
    # ============================================================
    @classmethod
    async def _managed_student_ids(cls, db: AsyncSession, current_user: CurrentUserModel) -> list[int] | None:
        """当前教师所管班级学生的 user_id 列表；admin 返回 None（不过滤）。"""
        roles = current_user.roles or []
        if 'admin' in roles:
            return None
        classes = await EduDao.get_teacher_classes(db, current_user.user.user_id)
        class_ids = [c['class_id'] for c in classes]
        if not class_ids:
            return []  # 未绑定任何班级，查不到任何学生记录
        students = await EduDao.get_students_by_class_ids(db, class_ids)
        return [s['user_id'] for s in students]

    @classmethod
    async def _check_teacher_permission(cls, db: AsyncSession, record, current_user: CurrentUserModel):
        """校验当前教师是否有权查看/批阅该 record（须属于所管班级学生）。admin 放行。"""
        roles = current_user.roles or []
        if 'admin' in roles:
            return
        student_ids = await cls._managed_student_ids(db, current_user)
        if record.user_id not in (student_ids or []):
            raise PermissionError('无权查看/批阅该学生记录')

    # ============================================================
    # 裁判模型解析（避免同模型自评）
    # ============================================================
    @classmethod
    async def _resolve_review_model(cls, db: AsyncSession, task) -> int:
        """优先 task.review_model_id → sys_config 默认回落 → 都缺则报错；==1(学生侧) 时告警。"""
        if task and task.review_model_id:
            model_id = int(task.review_model_id)
        else:
            model_id = await cls._get_sys_config_int(db, REVIEW_DEFAULT_MODEL_CONFIG_KEY)
        if not model_id:
            raise ValueError(
                '未配置批阅模型，请联系管理员在任务中设置 review_model_id，'
                f'或在系统参数 {REVIEW_DEFAULT_MODEL_CONFIG_KEY} 中指定一个可用的裁判模型'
            )
        if model_id == 1:
            logger.warning('[批阅] 裁判模型与学生侧相同(model_id=1)，建议检查任务review_model_id或系统参数配置，避免同模型自评')
        return model_id

    @classmethod
    async def _get_sys_config_int(cls, db: AsyncSession, key: str) -> int | None:
        try:
            from module_admin.entity.do.config_do import SysConfig
            result = await db.execute(
                select(SysConfig.config_value).where(SysConfig.config_key == key)
            )
            row = result.first()
            return int(row[0]) if row and row[0] else None
        except Exception as e:
            logger.warning('[批阅] 读取sys_config[%s]失败: %s', key, e)
            return None

    # ============================================================
    # AI 评论上下文构建 & RAG 检索
    # ============================================================
    @classmethod
    async def _build_review_context(cls, db: AsyncSession, record, scope: str) -> str:
        """拼装批阅材料：情境(背景) + 决策(上下文) + 反思(核心) + [full:研究问题]。"""
        lines = []

        scenario = await ScenarioDao.get_by_record_id(db, record.record_id)
        if scenario and scenario.key_events:
            lines.append('【情境关键事件】')
            for i, ke in enumerate(scenario.key_events[:6], 1):
                desc = ke.get('desc') or ke.get('description') or '' if isinstance(ke, dict) else str(ke)
                lines.append(f'  {i}. {desc}')

        decisions = await DecisionDao.get_by_record_id(db, record.record_id)
        if decisions:
            lines.append('【决策摘要】')
            for d in decisions:
                lines.append(
                    f'  - 关键事件「{d.key_event_desc or ""}」：行动「{d.action_taken or ""}」，理由「{d.reasoning or ""}」'
                )

        reflections = await ReflectionDao.get_list_by_record_id(db, record.record_id)
        if reflections:
            lines.append('【学生反思（核心批阅对象）】')
            for idx, r in enumerate(reflections, 1):
                score = float(r.depth_score) if r.depth_score else 0.0
                lines.append(f'  {idx}. {r.content or ""}（AI评估深度：{r.depth_level}，{score}）')

        if scope == 'full':
            research = await ResearchDao.get_by_record_id(db, record.record_id)
            if research:
                lines.append(f'【研究问题】{research.selected_question or ""}')

        return '\n'.join(lines) if lines else '（学生尚未提交反思研究内容）'

    @classmethod
    async def _retrieve_review_knowledge(cls, db: AsyncSession, task, context: str) -> str:
        """用反思材料做 query，从任务反思区知识库检索理论/守则。检索失败降级为空。"""
        try:
            if not task or not task.reflection_kb_ids:
                return ''
            query_text = (context or '')[:500]
            if not query_text.strip():
                return ''
            from module_rag.service.embedding_service import EmbeddingService
            from module_rag.service.retrieval_service import RetrievalService
            query_embedding = await EmbeddingService.embed_single(query_text)
            chunks = await RetrievalService.hybrid_search(
                db=db,
                query_text=query_text,
                query_embedding=query_embedding,
                kb_ids=task.reflection_kb_ids,
                top_k=4,
            )
            return '\n\n'.join([f'【{c["content"][:200]}】' for c in chunks])
        except Exception as e:
            logger.exception('[批阅] RAG检索异常')
            return ''

    # ============================================================
    # 辅助
    # ============================================================
    @classmethod
    def _ai_comment_to_text(cls, ai_comment: dict) -> str:
        if not ai_comment:
            return ''
        parts = []
        if ai_comment.get('summary'):
            parts.append(ai_comment['summary'])
        if ai_comment.get('conclusion'):
            parts.append(ai_comment['conclusion'])
        return ' '.join(parts)[:500]

    @classmethod
    def _review_to_dict(cls, review: EduReview) -> dict:
        return {
            'ai_comment': review.ai_comment,
            'ai_comment_version': review.ai_comment_version,
            'ai_comment_time': str(review.ai_comment_time) if review.ai_comment_time else None,
            'review_model_id': review.review_model_id,
            'teacher_comment': review.teacher_comment,
            'overall_comment': review.overall_comment,
            'reflection_score': float(review.reflection_score) if review.reflection_score else None,
            'ai_comment_feedback': review.ai_comment_feedback,
            'review_status': review.review_status,
            'review_time': str(review.review_time) if review.review_time else None,
            'update_time': str(review.update_time) if review.update_time else None,
        }

    @classmethod
    async def _get_student_info(cls, db: AsyncSession, user_id: int):
        """返回 (student_nick_name, class_name)。"""
        result = await db.execute(
            select(SysUser.nick_name, SysDept.dept_name)
            .select_from(SysUser)
            .outerjoin(EduStudentProfile, SysUser.user_id == EduStudentProfile.user_id)
            .outerjoin(SysDept, EduStudentProfile.class_id == SysDept.dept_id)
            .where(SysUser.user_id == user_id)
        )
        row = result.first()
        return (row[0] if row else None, row[1] if row else None)

    @classmethod
    async def _sync_to_evaluation(cls, db: AsyncSession, record, review: EduReview):
        """将老师点评的反思维度同步到终结性评价表（仅 record 已 submitted 才回写，不创建、不计算总分）。"""
        try:
            if record.status not in ('submitted', 'completed'):
                return
            from module_learning.dao.evaluation_dao import EvaluationDao
            evaluation = await EvaluationDao.get_by_record_id(db, record.record_id)
            if not evaluation:
                return
            if review.reflection_score is not None:
                evaluation.reflection_score = review.reflection_score
            if review.teacher_comment:
                evaluation.reflection_feedback = review.teacher_comment
            evaluation.update_time = datetime.now()
            await EvaluationDao.update(db, evaluation)
        except Exception as e:
            logger.warning('[批阅] 同步edu_evaluation失败 record_id=%s: %s', record.record_id, e)
