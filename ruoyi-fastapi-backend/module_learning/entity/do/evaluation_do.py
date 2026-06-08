from datetime import datetime

from sqlalchemy import CHAR, BigInteger, Boolean, Column, DateTime, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from config.database import Base


class EduEvaluation(Base):
    """教师评价表 —— 教师对学生提交的四区学习成果进行分区评分和反馈，一个学习记录只有一条评价"""
    __tablename__ = 'edu_evaluation'
    __table_args__ = {'comment': '教师评价表'}

    evaluation_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='评价主键ID')
    record_id = Column(BigInteger, nullable=False, comment='关联的学习记录ID，关联edu_learning_record.record_id（唯一约束）')
    teacher_id = Column(BigInteger, nullable=False, comment='评价教师ID，关联sys_user.user_id')
    # 分区评分（百分制）
    scenario_score = Column(Numeric(5, 2), comment='情境区评分（0-100）')
    decision_score = Column(Numeric(5, 2), comment='决策区评分（0-100）')
    reflection_score = Column(Numeric(5, 2), comment='反思区评分（0-100）')
    research_score = Column(Numeric(5, 2), comment='研究生成区评分（0-100）')
    total_score = Column(Numeric(5, 2), comment='加权总分 = 情境×0.2 + 决策×0.2 + 反思×0.3 + 研究×0.3')
    # 分区评语
    scenario_feedback = Column(Text, comment='教师对情境区的评语')
    decision_feedback = Column(Text, comment='教师对决策区的评语')
    reflection_feedback = Column(Text, comment='教师对反思区的评语')
    research_feedback = Column(Text, comment='教师对研究生成区的评语')
    overall_feedback = Column(Text, comment='教师总评语，综合评价学生整体表现')
    # 优秀标记
    is_excellent = Column(Boolean, server_default='false', comment='是否标记为优秀案例（true优秀 false普通）')
    # 状态控制
    status = Column(CHAR(1), server_default='0', comment='评价状态（0草稿 1已发布/学生可见）')
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')
    update_time = Column(DateTime, default=datetime.now, comment='最后更新时间')


class EduExcellentCase(Base):
    """优秀案例库（匿名化） —— 将学生优秀成果脱敏后入库，供后续学生参考学习"""
    __tablename__ = 'edu_excellent_case'
    __table_args__ = {'comment': '优秀案例库（匿名化）'}

    case_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='案例主键ID')
    source_record_id = Column(BigInteger, comment='原始学习记录ID（仅教师可见，用于溯源），关联edu_learning_record.record_id')
    task_id = Column(BigInteger, nullable=False, comment='关联的教学任务ID，关联edu_task.task_id')
    # 匿名化后的学生成果数据（姓名等敏感信息已脱敏）
    scenario_desc = Column(Text, comment='脱敏后的情境描述（人名替换为X某）')
    decision_data = Column(JSONB, comment='脱敏后的决策记录数据')
    reflection_data = Column(Text, comment='脱敏后的反思精华摘录')
    research_data = Column(Text, comment='脱敏后的研究问题和论文核心内容')
    teacher_comment = Column(Text, comment='教师推荐语，说明为何选为优秀案例')
    tags = Column(JSONB, comment='案例标签，JSON数组如["老年社工","伦理决策"]，继承自情境区的category_tags')
    # 状态控制
    status = Column(CHAR(1), server_default='0', comment='案例状态（0待审核 1已发布 2已下架）')
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')
    update_time = Column(DateTime, default=datetime.now, comment='最后更新时间')
