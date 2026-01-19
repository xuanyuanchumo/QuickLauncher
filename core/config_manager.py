# file: D:\Projects\PycharmProjects\QuickLauncher\core\config_manager.py
"""
配置管理器 - 优化版本
负责应用配置的加载、保存和管理
"""

import json
import os
import shutil
import threading
import uuid
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict, field
from datetime import datetime
from PySide6.QtCore import QObject, Signal
from PySide6.QtQml import QJSValue
import copy

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class AppConfig:
    """应用配置"""
    name: str
    path: str
    icon_path: str = ""
    arguments: str = ""
    working_dir: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
    added_time: float = 0.0
    last_used: float = 0.0
    usage_count: int = 0
    id: str = ""
    favorite: bool = False


@dataclass
class QuickWindowConfig:
    """快捷窗口配置"""
    auto_start: bool = False
    show_on_startup: bool = True
    show_labels: bool = False
    position: str = "bottom_center"
    size: int = 64
    opacity: float = 0.25
    hover_scale: float = 1.5
    app_order: List[str] = field(default_factory=list)
    max_icons_per_row: int = 10
    background_color: str = "#FFFFFF"  # 默认白色背景
    icon_spacing: int = 10
    icon_size: int = 48
    use_system_icons: bool = True
    show_favorites: bool = False
    animation_enabled: bool = True
    opacity_noise: float = 0.01
    opacity_tint: float = 0.15
    radius_blur: int = 20
    background_opacity: float = 0.3  # 专门用于背景毛玻璃效果的透明度
    rows: int = 1  # 窗口行数
    cols: int = 1  # 窗口列数


@dataclass
class MainWindowConfig:
    """主窗口配置"""
    opacity: float = 1.0
    background_image: str = ""
    opacity_noise: float = 0.02  # 噪声透明度
    opacity_tint: float = 0.15  # 色调透明度
    radius_blur: int = 20  # 模糊半径
    background_opacity: float = 0.3  # 专门用于背景毛玻璃效果的透明度
    background_color: str = "#FFFFFF"  # 背景颜色
    luminosity: float = 0.1  # 亮度
    enable_noise: bool = True  # 启用噪声效果
    auto_start: bool = False  # 开机自启动
    show_on_startup: bool = True  # 启动时显示主窗口
    hide_on_startup_if_auto: bool = False  # 开机自启动时是否隐藏主窗口


