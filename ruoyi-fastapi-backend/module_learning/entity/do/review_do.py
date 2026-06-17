from datetime import datetime

from sqlalchemy import CHAR, BigInteger, Column, DateTime, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from config.database import Base


class EduReview(Base):
    """反思批阅主表 —— 存储批阅(裁判)模型对学生反思研究的AI评论，以及老师针对学生结论的点评（过程性，与终结性评价 edu_evaluation 解耦）"""
    __tablename__ = 'edu_review'
    __table_args__ = {'comment': '反思批阅主表（AI评论+老师点评，过程性）'}

    review_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='批阅记录主键ID')
    record_id = Column(BigInteger, nullable=False, comment='关联的学习记录ID，关联edu_learning_record.record_id，唯一')
    task_id = Column(BigInteger, comment='冗余字段，关联的教学任务ID，关联edu_task.task_id，方便按任务筛选')
    student_id = Column(BigInteger, nullable=False, comment='冗余字段，学生用户ID（=edu_learning_record.user_id），方便按学生筛选')
    # AI 评论（由裁判模型生成）
    ai_comment = Column(JSONB, comment='AI评论结构化结果，JSON对象，含summary/depth_assessment/strengths/weaknesses/suggestions/theory_reference/conclusion')
    ai_comment_text = Column(Text, comment='AI评论纯文本摘要（summary+conclusion），列表展示用')
    ai_comment_version = Column(Integer, server_default='0', comment='AI评论版本号，每重新生成一次+1')
    ai_comment_time = Column(DateTime, comment='最近一次AI评论生成时间')
    ai_comment_scope = Column(String(20), server_default='reflection', comment='最近生成范围（reflection仅反思 / full含四区）')
    review_model_id = Column(BigInteger, comment='本次AI评论所用的裁判模型ID，关联ai_model.model_id，应与学生侧(model_id=1)不同，避免同模型自评')
    # 老师点评
    teacher_id = Column(BigInteger, comment='批阅教师用户ID，关联sys_user.user_id')
    reflection_score = Column(Numeric(5, 2), comment='老师对反思维度的评分（0-100）')
    teacher_comment = Column(Text, comment='老师针对学生反思结论的点评文字')
    overall_comment = Column(Text, comment='老师总评')
    ai_comment_feedback = Column(Text, comment='老师对AI评论的看法（认同/补充/纠正）')
    review_status = Column(CHAR(1), server_default='0', comment='批阅状态（0草稿 1已提交）')
    review_time = Column(DateTime, comment='老师点评提交时间')
    # 审计字段
    del_flag = Column(CHAR(1), server_default='0', comment='删除标志（0存在 2删除）')
    create_by = Column(String(64), server_default='', comment='创建者用户名')
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')
    update_by = Column(String(64), server_default='', comment='最后更新者用户名')
    update_time = Column(DateTime, default=datetime.now, comment='最后更新时间')


class EduReviewDialogue(Base):
    """反思批阅-AI评论历史 —— 记录每次生成的AI评论版本，供老师对比历史版本"""
    __tablename__ = 'edu_review_dialogue'
    __table_args__ = {'comment': '反思批阅-AI评论历史版本'}

    dialogue_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='历史记录主键ID')
    review_id = Column(BigInteger, nullable=False, comment='关联的批阅记录ID，关联edu_review.review_id')
    record_id = Column(BigInteger, nullable=False, comment='冗余字段，关联的学习记录ID，方便按record查历史')
    ai_comment = Column(JSONB, nullable=False, comment='该版本的AI评论结构化结果')
    ai_comment_text = Column(Text, comment='该版本AI评论纯文本摘要')
    version = Column(Integer, nullable=False, comment='版本号')
    scope = Column(String(20), server_default='reflection', comment='生成范围（reflection仅反思 / full含四区）')
    model_id = Column(BigInteger, comment='生成该版本所用模型ID，关联ai_model.model_id')
    create_time = Column(DateTime, default=datetime.now, comment='生成时间')
