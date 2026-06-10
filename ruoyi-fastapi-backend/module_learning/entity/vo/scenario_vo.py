from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ScenarioSaveModel(BaseModel):
    """保存情境描述"""
    record_id: int = Field(..., description='学习记录ID')
    description: Optional[str] = Field(None, description='场景描述')
    key_events: Optional[list] = Field(None, description='关键事件节点')
    identified_problems: Optional[list] = Field(None, description='AI识别的问题')
    category_tags: Optional[list] = Field(None, description='场景分类标签')


class ScenarioAnalyzeModel(BaseModel):
    """AI分析请求"""
    scenario_id: int = Field(..., description='情境ID')


class ScenarioFollowupModel(BaseModel):
    """AI追问请求"""
    scenario_id: int = Field(..., description='情境ID')
    user_message: Optional[str] = Field(None, description='用户回复')


class ScenarioVO(BaseModel):
    scenario_id: int
    record_id: int
    user_id: int
    description: Optional[str] = None
    key_events: Optional[list] = None
    identified_problems: Optional[list] = None
    category_tags: Optional[list] = None
    status: Optional[str] = None
    dialogues: Optional[list] = []
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    model_config = {'from_attributes': True}
