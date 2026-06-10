import re
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from module_learning.dao.evaluation_dao import EvaluationDao
from module_learning.dao.record_dao import RecordDao
from module_learning.dao.scenario_dao import ScenarioDao
from module_learning.dao.decision_dao import DecisionDao
from module_learning.dao.reflection_dao import ReflectionDao
from module_learning.dao.research_dao import ResearchDao
from module_learning.entity.do.evaluation_do import EduEvaluation, EduExcellentCase
from module_learning.entity.vo.evaluation_vo import EvaluationSubmitModel


class MonitorService:

    @classmethod
    async def get_class_overview(cls, db: AsyncSession, task_id: int) -> dict:
        """班级进度概览"""
        records = await RecordDao.get_by_task_id(db, task_id)
        total = len(records)

        stage_counts = {'scenario': 0, 'decision': 0, 'reflection': 0, 'research': 0, 'submitted': 0, 'completed': 0}
        students = []

        for r in records:
            stage_counts[r.current_stage] = stage_counts.get(r.current_stage, 0) + 1
            students.append({
                'record_id': r.record_id,
                'user_id': r.user_id,
                'current_stage': r.current_stage,
                'scenario_status': r.scenario_status,
                'decision_status': r.decision_status,
                'reflection_status': r.reflection_status,
                'research_status': r.research_status,
                'status': r.status,
                'submit_time': str(r.submit_time) if r.submit_time else None,
            })

        return {
            'task_id': task_id,
            'total_students': total,
            'stage_distribution': stage_counts,
            'students': students,
        }

    @classmethod
    async def get_student_detail(cls, db: AsyncSession, record_id: int) -> dict:
        """学生完整学习过程详情"""
        record = await RecordDao.get_by_id(db, record_id)
        if not record:
            return {}

        result = {
            'record_id': record.record_id,
            'task_id': record.task_id,
            'user_id': record.user_id,
            'current_stage': record.current_stage,
            'status': record.status,
            'score': float(record.score) if record.score else None,
            'teacher_feedback': record.teacher_feedback,
        }

        # 情境区数据
        scenario = await ScenarioDao.get_by_record_id(db, record_id)
        if scenario:
            result['scenario'] = {
                'description': scenario.description,
                'key_events': scenario.key_events,
                'identified_problems': scenario.identified_problems,
            }

        # 决策区数据
        decisions = await DecisionDao.get_by_record_id(db, record_id)
        result['decisions'] = [
            {
                'key_event_desc': d.key_event_desc,
                'is_intervened': d.is_intervened,
                'action_taken': d.action_taken,
                'reasoning': d.reasoning,
                'ethics_analysis': d.ethics_analysis,
            }
            for d in decisions
        ]

        # 反思区数据
        reflection = await ReflectionDao.get_by_record_id(db, record_id)
        if reflection:
            result['reflection'] = {
                'content': reflection.content,
                'depth_level': reflection.depth_level,
                'depth_score': float(reflection.depth_score) if reflection.depth_score else 0.0,
                'linked_theories': reflection.linked_theories,
            }

        # 研究区数据
        research = await ResearchDao.get_by_record_id(db, record_id)
        if research:
            result['research'] = {
                'selected_question': research.selected_question,
                'framework': research.framework,
            }

        # 评价数据
        evaluation = await EvaluationDao.get_by_record_id(db, record_id)
        if evaluation:
            result['evaluation'] = {
                'total_score': float(evaluation.total_score) if evaluation.total_score else None,
                'overall_feedback': evaluation.overall_feedback,
                'is_excellent': evaluation.is_excellent,
            }

        return result


