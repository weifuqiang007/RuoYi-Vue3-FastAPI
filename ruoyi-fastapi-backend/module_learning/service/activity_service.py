import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from module_learning.dao.edu_dao import EduDao
from module_learning.role_constants import LearningRoles
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_learning.dao.activity_dao import ActivityDao
from module_learning.dao.task_dao import TaskDao

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# 动作 → 中文文案
_ACTION_LABELS = {
    'publish': '发布了任务',
    'ongoing': '正在处理',
    'submit': '已提交',
    'review': '做了点评',
}

# 角色 → 跳转的任务列表页：已集中到 LearningRoles.ROLE_REDIRECT（见 role_constants.py）


def _humanize_time(dt: datetime, now: datetime) -> str:
    """datetime → 相对时间文案：刚刚 / N分钟前 / N小时前 / N天前 / 具体日期"""
    if not dt:
        return ''
    seconds = int((now - dt).total_seconds())
    if seconds < 60:
        return '刚刚'
    if seconds < 3600:
        return f'{seconds // 60}分钟前'
    if seconds < 86400:
        return f'{seconds // 3600}小时前'
    if seconds < 86400 * 7:
        return f'{seconds // 86400}天前'
    return dt.strftime('%Y-%m-%d')


class ActivityService:
    """
    首页动态墙：聚合「发布/处理中/已提交/点评」四类最近操作 + 用户名片 + 任务访问权限校验。
    """

    CACHE_KEY_PREFIX = 'edu:activity:recent'
    CACHE_TTL = 30  # 秒

    @classmethod
    async def get_recent_activities(
        cls, db: AsyncSession, request: Request, limit: int = 20
    ) -> list[dict]:
        cache_key = f'{cls.CACHE_KEY_PREFIX}:{limit}'
        redis = getattr(request.app.state, 'redis', None)

        # 1. 先读缓存
        if redis is not None:
            try:
                cached = await redis.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                logger.warning('动态墙缓存读取失败: %s', e)

        # 2. 聚合4类（同一 AsyncSession 不能并发执行查询，保持串行）
        published = await ActivityDao.get_recent_published(db, limit)
        ongoing = await ActivityDao.get_recent_ongoing(db, limit)
        submitted = await ActivityDao.get_recent_submitted(db, limit)
        reviewed = await ActivityDao.get_recent_reviewed(db, limit)
        raw = published + ongoing + submitted + reviewed

        # 3. 按原始 datetime 倒序排序后截取，再格式化
        raw = [m for m in raw if m.get('occurred_at')]
        raw.sort(key=lambda x: x['occurred_at'], reverse=True)
        top = raw[:limit]

        now = datetime.now()
        items = [
            {
                'actor_id': m.get('actor_id'),
                'actor_name': m['actor_name'],
                'actor_role': m.get('actor_role', ''),
                'task_id': m.get('task_id'),
                'task_name': m['task_name'],
                'record_id': m.get('record_id'),
                'action': m['action'],
                'action_label': _ACTION_LABELS.get(m['action'], ''),
                'occurred_at': m['occurred_at'].strftime('%Y-%m-%d %H:%M:%S'),
                'occurred_at_ts': int(m['occurred_at'].timestamp()),
                'occurred_at_label': _humanize_time(m['occurred_at'], now),
            }
            for m in top
        ]

        # 4. 写缓存（失败不阻塞）
        if redis is not None:
            try:
                await redis.set(cache_key, json.dumps(items, ensure_ascii=False), ex=cls.CACHE_TTL)
            except Exception as e:
                logger.warning('动态墙缓存写入失败: %s', e)

        return items

    @classmethod
    async def get_user_card(cls, db: AsyncSession, user_id: int) -> dict | None:
        """用户名片（姓名/角色/班级或职称/注册时间）"""
        return await ActivityDao.get_user_card(db, user_id)

    @classmethod
    async def check_task_access(
        cls, db: AsyncSession, current_user: CurrentUserModel, task_id: int
    ) -> dict:
        """
        校验当前用户能否访问指定任务（数据权限），并返回按角色应跳转的任务列表页。
        - admin：全部可访问 → /learning/task-manage
        - teacher：自己创建 或 分配给所管班级 → /learning/task-manage
        - student：自研课题本人 或 分配给自己班级 → /learning/my-tasks
        """
        task = await TaskDao.get_by_id(db, task_id)
        if not task:
            return {'can_access': False, 'redirect_path': '', 'reason': '任务不存在或已删除'}

        roles = current_user.roles or []
        user_id = current_user.user.user_id

        if LearningRoles.is_admin(roles):
            return {'can_access': True, 'redirect_path': LearningRoles.redirect_for(LearningRoles.ADMIN), 'reason': ''}

        # 任务被分配到的班级集合（dept_id）
        assigned = await TaskDao.get_assigned_classes(db, task_id)
        assigned_dept_ids = {c.get('dept_id') for c in assigned if c.get('dept_id')}

        if LearningRoles.is_teacher(roles):
            if task.teacher_id == user_id:
                return {'can_access': True, 'redirect_path': LearningRoles.redirect_for(LearningRoles.TEACHER), 'reason': ''}
            classes = await EduDao.get_teacher_classes(db, user_id)
            teacher_class_ids = {c.get('class_id') for c in (classes or []) if c.get('class_id')}
            if teacher_class_ids & assigned_dept_ids:
                return {'can_access': True, 'redirect_path': LearningRoles.redirect_for(LearningRoles.TEACHER), 'reason': ''}
            return {'can_access': False, 'redirect_path': '', 'reason': '该任务不在您管理的班级范围内'}

        if LearningRoles.is_student(roles):
            # 自研课题本人
            if str(task.creator_type) == '1' and task.student_id == user_id:
                return {'can_access': True, 'redirect_path': LearningRoles.redirect_for(LearningRoles.STUDENT), 'reason': ''}
            profile = await EduDao.get_student_profile_by_user_id(db, user_id)
            if profile and profile.class_id and profile.class_id in assigned_dept_ids:
                return {'can_access': True, 'redirect_path': LearningRoles.redirect_for(LearningRoles.STUDENT), 'reason': ''}
            return {'can_access': False, 'redirect_path': '', 'reason': '该任务未分配给您所在的班级'}

        return {'can_access': False, 'redirect_path': '', 'reason': '当前角色无权访问该任务'}
