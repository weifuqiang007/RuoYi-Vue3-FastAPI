from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TaskCreateModel(BaseModel):
    """创建任务请求"""
    task_name: str = Field(..., max_length=200, description='任务名称')
    task_description: Optional[str] = Field(None, description='任务描述')
    preset_scenario: Optional[str] = Field(None, description='预设情境')
    scenario_kb_ids: Optional[list[int]] = Field(None, description='情境区知识库ID列表')
    decision_kb_ids: Optional[list[int]] = Field(None, description='决策区知识库ID列表')
    reflection_kb_ids: Optional[list[int]] = Field(None, description='反思区知识库ID列表')
    research_kb_ids: Optional[list[int]] = Field(None, description='研究区知识库ID列表')
    scenario_config: Optional[dict] = Field(None, description='情境区AI配置')
    reflection_config: Optional[dict] = Field(None, description='反思区AI配置')
    deadline: Optional[datetime] = Field(None, description='截止时间')


class TaskUpdateModel(BaseModel):
    """更新任务请求"""
    task_id: int = Field(..., description='任务ID')
    task_name: Optional[str] = Field(None, max_length=200, description='任务名称')
    task_description: Optional[str] = Field(None, description='任务描述')
    preset_scenario: Optional[str] = Field(None, description='预设情境')
    scenario_kb_ids: Optional[list[int]] = Field(None, description='情境区知识库ID列表')
    decision_kb_ids: Optional[list[int]] = Field(None, description='决策区知识库ID列表')
    reflection_kb_ids: Optional[list[int]] = Field(None, description='反思区知识库ID列表')
    research_kb_ids: Optional[list[int]] = Field(None, description='研究区知识库ID列表')
    scenario_config: Optional[dict] = Field(None, description='情境区AI配置')
    reflection_config: Optional[dict] = Field(None, description='反思区AI配置')
    deadline: Optional[datetime] = Field(None, description='截止时间')


class TaskPublishModel(BaseModel):
    """发布任务到班级"""
    dept_ids: list[int] = Field(..., description='班级ID列表')


class TaskVO(BaseModel):
    """任务详情响应"""
    task_id: int
    task_name: str
    task_description: Optional[str] = None
    teacher_id: Optional[int] = None
    creator_type: Optional[str] = '0'
    student_id: Optional[int] = None
    preset_scenario: Optional[str] = None
    scenario_kb_ids: Optional[list] = None
    decision_kb_ids: Optional[list] = None
    reflection_kb_ids: Optional[list] = None
    research_kb_ids: Optional[list] = None
    scenario_config: Optional[dict] = None
    reflection_config: Optional[dict] = None
    deadline: Optional[datetime] = None
    status: Optional[str] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    model_config = {'from_attributes': True}


class StudentTaskCreateModel(BaseModel):
    """学生自建自研课题请求"""
    task_name: str = Field(..., max_length=200, description='课题名称')
    task_description: Optional[str] = Field(None, description='课题描述')
