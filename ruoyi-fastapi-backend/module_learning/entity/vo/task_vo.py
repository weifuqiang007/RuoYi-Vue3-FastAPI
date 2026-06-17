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
    review_model_id: Optional[int] = Field(None, description='批阅(裁判)AI模型ID，关联ai_model.model_id；为空时回落系统默认批阅模型，必须与学生侧模型不同')
    deadline: Optional[datetime] = Field(None, description='截止时间')
    dept_ids: Optional[list[int]] = Field(None, description='分配的班级ID列表')


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
    review_model_id: Optional[int] = Field(None, description='批阅(裁判)AI模型ID，关联ai_model.model_id；为空时回落系统默认批阅模型，必须与学生侧模型不同')
    deadline: Optional[datetime] = Field(None, description='截止时间')
    dept_ids: Optional[list[int]] = Field(None, description='分配的班级ID列表，传此字段则覆盖原有分配')


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
    review_model_id: Optional[int] = None
    deadline: Optional[datetime] = None
    status: Optional[str] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    model_config = {'from_attributes': True}


class StudentTaskCreateModel(BaseModel):
    """学生自建自研课题请求"""
    task_name: str = Field(..., max_length=200, description='课题名称')
    task_description: Optional[str] = Field(None, description='课题描述')
    scenario_kb_ids: Optional[list[int]] = Field(None, description='情境区知识库ID列表，不传则默认使用公用知识库[5]')
    decision_kb_ids: Optional[list[int]] = Field(None, description='决策区知识库ID列表，不传则默认使用公用知识库[5]')
    reflection_kb_ids: Optional[list[int]] = Field(None, description='反思区知识库ID列表，不传则默认使用公用知识库[5]')
    research_kb_ids: Optional[list[int]] = Field(None, description='研究区知识库ID列表，不传则默认使用公用知识库[5]')
    review_model_id: Optional[int] = Field(None, description='批阅(裁判)AI模型ID，关联ai_model.model_id；为空时回落系统默认批阅模型，必须与学生侧模型不同')


class TaskListQueryModel(BaseModel):
    """任务列表查询条件"""
    creator_type: Optional[str] = Field(None, description="任务类型：'0'教学任务 / '1'自研课题")
    task_name: Optional[str] = Field(None, description='任务名称（模糊匹配）')
    dept_id: Optional[int] = Field(None, description='归属班级ID')
    teacher_name: Optional[str] = Field(None, description='发布教师姓名（模糊匹配）')
    task_description: Optional[str] = Field(None, description='任务简述（模糊匹配）')
    deadline_begin: Optional[str] = Field(None, description='截止时间起始')
    deadline_end: Optional[str] = Field(None, description='截止时间结束')
    create_time_begin: Optional[str] = Field(None, description='创建时间起始')
    create_time_end: Optional[str] = Field(None, description='创建时间结束')
    status: Optional[str] = Field(None, description='发布状态')
    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
