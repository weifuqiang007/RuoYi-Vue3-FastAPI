"""
登录策略扩展点注册表（框架侧）。

设计目的
--------
框架登录流程（``module_admin/service/login_service.py``）不应反向依赖任何业务
模块的审核/准入逻辑（例如 ``module_learning`` 的注册审核）。业务模块把"登录前
校验"写在各自的 ``hooks.py`` 里，用 ``@LoginPolicyHooks.register_login_validator``
注册；框架在认证通过后、签发 token 前统一调用，从而实现"框架只定机制，业务自注册"。

注册时机
--------
与 ``common.lifecycle.LifecycleHooks`` 一致：业务模块的 ``hooks.py`` 在应用启动时
被 ``LifecycleHooks.discover_and_load`` 自动导入，导入即触发装饰器注册。
因此登录校验器在服务开始接收请求前就已就绪。

与启动钩子的区别
----------------
启动钩子是 **fail-soft**（单个失败不阻断整体启动）；登录校验器是 **fail-fast**——
任一校验器抛出的异常（通常是 ``LoginException``）会直接向上抛出，由调用方/
全局异常处理器返回登录失败响应。框架**不吞没**业务校验异常，否则会把"待审核/
审核未通过"等正当拦截变成静默放行。
"""

from collections.abc import Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from utils.log_util import logger

# 登录校验器：(名称, 异步回调) —— 类级共享，注册后随进程存活
# 回调签名：async (query_db, user_id) -> None，校验失败时直接抛 LoginException
_login_validators: list[tuple[str, Callable[[AsyncSession, int], Awaitable[None]]]] = []


class LoginPolicyHooks:
    """登录策略扩展点注册表。"""

    @classmethod
    def register_login_validator(cls, name: str):
        """装饰器：注册一个登录前校验器。

        :param name: 校验器名称，用于日志标识
        :return: 装饰器（原函数原样返回）
        """

        def decorator(fn: Callable[[AsyncSession, int], Awaitable[None]]):
            _login_validators.append((name, fn))
            logger.debug(f'登录校验器已注册: {name}')
            return fn

        return decorator

    @classmethod
    async def run_login_validators(cls, query_db: AsyncSession, user_id: int) -> None:
        """按注册顺序执行所有登录校验器。

        无校验器时（如全新框架、未接入业务审核）直接返回，登录正常放行。
        任一校验器抛出的异常将原样向上抛出（fail-fast），不做兜底吞没。

        :param query_db: orm 会话
        :param user_id: 待登录用户 ID
        :raises LoginException: 业务校验未通过时由具体校验器抛出
        """
        if not _login_validators:
            return
        for name, fn in _login_validators:
            logger.debug(f'执行登录校验器[{name}]')
            await fn(query_db, user_id)
