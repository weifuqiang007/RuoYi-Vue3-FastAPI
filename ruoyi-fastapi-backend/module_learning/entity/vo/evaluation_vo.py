from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class EvaluationSubmitModel(BaseModel):
    """教师提交评价"""
    record_id: int = Field(..., description='学习记录ID')
    scenario_score: Optional[float] = Field(None, description='情境区分数')
    decision_score: Optional[float] = Field(None, description='决策区分数')
    reflection_score: Optional[float] = Field(None, description='反思区分数')
    research_score: Optional[float] = Field(None, description='研究区分数')
    scenario_feedback: Optional[str] = Field(None, description='情境区评语')
    decision_feedback: Optional[str] = Field(None, description='决策区评语')
    reflection_feedback: Optional[str] = Field(None, description='反思区评语')
    research_feedback: Optional[str] = Field(None, description='研究区评语')
    overall_feedback: Optional[str] = Field(None, description='总评语')


class EvaluationVO(BaseModel):
    evaluation_id: int
    record_id: int
    teacher_id: int
    scenario_score: Optional[float] = None
    decision_score: Optional[float] = None
    reflection_score: Optional[float] = None
    research_score: Optional[float] = None
    total_score: Optional[float] = None
    scenario_feedback: Optional[str] = None
    decision_feedback: Optional[str] = None
    reflection_feedback: Optional[str] = None
    research_feedback: Optional[str] = None
    overall_feedback: Optional[str] = None
    is_excellent: Optional[bool] = None
    status: Optional[str] = None
    create_time: Optional[datetime] = None

    model_config = {'from_attributes': True}