class EvaluationService:

    @classmethod
    async def submit(cls, db: AsyncSession, data: EvaluationSubmitModel, teacher_id: int) -> dict:
        """教师提交评价"""
        record = await RecordDao.get_by_id(db, data.record_id)
        if not record:
            raise ValueError('学习记录不存在')
        if record.status not in ('submitted', 'completed'):
            raise ValueError('学生尚未提交，无法评价')

        # 计算加权总分
        total = (
            (data.scenario_score or 0) * 0.2
            + (data.decision_score or 0) * 0.2
            + (data.reflection_score or 0) * 0.3
            + (data.research_score or 0) * 0.3
        )

        # 查找或创建评价
        evaluation = await EvaluationDao.get_by_record_id(db, data.record_id)
        if not evaluation:
            evaluation = EduEvaluation(
                record_id=data.record_id,
                teacher_id=teacher_id,
            )
            evaluation = await EvaluationDao.create(db, evaluation)

        evaluation.scenario_score = data.scenario_score
        evaluation.decision_score = data.decision_score
        evaluation.reflection_score = data.reflection_score
        evaluation.research_score = data.research_score
        evaluation.total_score = total
        evaluation.scenario_feedback = data.scenario_feedback
        evaluation.decision_feedback = data.decision_feedback
        evaluation.reflection_feedback = data.reflection_feedback
        evaluation.research_feedback = data.research_feedback
        evaluation.overall_feedback = data.overall_feedback
        evaluation.status = '1'
        evaluation.update_time = datetime.now()
        await EvaluationDao.update(db, evaluation)

        # 更新学习记录
        record.status = 'completed'
        record.score = total
        record.teacher_feedback = data.overall_feedback
        record.complete_time = datetime.now()
        record.update_time = datetime.now()
        await RecordDao.update(db, record)

        return {'evaluation_id': evaluation.evaluation_id, 'total_score': total}

    @classmethod
    async def get_detail(cls, db: AsyncSession, record_id: int) -> dict | None:
        """查看评价"""
        evaluation = await EvaluationDao.get_by_record_id(db, record_id)
        if not evaluation:
            return None
        return {
            'evaluation_id': evaluation.evaluation_id,
            'record_id': evaluation.record_id,
            'teacher_id': evaluation.teacher_id,
            'scenario_score': float(evaluation.scenario_score) if evaluation.scenario_score else None,
            'decision_score': float(evaluation.decision_score) if evaluation.decision_score else None,
            'reflection_score': float(evaluation.reflection_score) if evaluation.reflection_score else None,
            'research_score': float(evaluation.research_score) if evaluation.research_score else None,
            'total_score': float(evaluation.total_score) if evaluation.total_score else None,
            'scenario_feedback': evaluation.scenario_feedback,
            'decision_feedback': evaluation.decision_feedback,
            'reflection_feedback': evaluation.reflection_feedback,
            'research_feedback': evaluation.research_feedback,
            'overall_feedback': evaluation.overall_feedback,
            'is_excellent': evaluation.is_excellent,
            'create_time': str(evaluation.create_time) if evaluation.create_time else None,
        }

    @classmethod
    async def mark_excellent(cls, db: AsyncSession, record_id: int, teacher_id: int) -> dict:
        """标记为优秀案例"""
        record = await RecordDao.get_by_id(db, record_id)
        if not record:
            raise ValueError('学习记录不存在')

        # 获取完整数据
        scenario = await ScenarioDao.get_by_record_id(db, record_id)
        decisions = await DecisionDao.get_by_record_id(db, record_id)
        reflection = await ReflectionDao.get_by_record_id(db, record_id)
        research = await ResearchDao.get_by_record_id(db, record_id)

        # 匿名化处理
        def anonymize(text: str) -> str:
            if not text:
                return ''
            return re.sub(r'[一-鿿]{1}[大爷叔阿姨哥姐]', lambda m: 'X' + m.group(0)[1:], text)

        case = EduExcellentCase(
            source_record_id=record_id,
            task_id=record.task_id or 0,
            scenario_desc=anonymize(scenario.description if scenario else ''),
            reflection_data=anonymize(reflection.content if reflection else ''),
            research_data=anonymize(research.selected_question if research else ''),
            tags=scenario.category_tags if scenario else [],
        )
        case = await EvaluationDao.create_case(db, case)

        # 标记评价
        evaluation = await EvaluationDao.get_by_record_id(db, record_id)
        if evaluation:
            evaluation.is_excellent = True
            evaluation.update_time = datetime.now()
            await EvaluationDao.update(db, evaluation)

        return {'case_id': case.case_id}

    @classmethod
    async def get_cases(cls, db: AsyncSession) -> list:
        """获取优秀案例列表"""
        cases = await EvaluationDao.get_excellent_cases(db)
        return [
            {
                'case_id': c.case_id,
                'task_id': c.task_id,
                'scenario_desc': c.scenario_desc[:200] if c.scenario_desc else '',
                'tags': c.tags,
                'teacher_comment': c.teacher_comment,
                'create_time': str(c.create_time) if c.create_time else None,
            }
            for c in cases
        ]

    @classmethod
    async def get_case_detail(cls, db: AsyncSession, case_id: int) -> dict | None:
        case = await EvaluationDao.get_case_by_id(db, case_id)
        if not case:
            return None
        return {
            'case_id': case.case_id,
            'task_id': case.task_id,
            'scenario_desc': case.scenario_desc,
            'decision_data': case.decision_data,
            'reflection_data': case.reflection_data,
            'research_data': case.research_data,
            'teacher_comment': case.teacher_comment,
            'tags': case.tags,
        }
