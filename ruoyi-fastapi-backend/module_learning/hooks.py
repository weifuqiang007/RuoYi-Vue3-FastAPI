"""
学习模块的应用生命周期钩子（业务侧自注册）。

被 ``common/lifecycle.py`` 的 discover 机制在应用启动时自动导入。导入时通过
``@LoginPolicyHooks.register_login_validator`` 把"教育注册审核"校验注册进框架
登录流程，从而让框架入口 ``module_admin/service/login_service.py`` 不再直接
依赖 ``module_learning``（消除框架→业务反向耦合）。

注册审核逻辑原内联于 login_service.authenticate_user，迁移至此；行为保持不变：
  - 审核中（audit_status=='0'）→ 拦截，提示"账号待审核"
  - 已拒绝（audit_status=='2'）→ 拦截，提示"审核未通过"并带备注
  - 无审核记录或已通过 → 放行
"""

from exceptions.exception import LoginException
from utils.log_util import logger

from common.login_policy import LoginPolicyHooks


@LoginPolicyHooks.register_login_validator('edu_registration_audit')
async def check_registration_audit(query_db, user_id: int) -> None:
    """登录前校验教育模块注册审核状态：待审核 / 被拒绝则阻止登录。"""

    # 惰性 import：discover 阶段导入本模块时不触发 module_learning 的完整加载链
    from module_learning.dao.edu_dao import EduDao

    audit = await EduDao.get_audit_by_user_id(query_db, user_id)
    if audit and audit.audit_status == '0':
        logger.warning('账号待审核')
        raise LoginException(data='', message='账号待审核，请等待管理员审批')
    if audit and audit.audit_status == '2':
        logger.warning('账号审核未通过')
        raise LoginException(
            data='', message=f'账号审核未通过：{audit.audit_remark or "请联系管理员"}'
        )
