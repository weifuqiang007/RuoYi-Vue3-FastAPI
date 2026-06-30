"""
应用生命周期钩子注册表（框架侧）。

设计目的
--------
框架入口 ``server.py`` 不应反向依赖任何业务模块（如 ``module_rag``）。
业务模块把自己的启动初始化逻辑写在各自的 ``hooks.py`` 里，用
``@LifecycleHooks.register_startup`` 注册；框架在启动时统一调用，
从而实现"框架只定机制，业务自注册"。

发现机制与 ``common/router.py`` 的路由自动发现一致：
扫描 ``<project_root>/*/hooks.py``，import 触发装饰器注册。
"""

import glob
import importlib
import os
import sys
from collections.abc import Awaitable, Callable

from utils.log_util import logger

# 启动钩子：(名称, 异步回调) —— 类级共享，单进程启动下无需加锁
_startup_hooks: list[tuple[str, Callable[['object'], Awaitable[None]]]] = []


class LifecycleHooks:
    """应用生命周期钩子注册表。"""

    @classmethod
    def register_startup(cls, name: str):
        """装饰器：注册一个异步启动钩子。

        :param name: 钩子名称，用于启动日志标识
        :return: 装饰器（原函数原样返回）
        """

        def decorator(fn: Callable[['object'], Awaitable[None]]):
            _startup_hooks.append((name, fn))
            return fn

        return decorator

    @classmethod
    def discover_and_load(cls) -> None:
        """扫描所有 ``module_*/hooks.py`` 并导入，触发 ``@register_startup`` 注册。

        导入失败的模块仅告警，不阻断应用启动。
        """
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        pattern = os.path.join(project_root, '*', 'hooks.py')
        for file_path in sorted(glob.glob(pattern)):
            relative_path = os.path.relpath(file_path, project_root)
            module_name = relative_path.replace(os.sep, '.')[:-3]
            try:
                importlib.import_module(module_name)
                logger.info(f'生命周期钩子模块加载: {module_name}')
            except Exception as e:
                logger.warning(f'生命周期钩子模块加载失败 {module_name}: {e}')

    @classmethod
    async def run_startup(cls, app: 'object') -> None:
        """执行所有已注册的启动钩子（单个失败不阻断整体启动）。"""
        if not _startup_hooks:
            logger.info('无生命周期启动钩子需要执行')
            return
        for name, fn in _startup_hooks:
            try:
                await fn(app)
                logger.info(f'启动钩子[{name}]完成')
            except Exception as e:
                logger.warning(f'启动钩子[{name}]失败（不阻断启动）: {e}')
