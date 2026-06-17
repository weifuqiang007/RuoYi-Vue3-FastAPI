from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ReviewListQueryModel(BaseModel):
    """教师批阅列表查询条件"""
    class_id: Optional[int] = Field(None, description='班级ID（精确匹配，复用sys_dept.dept_id）')
    task_id: Optional[int] = Field(None, description='任务/课题ID（精确匹配）')
    creator_type: Optional[str] = Field(None, description="课题类型筛选：'0'教学任务 / '1'自研课题（精确匹配）")
    student_name: Optional[str] = Field(None, description='学生姓名（模糊匹配）')
    review_status: Optional[str] = Field(None, description="批阅状态筛选：'pending'待批阅 / 'commented'已点评 / 'no_ai'未生成AI评论")
    submit_time_begin: Optional[str] = Field(None, description='提交时间起始，如 2026-06-01 00:00:00')
    submit_time_end: Optional[str] = Field(None, description='提交时间结束，如 2026-06-30 23:59:59')
    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class TeacherCommentModel(BaseModel):
    """老师提交/更新点评"""
    reflection_score: Optional[float] = Field(None, description='老师对反思维度的评分（0-100）')
    teacher_comment: Optional[str] = Field(None, description='老师针对学生反思结论的点评文字（submit=true时必填）')
    overall_comment: Optional[str] = Field(None, description='老师总评')
    ai_comment_feedback: Optional[str] = Field(None, description='老师对AI评论的看法（认同/补充/纠正）')
    submit: bool = Field(True, description='true=提交(review_status=1) false=保存草稿(review_status=0)')


class AiCommentScopeModel(BaseModel):
    """生成/重新生成AI评论"""
    scope: Literal['reflection', 'full'] = Field('reflection', description='评论范围：reflection仅反思 / full含四区')


class ReviewVO(BaseModel):
    """批阅数据响应"""
    review_id: Optional[int] = Field(None, description='批阅记录主键ID')
    record_id: int = Field(..., description='关联的学习记录ID')
    ai_comment: Optional[dict] = Field(None, description='AI评论结构化结果')
    ai_comment_version: Optional[int] = Field(None, description='AI评论版本号')
    ai_comment_time: Optional[datetime] = Field(None, description='最近一次AI评论生成时间')
    review_model_id: Optional[int] = Field(None, description='本次AI评论所用裁判模型ID')
    teacher_comment: Optional[str] = Field(None, description='老师针对反思结论的点评')
    overall_comment: Optional[str] = Field(None, description='老师总评')
    reflection_score: Optional[float] = Field(None, description='反思维度评分')
    ai_comment_feedback: Optional[str] = Field(None, description='老师对AI评论的看法')
    review_status: Optional[str] = Field(None, description='批阅状态（0草稿 1已提交）')
    review_time: Optional[datetime] = Field(None, description='老师点评提交时间')
    update_time: Optional[datetime] = Field(None, description='最后更新时间')

    model_config = {'from_attributes': True}
