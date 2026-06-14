from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReflectionSaveModel(BaseModel):
    """保存反思文本"""
    decision_id: int = Field(..., description='关联的决策记录ID，每个决策对应一条独立反思')
    content: str = Field(..., description='反思文本内容')


class ReflectionQuestionModel(BaseModel):
    """AI生成提问请求"""
    reflection_id: int = Field(..., description='反思ID')


class ReflectionVO(BaseModel):
    """反思区数据响应模型"""
    reflection_id: int = Field(..., description='反思区数据主键ID')
    record_id: int = Field(..., description='关联的学习记录ID')
    decision_id: Optional[int] = Field(None, description='关联的决策记录ID')
    scenario_id: int = Field(..., description='关联的情境区数据ID')
    student_id: int = Field(..., description='学生用户ID')
    key_event_desc: Optional[str] = Field(None, description='对应的关键事件描述')
    content: Optional[str] = Field(None, description='学生撰写的反思文本内容')
    depth_level: Optional[str] = Field(None, description='AI评估的反思深度等级（descriptive/analytical/reflexive）')
    depth_score: Optional[float] = Field(None, description='AI评估的反思深度分数（0.00-1.00）')
    linked_theories: Optional[list] = Field(None, description='AI关联的专业理论列表')
    version: Optional[int] = Field(None, description='编辑版本号')
    status: Optional[str] = Field(None, description='反思区状态（0草稿 1已确认）')
    dialogues: Optional[list] = Field([], description='AI对话记录列表')
    create_time: Optional[datetime] = Field(None, description='创建时间')
    update_time: Optional[datetime] = Field(None, description='最后更新时间')

    model_config = {'from_attributes': True}