class ConfigManager(QObject):
    """配置管理器（单例模式）"""

    # 信号定义
    quick_config_updated = Signal()  # 快捷窗口配置更新信号
    main_window_config_updated = Signal()  # 主窗口配置更新信号
    app_list_updated = Signal()  # 应用列表更新信号
    app_config_updated = Signal(str)  # 特定应用配置更新信号
    config_saved = Signal(bool)  # 配置保存完成信号

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            super().__init__()
            self._initialized = True

            # 使用项目根目录作为配置目录
            self.project_root = Path(__file__).parent.parent
            self.config_dir = self.project_root / "config"
            self.config_file = self.config_dir / "config.json"
            self.backup_dir = self.config_dir / "backups"

            # 创建必要的目录
            self.config_dir.mkdir(parents=True, exist_ok=True)
            self.backup_dir.mkdir(parents=True, exist_ok=True)

            # 数据存储
            self._config: Dict[str, Any] = {}
            self._apps: Dict[str, AppConfig] = {}
            self._quick_config: QuickWindowConfig = QuickWindowConfig()
            self._main_window_config: MainWindowConfig = MainWindowConfig()

            # 添加保存状态追踪
            self._is_saving = False
            self._pending_save = False
            self._last_save_time = 0
            self._save_lock = threading.RLock()

            # 初始化数据
            self._load_config()

            logger.info(f"配置管理器初始化完成，配置文件: {self.config_file}")

    def _load_config(self):
        """加载配置文件"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                logger.info(f"配置文件加载成功: {self.config_file}")
            else:
                self._config = self._get_default_config()
                logger.info("使用默认配置")
                # 保存默认配置
                self.save(create_backup=False)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            self._config = self._get_default_config()
            self._create_backup("load_failure")

        # 加载应用配置
        self._load_apps()

        # 加载快捷窗口配置
        self._load_quick_config()

        # 加载主窗口配置
        self._load_main_window_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "version": "1.0.0",
            "apps": {},
            "quick_window": asdict(QuickWindowConfig()),
            "main_window": asdict(MainWindowConfig()),
            "settings": {
                "auto_save": True,
                "backup_count": 5,
                "recent_apps_limit": 10,
                "cache_dir": "cache/icons",
                "max_cache_size_mb": 500,
                "cache_days_to_live": 7,
                "min_save_interval": 1,  # 最小保存间隔（秒）
                "max_pending_time": 5   # 最大延迟保存时间（秒）
            }
        }

    def _load_apps(self):
        """加载应用配置"""
        apps_data = self._config.get("apps", {})
        self._apps = {}

        for app_id, app_data in apps_data.items():
            try:
                # 确保所有必需字段都存在
                app_config = AppConfig(
                    name=app_data.get("name", ""),
                    path=app_data.get("path", ""),
                    icon_path=app_data.get("icon_path", ""),
                    arguments=app_data.get("arguments", ""),
                    working_dir=app_data.get("working_dir", ""),
                    description=app_data.get("description", ""),
                    tags=app_data.get("tags", []),
                    added_time=app_data.get("added_time", 0.0),
                    last_used=app_data.get("last_used", 0.0),
                    usage_count=app_data.get("usage_count", 0),
                    id=app_data.get("id", app_id),
                    favorite=app_data.get("favorite", False)
                )
                self._apps[app_id] = app_config
            except Exception as e:
                logger.error(f"加载应用配置失败 {app_id}: {e}")

    def _load_quick_config(self):
        """加载快捷窗口配置"""
        quick_data = self._config.get("quick_window", {})
        if isinstance(quick_data, dict):
            temp_config = QuickWindowConfig()
            for key, value in quick_data.items():
                if hasattr(temp_config, key):
                    # 确保数据类型正确
                    if key == "hover_scale":
                        # 确保hover_scale是浮点数类型
                        try:
                            setattr(temp_config, key, float(value))
                        except (ValueError, TypeError):
                            setattr(temp_config, key, 1.2)  # 默认值
                    elif key == "opacity":
                        # 确保opacity是浮点数类型
                        try:
                            setattr(temp_config, key, float(value))
                        except (ValueError, TypeError):
                            setattr(temp_config, key, 0.9)  # 默认值
                    elif key == "size" or key == "icon_size":
                        # 确保尺寸是整数类型
                        try:
                            setattr(temp_config, key, int(value))
                        except (ValueError, TypeError):
                            setattr(temp_config, key, 64)  # 默认值
                    elif key == "icon_spacing" or key == "max_icons_per_row":
                        # 确保间距和数量是整数类型
                        try:
                            setattr(temp_config, key, int(value))
                        except (ValueError, TypeError):
                            setattr(temp_config, key, 10 if key == "icon_spacing" else 10)  # 默认值
                    elif key in ["rows", "cols"]:  # 处理行数和列数
                        # 确保行数和列数是整数类型
                        try:
                            setattr(temp_config, key, int(value))
                        except (ValueError, TypeError):
                            # 设置默认值
                            if key == "rows":
                                setattr(temp_config, key, 1)  # 默认1行
                            elif key == "cols":
                                setattr(temp_config, key, 5)  # 默认5列
                    elif key in ["auto_start", "show_on_startup", "show_labels", "use_system_icons", "show_favorites", "animation_enabled"]:
                        # 确保布尔值是布尔类型
                        if isinstance(value, bool):
                            setattr(temp_config, key, value)
                        elif isinstance(value, str):
                            setattr(temp_config, key, value.lower() == "true")
                        else:
                            setattr(temp_config, key, bool(value))
                    elif key in ["opacity_noise", "opacity_tint"]:
                        # 确保这些是浮点数类型
                        try:
                            setattr(temp_config, key, float(value))
                        except (ValueError, TypeError):
                            # 设置默认值
                            if key == "opacity_noise":
                                setattr(temp_config, key, 0.01)
                            elif key == "opacity_tint":
                                setattr(temp_config, key, 0.15)
                    elif key == "radius_blur":
                        # 确保radius_blur是整数类型
                        try:
                            setattr(temp_config, key, int(value))
                        except (ValueError, TypeError):
                            setattr(temp_config, key, 20)  # 默认值
                    elif key == "background_opacity":
                        # 确保background_opacity是浮点数类型
                        try:
                            setattr(temp_config, key, float(value))
                        except (ValueError, TypeError):
                            setattr(temp_config, key, 0.3)  # 默认值
                    else:
                        setattr(temp_config, key, value)
            
            # 检查是否需要更新旧的默认背景颜色
            if temp_config.background_color == "#2D2D30":
                temp_config.background_color = "#FFFFFF"
            
            self._quick_config = temp_config
        else:
            self._quick_config = QuickWindowConfig()

    def _load_main_window_config(self):
        """加载主窗口配置"""
        main_window_data = self._config.get("main_window", {})
        if isinstance(main_window_data, dict):
            temp_config = MainWindowConfig()
            for key, value in main_window_data.items():
                if hasattr(temp_config, key):
                    # 确保数据类型正确
                    if key in ["opacity", "opacity_noise", "opacity_tint", "luminosity"]:
                        # 确保这些是浮点数类型
                        try:
                            setattr(temp_config, key, float(value))
                        except (ValueError, TypeError):
                            # 设置默认值
                            if key == "opacity":
                                setattr(temp_config, key, 1.0)
                            elif key == "opacity_noise":
                                setattr(temp_config, key, 0.01)
                            elif key == "opacity_tint":
                                setattr(temp_config, key, 0.15)
                            elif key == "luminosity":
                                setattr(temp_config, key, 0.1)
                    elif key in ["radius_blur"]:
                        # 确保这些是整数类型
                        try:
                            setattr(temp_config, key, int(value))
                        except (ValueError, TypeError):
                            if key == "radius_blur":
                                setattr(temp_config, key, 20)  # 默认值
                    elif key in ["background_opacity"]:
                        # 确保这些是浮点数类型
                        try:
                            setattr(temp_config, key, float(value))
                        except (ValueError, TypeError):
                            setattr(temp_config, key, 0.3)  # 默认值
                    elif key in ["background_image", "background_color"]:
                        # 确保这些是字符串类型
                        try:
                            setattr(temp_config, key, str(value))
                        except (ValueError, TypeError):
                            if key == "background_image":
                                setattr(temp_config, key, "")  # 默认值
                            elif key == "background_color":
                                setattr(temp_config, key, "#FFFFFF")  # 默认值
                    elif key in ["enable_noise", "auto_start", "show_on_startup", "hide_on_startup_if_auto"]:
                        # 确保这些是布尔类型
                        if isinstance(value, bool):
                            setattr(temp_config, key, value)
                        elif isinstance(value, str):
                            setattr(temp_config, key, value.lower() == "true")
                        else:
                            setattr(temp_config, key, bool(value))
                    else:
                        setattr(temp_config, key, value)
            
            self._main_window_config = temp_config
        else:
            self._main_window_config = MainWindowConfig()

    def _create_backup(self, reason: str = "manual"):
        """创建备份"""
        try:
            if not self.config_file.exists():
                return False

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"config_{timestamp}_{reason}.json"

            # 复制配置文件
            shutil.copy2(self.config_file, backup_file)

            # 清理旧的备份文件
            self._cleanup_old_backups()

            logger.info(f"配置备份已创建: {backup_file}")
            return True

        except Exception as e:
            logger.error(f"创建备份失败: {e}")
            return False

    def _cleanup_old_backups(self):
        """清理旧的备份文件"""
        try:
            backup_files = list(self.backup_dir.glob("config_*.json"))
            backup_files.sort(key=lambda x: x.stat().st_mtime)

            max_backups = self._config.get("settings", {}).get("backup_count", 5)
            if len(backup_files) > max_backups:
                files_to_delete = backup_files[:-max_backups]
                for file in files_to_delete:
                    try:
                        file.unlink()
                        logger.info(f"删除旧备份: {file}")
                    except Exception as e:
                        logger.warning(f"删除备份文件失败 {file}: {e}")

        except Exception as e:
            logger.error(f"清理备份文件失败: {e}")

    def save(self, create_backup: bool = True, force: bool = False):
        """保存配置，增加防抖和状态追踪功能"""
        with self._save_lock:
            import time
            current_time = time.time()
            
            # 检查是否需要跳过保存（最小间隔检查）
            min_interval = self._config.get("settings", {}).get("min_save_interval", 1)
            if not force and (current_time - self._last_save_time < min_interval):
                # 设置延迟保存标志
                self._pending_save = True
                # 启动一个计时器，在最大延迟时间内保存
                if not hasattr(self, '_delayed_save_timer'):
                    self._delayed_save_timer = threading.Timer(
                        self._config.get("settings", {}).get("max_pending_time", 5),
                        self._execute_delayed_save
                    )
                    self._delayed_save_timer.start()
                return True

            # 检查是否已经在保存过程中
            if self._is_saving and not force:
                # 标记需要保存但暂时跳过
                self._pending_save = True
                return True

            # 开始保存过程
            self._is_saving = True
            self._pending_save = False

        try:
            if create_backup:
                self._create_backup("before_save")

            # 在保存前清理可能的QJSValue对象
            apps_data = {}
            for app_id, app in self._apps.items():
                # 将app转换为字典并处理可能的QJSValue
                app_dict = asdict(app)
                clean_app_dict = self._clean_qjsvalue_from_dict(app_dict)

                # 确保行数和列数是整数类型
                if 'rows' in clean_app_dict and clean_app_dict['rows'] is not None:
                    try:
                        clean_app_dict['rows'] = int(clean_app_dict['rows'])
                    except (ValueError, TypeError):
                        clean_app_dict['rows'] = 1  # 默认值
                if 'cols' in clean_app_dict and clean_app_dict['cols'] is not None:
                    try:
                        clean_app_dict['cols'] = int(clean_app_dict['cols'])
                    except (ValueError, TypeError):
                        clean_app_dict['cols'] = 5  # 默认值

                apps_data[app_id] = clean_app_dict

            quick_config_data = asdict(self._quick_config)
            clean_quick_config_data = self._clean_qjsvalue_from_dict(quick_config_data)
            
            # 确保行数和列数是整数类型
            if 'rows' in clean_quick_config_data and clean_quick_config_data['rows'] is not None:
                try:
                    clean_quick_config_data['rows'] = int(clean_quick_config_data['rows'])
                except (ValueError, TypeError):
                    clean_quick_config_data['rows'] = 1  # 默认值
            if 'cols' in clean_quick_config_data and clean_quick_config_data['cols'] is not None:
                try:
                    clean_quick_config_data['cols'] = int(clean_quick_config_data['cols'])
                except (ValueError, TypeError):
                    clean_quick_config_data['cols'] = 5  # 默认值
            
            main_window_config_data = asdict(self._main_window_config)
            clean_main_window_config_data = self._clean_qjsvalue_from_dict(main_window_config_data)

            # 准备配置数据
            self._config["apps"] = apps_data
            self._config["quick_window"] = clean_quick_config_data
            self._config["main_window"] = clean_main_window_config_data

            # 保存到文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)

            logger.info("配置保存成功")
            self._last_save_time = current_time
            self.config_saved.emit(True)
            return True

        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            self.config_saved.emit(False)
            return False

        finally:
            # 重置保存状态
            with self._save_lock:
                self._is_saving = False
                # 检查是否有待处理的保存请求
                if self._pending_save:
                    self._pending_save = False
                    # 使用另一个线程执行延迟保存以避免阻塞
                    threading.Thread(target=self._execute_delayed_save, daemon=True).start()

    def _execute_delayed_save(self):
        """执行延迟保存"""
        with self._save_lock:
            if self._pending_save:
                self._pending_save = False
        self.save(create_backup=False)

    def get_config_info(self) -> Dict[str, Any]:
        """获取配置信息"""
        try:
            return {
                "config_file": str(self.config_file),
                "config_dir": str(self.config_dir),
                "backup_dir": str(self.backup_dir),
                "app_count": len(self._apps),
                "config_version": self._config.get("version", "1.0.0"),
                "last_save_time": os.path.getmtime(self.config_file) if self.config_file.exists() else 0,
                "settings": self._config.get("settings", {}),
                "is_saving": self._is_saving,
                "pending_save": self._pending_save
            }
        except Exception as e:
            logger.error(f"获取配置信息失败: {e}")
            return {}

    # 应用管理方法
    def add_app(self, app: AppConfig) -> str:
        """添加应用"""
        try:
            if not app.id:
                app.id = str(uuid.uuid4())

            self._apps[app.id] = app

            # 自动保存
            if self._config.get("settings", {}).get("auto_save", True):
                self.save()

            self.app_list_updated.emit()
            return app.id

        except Exception as e:
            logger.error(f"添加应用失败: {e}")
            return ""

    def remove_app(self, app_id: str) -> bool:
        """移除应用"""
        if app_id in self._apps:
            del self._apps[app_id]

            # 从快捷窗口排序中移除
            if app_id in self._quick_config.app_order:
                self._quick_config.app_order.remove(app_id)

            # 自动保存
            if self._config.get("settings", {}).get("auto_save", True):
                self.save()

            self.app_list_updated.emit()
            return True
        return False

    def update_app(self, app_id: str, **kwargs):
        """更新应用"""
        if app_id in self._apps:
            for key, value in kwargs.items():
                if hasattr(self._apps[app_id], key):
                    setattr(self._apps[app_id], key, value)

            # 自动保存
            if self._config.get("settings", {}).get("auto_save", True):
                self.save()

            self.app_list_updated.emit()
            self.app_config_updated.emit(app_id)

    def get_app(self, app_id: str) -> Optional[AppConfig]:
        """获取应用"""
        return self._apps.get(app_id)

    def get_all_apps(self) -> Dict[str, AppConfig]:
        """获取所有应用"""
        return self._apps.copy()

    def get_apps_by_tag(self, tag: str) -> Dict[str, AppConfig]:
        """根据标签获取应用"""
        return {
            app_id: app for app_id, app in self._apps.items()
            if tag in app.tags
        }

    def get_favorite_apps(self) -> Dict[str, AppConfig]:
        """获取收藏的应用"""
        return {
            app_id: app for app_id, app in self._apps.items()
            if app.favorite
        }

    def search_apps(self, query: str) -> Dict[str, AppConfig]:
        """搜索应用"""
        query_lower = query.lower()
        results = {}

        for app_id, app in self._apps.items():
            if (query_lower in app.name.lower() or
                query_lower in app.path.lower() or
                query_lower in app.description.lower() or
                any(query_lower in tag.lower() for tag in app.tags)):
                results[app_id] = app

        return results

    def get_recent_apps(self, limit: int = 10) -> Dict[str, AppConfig]:
        """获取最近使用的应用"""
        sorted_apps = sorted(
            self._apps.values(),
            key=lambda x: x.last_used,
            reverse=True
        )
        return {app.id: app for app in sorted_apps[:limit]}

    # 快捷窗口配置
    @property
    def quick_config(self) -> QuickWindowConfig:
        return self._quick_config

    @quick_config.setter
    def quick_config(self, config: QuickWindowConfig):
        self._quick_config = config
        if self._config.get("settings", {}).get("auto_save", True):
            self.save()
        self.quick_config_updated.emit()

    def update_quick_config(self, **kwargs):
        """更新快捷窗口配置"""
        processed_kwargs = {}
        for key, value in kwargs.items():
            # 处理QJSValue对象
            processed_value = self._process_qjsvalue(value)
            if hasattr(self._quick_config, key):
                processed_kwargs[key] = processed_value
                setattr(self._quick_config, key, processed_value)

        # 如果更新了app_order，需要特别处理以确保发出正确的信号
        app_order_updated = 'app_order' in processed_kwargs
        
        if self._config.get("settings", {}).get("auto_save", True):
            self.save()
        
        # 发出配置更新信号
        self.quick_config_updated.emit()
        
        # 如果应用顺序更新了，也发出应用列表更新信号，因为这会影响快捷窗口显示
        if app_order_updated:
            self.app_list_updated.emit()
        
        # 记录更新的配置项
        logger.info(f"快捷窗口配置已更新: {list(processed_kwargs.keys())}")

        return True

    def _clean_qjsvalue_from_dict(self, obj):
        """从字典或列表中递归清理QJSValue对象"""
        if isinstance(obj, dict):
            return {key: self._clean_qjsvalue_from_dict(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._clean_qjsvalue_from_dict(item) for item in obj]
        elif isinstance(obj, QJSValue):
            # 将QJSValue转换为Python原生类型
            if obj.isBool():
                return bool(obj.toBool())
            elif obj.isNumber():
                num_val = obj.toNumber()
                return float(num_val) if '.' in str(num_val) else int(num_val)
            elif obj.isString():
                return str(obj.toString())
            elif obj.isNull() or obj.isUndefined():
                return None
            else:
                try:
                    return obj.toVariant()
                except:
                    return str(obj.toString()) if hasattr(obj, 'toString') else None
        else:
            return obj

    def _process_qjsvalue(self, value):
        """处理QJSValue对象，将其转换为Python原生类型"""
        if isinstance(value, QJSValue):
            # 将QJSValue转换为Python原生类型
            if value.isBool():
                return bool(value.toBool())
            elif value.isNumber():
                num_val = value.toNumber()
                return float(num_val) if '.' in str(num_val) else int(num_val)
            elif value.isString():
                return str(value.toString())
            elif value.isNull() or value.isUndefined():
                return None
            else:
                # 尝试转换复杂对象
                try:
                    return value.toVariant()
                except:
                    # 如果转换失败，尝试直接转换
                    return str(value.toString()) if hasattr(value, 'toString') else None
        elif isinstance(value, (dict, list)):
            # 递归处理字典和列表中的QJSValue对象
            if isinstance(value, dict):
                return {k: self._process_qjsvalue(v) for k, v in value.items()}
            else:
                return [self._process_qjsvalue(item) for item in value]
        else:
            return value

    # 批量操作
    def batch_update_apps(self, updates: Dict[str, Dict[str, Any]]):
        """批量更新应用"""
        for app_id, update_data in updates.items():
            if app_id in self._apps:
                self.update_app(app_id, **update_data)
        # 批量操作完成后统一保存一次
        if updates and self._config.get("settings", {}).get("auto_save", True):
            self.save()

    def batch_remove_apps(self, app_ids: List[str]) -> bool:
        """批量移除应用"""
        success = True
        for app_id in app_ids:
            if not self.remove_app(app_id):
                success = False
        
        # 批量操作完成后统一保存一次
        if app_ids and self._config.get("settings", {}).get("auto_save", True):
            self.save()

        return success

    # 导入导出
    def export_apps(self, file_path: Path, format_type: str = "json") -> bool:
        """导出应用列表"""
        try:
            apps_data = {app_id: asdict(app) for app_id, app in self._apps.items()}

            if format_type == "json":
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(apps_data, f, indent=2, ensure_ascii=False)
            elif format_type == "csv":
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=[
                        'id', 'name', 'path', 'description', 'tags',
                        'added_time', 'last_used', 'usage_count', 'favorite'
                    ])
                    writer.writeheader()
                    for app_data in apps_data.values():
                        writer.writerow(app_data)
            else:
                return False

            logger.info(f"应用列表已导出到: {file_path}")
            return True

        except Exception as e:
            logger.error(f"导出应用列表失败: {e}")
            return False

    def import_apps(self, file_path: Path, format_type: str = "json") -> bool:
        """导入应用列表"""
        try:
            if format_type == "json":
                with open(file_path, 'r', encoding='utf-8') as f:
                    apps_data = json.load(f)
            elif format_type == "csv":
                import csv
                apps_data = {}
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        app_id = row.get('id', str(uuid.uuid4()))
                        apps_data[app_id] = row
            else:
                return False

            # 导入应用
            imported_count = 0
            for app_id, app_data in apps_data.items():
                try:
                    app_config = AppConfig(
                        name=app_data.get("name", ""),
                        path=app_data.get("path", ""),
                        icon_path=app_data.get("icon_path", ""),
                        arguments=app_data.get("arguments", ""),
                        working_dir=app_data.get("working_dir", ""),
                        description=app_data.get("description", ""),
                        tags=app_data.get("tags", []),
                        added_time=app_data.get("added_time", 0.0),
                        last_used=app_data.get("last_used", 0.0),
                        usage_count=app_data.get("usage_count", 0),
                        id=app_id,
                        favorite=app_data.get("favorite", False)
                    )
                    self.add_app(app_config)
                    imported_count += 1
                except Exception as e:
                    logger.error(f"导入应用失败 {app_id}: {e}")

            logger.info(f"成功导入 {imported_count} 个应用")
            # 导入完成后统一保存一次
            if imported_count > 0 and self._config.get("settings", {}).get("auto_save", True):
                self.save()
            return True

        except Exception as e:
            logger.error(f"导入应用列表失败: {e}")
            return False

    # 工具方法
    def get_app_count(self) -> int:
        """获取应用数量"""
        return len(self._apps)

    def clear_all_apps(self) -> bool:
        """清空所有应用"""
        try:
            self._apps.clear()
            self._quick_config.app_order.clear()
            self.save()
            self.app_list_updated.emit()
            return True
        except Exception as e:
            logger.error(f"清空应用失败: {e}")
            return False

    def reset_config(self):
        """重置配置"""
        try:
            self._config = self._get_default_config()
            self._apps.clear()
            self._quick_config = QuickWindowConfig()
            self.save()
            self.app_list_updated.emit()
            self.quick_config_updated.emit()
            return True
        except Exception as e:
            logger.error(f"重置配置失败: {e}")
            return False

    def validate_config(self) -> Dict[str, Any]:
        """验证配置有效性"""
        try:
            validation_results = {
                "apps_valid": True,
                "quick_config_valid": True,
                "backup_files_exist": False,
                "config_file_exists": False,
                "issues": []
            }

            # 检查配置文件是否存在
            validation_results["config_file_exists"] = self.config_file.exists()
            if not validation_results["config_file_exists"]:
                validation_results["issues"].append("配置文件不存在")

            # 检查备份文件
            backup_files = list(self.backup_dir.glob("*.json"))
            validation_results["backup_files_exist"] = len(backup_files) > 0

            # 检查应用配置
            for app_id, app in self._apps.items():
                if not app.name or not app.path:
                    validation_results["apps_valid"] = False
                    validation_results["issues"].append(f"应用 {app_id} 配置不完整")

            # 检查快捷窗口配置
            if not isinstance(self._quick_config, QuickWindowConfig):
                validation_results["quick_config_valid"] = False
                validation_results["issues"].append("快捷窗口配置无效")

            return validation_results

        except Exception as e:
            logger.error(f"验证配置失败: {e}")
            return {
                "apps_valid": False,
                "quick_config_valid": False,
                "backup_files_exist": False,
                "config_file_exists": False,
                "issues": [str(e)]
            }

    def update_main_window_config(self, **kwargs):
        """更新主窗口配置"""
        processed_kwargs = {}
        for key, value in kwargs.items():
            # 处理QJSValue对象
            processed_value = self._process_qjsvalue(value)
            if hasattr(self._main_window_config, key):
                # 特别处理background_image字段，避免None值
                if key == 'background_image' and processed_value is None:
                    processed_value = ""  # 将None转换为空字符串
                processed_kwargs[key] = processed_value
                setattr(self._main_window_config, key, processed_value)

        if self._config.get("settings", {}).get("auto_save", True):
            self.save()
        
        # 发出主窗口配置更新信号
        self.main_window_config_updated.emit()
        
        # 记录主窗口配置更新
        logger.info(f"主窗口配置已更新: {list(processed_kwargs.keys())}")
        if 'background_image' in processed_kwargs:
            logger.info(f"背景图片路径已更新: {processed_kwargs['background_image']}")

        return True

    @property
    def main_window_config(self) -> MainWindowConfig:
        return self._main_window_config

    @main_window_config.setter
    def main_window_config(self, config: MainWindowConfig):
        # 确保背景图片路径不被None值覆盖
        if config.background_image is None:
            config.background_image = self._main_window_config.background_image
        self._main_window_config = config
        if self._config.get("settings", {}).get("auto_save", True):
            self.save()
        self.main_window_config_updated.emit()