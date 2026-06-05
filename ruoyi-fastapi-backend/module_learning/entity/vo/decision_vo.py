from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DecisionSaveModel(BaseModel):
    """保存决策记录"""
    record_id: int = Field(..., description='学习记录ID')
    scenario_id: int = Field(..., description='情境ID')
    key_event_index: Optional[int] = Field(None, description='关键事件索引')
    key_event_desc: Optional[str] = Field(None, description='关键事件描述')
    is_intervened: Optional[bool] = Field(None, description='是否介入')
    action_taken: Optional[str] = Field(None, description='具体行动')
    reasoning: Optional[str] = Field(None, description='行动理由')
    psychological_state: Optional[str] = Field(None, description='心理活动')
    alternatives: Optional[str] = Field(None, description='替代方案')
    expected_outcome: Optional[str] = Field(None, description='预期结果')
    actual_outcome: Optional[str] = Field(None, description='实际结果')


class DecisionEthicsModel(BaseModel):
    """AI伦理分析请求"""
    decision_id: int = Field(..., description='决策ID')


class DecisionVO(BaseModel):
    decision_id: int
    record_id: int
    scenario_id: int
    student_id: int
    key_event_index: Optional[int] = None
    key_event_desc: Optional[str] = None
    is_intervened: Optional[bool] = None
    action_taken: Optional[str] = None
    reasoning: Optional[str] = None
    psychological_state: Optional[str] = None
    alternatives: Optional[str] = None
    expected_outcome: Optional[str] = None
    actual_outcome: Optional[str] = None
    ethics_analysis: Optional[dict] = None
    status: Optional[str] = None
    dialogues: Optional[list] = []
    create_time: Optional[datetime] = None

    model_config = {'from_attributes': True}
