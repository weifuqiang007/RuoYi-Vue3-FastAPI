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


class RecordVO(BaseModel):
    record_id: int
    task_id: Optional[int] = None
    user_id: int
    current_stage: Optional[str] = None
    scenario_status: Optional[str] = None
    decision_status: Optional[str] = None
    reflection_status: Optional[str] = None
    research_status: Optional[str] = None
    scenario_id: Optional[int] = None
    decision_id: Optional[int] = None
    reflection_id: Optional[int] = None
    research_id: Optional[int] = None
    status: Optional[str] = None
    score: Optional[float] = None
    teacher_feedback: Optional[str] = None
    start_time: Optional[datetime] = None
    submit_time: Optional[datetime] = None
    complete_time: Optional[datetime] = None
    create_time: Optional[datetime] = None

    model_config = {'from_attributes': True}
