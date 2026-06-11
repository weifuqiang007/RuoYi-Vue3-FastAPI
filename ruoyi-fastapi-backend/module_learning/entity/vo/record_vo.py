from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RecordStartModel(BaseModel):
    """开始任务"""
    pass


class RecordSelfStudyModel(BaseModel):
    """创建自研课题"""
    pass


class RecordAdvanceModel(BaseModel):
    """推进到下一区"""
    pass


class RecordListQueryModel(BaseModel):
    """学习记录列表查询条件"""
    creator_type: Optional[str] = Field(None, description="创建者类型筛选：'0'教师创建 / '1'学生自建")
    task_name: Optional[str] = Field(None, description='课题名称（模糊匹配）')
    create_time_begin: Optional[str] = Field(None, description='创建时间起始，如 2026-06-01')
    create_time_end: Optional[str] = Field(None, description='创建时间结束，如 2026-06-30')
    deadline_begin: Optional[str] = Field(None, description='截止时间起始')
    deadline_end: Optional[str] = Field(None, description='截止时间结束')
    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class RecordVO(BaseModel):
    """学习记录详情响应"""
    record_id: int = Field(..., description='学习记录主键ID')
    task_id: Optional[int] = Field(None, description='关联的教学任务ID，关联edu_task.task_id')
    task_name: Optional[str] = Field(None, description='课题/任务名称，来自edu_task.task_name')
    creator_type: Optional[str] = Field(None, description="创建者类型：'0'教师创建 / '1'学生自建")
    creator_name: Optional[str] = Field(None, description='创建者姓名（教师或学生昵称），根据creator_type取teacher_name或student_name')
    deadline: Optional[str] = Field(None, description='任务截止时间，来自edu_task.deadline')
    user_id: int = Field(..., description='记录所属用户ID（支持student/teacher/admin），关联sys_user.user_id')
    current_stage: Optional[str] = Field(None, description='当前所在阶段（scenario/decision/reflection/research/submitted/completed）')
    scenario_status: Optional[str] = Field(None, description='情境区完成状态（0未开始 1进行中 2已完成）')
    decision_status: Optional[str] = Field(None, description='决策区完成状态（0未开始 1进行中 2已完成）')
    reflection_status: Optional[str] = Field(None, description='反思区完成状态（0未开始 1进行中 2已完成）')
    research_status: Optional[str] = Field(None, description='研究生成区完成状态（0未开始 1进行中 2已完成）')
    scenario_id: Optional[int] = Field(None, description='关联的情境区数据ID，关联edu_scenario_data.scenario_id')
    decision_id: Optional[int] = Field(None, description='关联的决策区数据ID，关联edu_decision_data.decision_id')
    reflection_id: Optional[int] = Field(None, description='关联的反思区数据ID，关联edu_reflection_data.reflection_id')
    research_id: Optional[int] = Field(None, description='关联的研究区数据ID，关联edu_research_data.research_id')
    status: Optional[str] = Field(None, description='整体状态（ongoing进行中/submitted已提交/completed已完成）')
    score: Optional[float] = Field(None, description='教师评分，加权总分')
    teacher_feedback: Optional[str] = Field(None, description='教师总评语')
    start_time: Optional[datetime] = Field(None, description='用户开始任务的时间')
    submit_time: Optional[datetime] = Field(None, description='用户提交研究成果的时间')
    complete_time: Optional[datetime] = Field(None, description='教师评分完成、记录关闭的时间')
    create_time: Optional[datetime] = Field(None, description='记录创建时间')

    model_config = {'from_attributes': True}
