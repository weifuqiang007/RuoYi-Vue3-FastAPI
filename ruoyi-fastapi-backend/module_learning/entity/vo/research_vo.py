from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ResearchQuestionModel(BaseModel):
    """AI生成研究问题"""
    research_id: int = Field(..., description='研究ID')


class ResearchFrameworkModel(BaseModel):
    """AI生成论文框架"""
    research_id: int = Field(..., description='研究ID')
    selected_question: str = Field(..., description='选定的研究问题')


class ResearchSaveModel(BaseModel):
    """保存研究区整体数据"""
    research_id: int = Field(..., description='研究ID')
    selected_question: Optional[str] = Field(None, description='选定的研究问题')
    material_summary: Optional[str] = Field(None, description='材料汇总')
    chapters: Optional[list] = Field(None, description='章节内容列表，每项含chapter_index和content')


class ResearchChapterSaveModel(BaseModel):
    """保存章节"""
    research_id: int = Field(..., description='研究ID')
    chapter_index: int = Field(..., description='章节序号')
    content: Optional[str] = Field(None, description='章节内容')


class ResearchChapterDraftModel(BaseModel):
    """AI辅助撰写章节"""
    research_id: int = Field(..., description='研究ID')
    chapter_index: int = Field(..., description='章节序号')


class ResearchVO(BaseModel):
    research_id: int
    record_id: int
    student_id: int
    material_summary: Optional[str] = None
    candidate_questions: Optional[list] = None
    selected_question: Optional[str] = None
    framework: Optional[list] = None
    ref_literature: Optional[list] = None
    status: Optional[str] = None
    chapters: Optional[list] = []
    create_time: Optional[datetime] = None

    model_config = {'from_attributes': True}
