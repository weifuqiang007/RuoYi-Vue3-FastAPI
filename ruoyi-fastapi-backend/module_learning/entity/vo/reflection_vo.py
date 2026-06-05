from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReflectionSaveModel(BaseModel):
    """保存反思文本"""
    record_id: int = Field(..., description='学习记录ID')
    content: str = Field(..., description='反思文本内容')


class ReflectionQuestionModel(BaseModel):
    """AI生成提问请求"""
    reflection_id: int = Field(..., description='反思ID')


class ReflectionVO(BaseModel):
    reflection_id: int
    record_id: int
    scenario_id: int
    student_id: int
    content: Optional[str] = None
    depth_level: Optional[str] = None
    depth_score: Optional[float] = None
    linked_theories: Optional[list] = None
    version: Optional[int] = None
    status: Optional[str] = None
    dialogues: Optional[list] = []
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    model_config = {'from_attributes': True}
