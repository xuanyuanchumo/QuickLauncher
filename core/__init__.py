"""
QuickLauncher 核心模块
包含配置管理、应用管理和图标缓存等核心功能
"""

from .config_manager import ConfigManager, AppConfig, QuickWindowConfig
from .app_manager import AppManager
from .icon_cache import IconCache

__all__ = [
    'ConfigManager',
    'AppConfig',
    'QuickWindowConfig',
    'AppManager',
    'IconCache'
]