# file:D:\Projects\PycharmProjects\QuickLauncher\ui\main_window.py
"""
主窗口后端逻辑
连接QML界面和核心业务逻辑
"""

import sys
import json
import traceback
import os
from pathlib import Path
from typing import List, Dict, Any
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox
from PySide6.QtCore import QObject, Signal, Slot, QTimer, QUrl, QThread
from core.app_manager import AppManager
from core.config_manager import ConfigManager
from utils.file_handler import FileHandler
from utils.logger_config import app_logger

# 尝试导入PIL用于图片处理
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("警告: PIL库未安装，无法进行图片尺寸检查和优化")


class MainWindowBackend(QObject):
    """主窗口后端逻辑"""

    # 信号定义
    app_list_updated = Signal(list)
    config_updated = Signal(dict)  # 通用配置更新信号，需要传递配置字典
    main_window_config_updated = Signal('QVariantMap')  # 主窗口配置更新信号
    quick_window_config_updated = Signal('QVariantMap')  # 快捷窗口配置更新信号
    operation_status = Signal(str, str)  # (操作类型, 状态消息)
    show_message = Signal(str, str, str)  # (标题, 内容, 类型)
    import_export_status = Signal(str, bool, str)  # (操作, 成功, 消息)

    def __init__(self):
        super().__init__()
        app_logger.debug("初始化主窗口后端")
        self.app_manager = AppManager()
        self.config_manager = ConfigManager()

        # 从app_manager获取缓存相关信息
        self.cache_available = self.app_manager.cache_available
        self.icon_cache = self.app_manager.icon_cache

        # 连接配置更新信号
        # 主窗口需要接收快捷窗口配置更新以保持同步
        self.config_manager.quick_config_updated.connect(self._on_quick_config_updated)
        self.config_manager.main_window_config_updated.connect(self._on_main_window_config_updated)
        self.config_manager.app_list_updated.connect(self._on_app_list_updated)
        self.config_manager.config_saved.connect(self._on_config_saved)

        # 定时自动保存 - 优化为60秒一次，减少磁盘写入频率
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self._auto_save)
        self.auto_save_timer.start(60000)  # 60秒自动保存一次，减少频繁保存
        app_logger.debug("主窗口后端初始化完成")

    def _on_main_window_config_updated(self):
        """主窗口配置更新时发出信号"""
        try:
            print("【DEBUG】开始执行主窗口配置更新")
            config = self.get_main_window_config()
            print(f"【DEBUG】获取到的配置: {config}")
            self.main_window_config_updated.emit(config)
            print(f"【DEBUG】主窗口配置更新信号已发出，配置项: {list(config.keys()) if isinstance(config, dict) else 'N/A'}")
            app_logger.info(f"主窗口配置更新信号已发出，配置项: {list(config.keys()) if isinstance(config, dict) else 'N/A'}")
            
            # 不再发出通用的config_updated信号以避免影响快捷窗口
        except Exception as e:
            app_logger.error(f"主窗口配置更新处理失败: {e}")
            print(f"主窗口配置更新处理失败: {e}")
    
    def _on_quick_config_updated(self):
        """快捷窗口配置更新时发出信号"""
        try:
            # 快捷窗口配置更新时发出专门的信号
            config = self.get_quick_window_config()
            self.quick_window_config_updated.emit(config)
        except Exception as e:
            app_logger.error(f"快捷窗口配置更新处理失败: {e}")
            print(f"快捷窗口配置更新处理失败: {e}")

    def _on_app_list_updated(self):
        """应用列表更新时发出信号"""
        try:
            apps = self.get_applications()
            self.app_list_updated.emit(apps)
        except Exception as e:
            print(f"应用列表更新处理失败: {e}")

    def _on_config_saved(self, success: bool):
        """配置保存完成"""
        if success:
            print("配置保存成功")
        else:
            print("配置保存失败")

    def _auto_save(self):
        """自动保存配置"""
        try:
            # 只在有自动保存启用时才执行
            if self.config_manager._config.get("settings", {}).get("auto_save", True):
                self.config_manager.save(create_backup=False)  # 自动保存时不创建备份，减少磁盘操作
        except Exception as e:
            print(f"自动保存失败: {e}")

    @Slot(result='QVariantList')
    def show_file_dialog(self) -> List[Dict[str, Any]]:
        """显示文件选择对话框"""
        try:
            app = QApplication.instance()
            if not app:
                self.show_message.emit("错误", "应用程序未初始化", "error")
                return []

            # 获取主窗口
            main_window = None
            for widget in app.topLevelWidgets():
                main_window = widget
                break

            if not main_window:
                self.show_message.emit("错误", "未找到主窗口", "error")
                return []

            # 设置文件过滤器
            file_filter = "可执行文件 (*.exe);;快捷方式 (*.lnk);;安装包 (*.msi);;脚本文件 (*.bat *.cmd *.ps1);;所有文件 (*.*)"

            # 打开文件选择对话框
            file_paths, _ = QFileDialog.getOpenFileNames(
                main_window,
                "选择应用程序",
                str(Path.home()),
                file_filter
            )

            if not file_paths:
                return []

            # 批量添加应用
            result = self.app_manager.batch_add_applications(file_paths)

            # 显示结果
            if result["successful"] > 0:
                message = f"成功添加 {result['successful']} 个应用"
                if result["failed"] > 0:
                    message += f"，{result['failed']} 个失败"
                self.show_message.emit("成功", message, "success")
            elif result["failed"] > 0:
                self.show_message.emit("警告", f"添加应用失败，共 {result['failed']} 个文件", "warning")

            # 返回成功添加的应用
            added_apps = []
            for detail in result["details"]:
                if detail["success"]:
                    # 查找刚添加的应用
                    apps = self.get_applications()
                    for app in apps:
                        if app.get("path") == detail["path"]:
                            added_apps.append(app)
                            break

            return added_apps

        except Exception as e:
            error_msg = f"文件选择失败: {str(e)}"
            self.show_message.emit("错误", error_msg, "error")
            print(f"文件选择对话框出错: {e}")
            traceback.print_exc()
            return []

    @Slot(str, result='QVariantMap')
    def add_application(self, exe_path: str) -> Dict[str, Any]:
        """添加应用"""
        try:
            result = self.app_manager.add_application(exe_path)

            if result["success"]:
                self.operation_status.emit("add", result["message"])
                self.app_list_updated.emit(self.get_applications())
            else:
                self.operation_status.emit("add", result["message"])
                self.show_message.emit("错误", result["message"], "error")

            return result

        except Exception as e:
            error_msg = f"添加应用失败: {str(e)}"
            self.show_message.emit("错误", error_msg, "error")
            return {"success": False, "message": error_msg}

    @Slot(str, result='QVariantMap')
    def remove_application(self, app_id: str) -> Dict[str, Any]:
        """删除单个应用"""
        try:
            result = self.app_manager.remove_application(app_id)

            if result["success"]:
                self.operation_status.emit("remove", result["message"])
                self.app_list_updated.emit(self.get_applications())
            else:
                self.operation_status.emit("remove", result["message"])

            return result

        except Exception as e:
            error_msg = f"删除应用失败: {str(e)}"
            self.show_message.emit("错误", error_msg, "error")
            return {"success": False, "message": error_msg}

    @Slot('QVariantList', result='QVariantMap')
    def remove_applications(self, app_ids: List[str]) -> Dict[str, Any]:
        """批量删除应用"""
        try:
            result = self.app_manager.remove_applications(app_ids)

            if result["successful"] > 0:
                message = f"已删除 {result['successful']} 个应用"
                self.operation_status.emit("remove", message)
                self.app_list_updated.emit(self.get_applications())
            else:
                self.operation_status.emit("remove", "删除应用失败")

            return result

        except Exception as e:
            error_msg = f"批量删除应用失败: {str(e)}"
            self.show_message.emit("错误", error_msg, "error")
            return {
                "success": False,
                "message": error_msg,
                "total": len(app_ids),
                "successful": 0,
                "failed": len(app_ids)
            }

    @Slot(str, str, str, result='QVariantMap')
    def update_application_info(self, app_id: str, name: str, description: str) -> Dict[str, Any]:
        """更新应用信息"""
        try:
            if not name.strip():
                return {"success": False, "message": "应用名称不能为空"}

            result = self.app_manager.update_application(
                app_id,
                name=name.strip(),
                description=description.strip()
            )

            if result["success"]:
                self.operation_status.emit("update", result["message"])
                self.app_list_updated.emit(self.get_applications())
            else:
                self.operation_status.emit("update", result["message"])

            return result

        except Exception as e:
            error_msg = f"更新应用信息失败: {str(e)}"
            self.show_message.emit("错误", error_msg, "error")
            return {"success": False, "message": error_msg}

    @Slot(str, result='QVariantMap')
    def launch_application(self, app_id: str) -> Dict[str, Any]:
        """启动应用"""
        try:
            result = self.app_manager.launch_application(app_id)

            if result["success"]:
                self.operation_status.emit("launch", result["message"])
            else:
                self.operation_status.emit("launch", result["message"])

            return result

        except Exception as e:
            error_msg = f"启动应用失败: {str(e)}"
            self.show_message.emit("错误", error_msg, "error")
            return {"success": False, "message": error_msg}

    @Slot(result='QVariantList')
    def get_applications(self) -> List[Dict[str, Any]]:
        """获取应用列表"""
        try:
            return self.app_manager.get_applications()
        except Exception as e:
            print(f"获取应用列表失败: {e}")
            self.show_message.emit("错误", "获取应用列表失败", "error")
            return []

    @Slot(str, result='QVariantList')
    def search_applications(self, query: str) -> List[Dict[str, Any]]:
        """搜索应用"""
        try:
            # 限制搜索只在应用名称中进行
            return self.app_manager.search_applications(query, search_fields=["name"])
        except Exception as e:
            print(f"搜索应用失败: {e}")
            return []

    @Slot(str, 'QVariant', result=bool)
    def update_quick_window_config(self, key: str, value: Any) -> bool:
        """更新快捷窗口配置"""
        try:

            app_logger.info(f"更新快捷窗口配置: {key} = {value}")
            
            # 从PySide6.QtQml导入QJSValue进行类型检查
            from PySide6.QtQml import QJSValue
            # 检查并处理QJSValue对象
            if isinstance(value, QJSValue):
                # 将QJSValue转换为Python原生类型
                if value.isBool():
                    processed_value = bool(value.toBool())
                elif value.isNumber():
                    num_val = value.toNumber()
                    processed_value = float(num_val) if '.' in str(num_val) else int(num_val)
                elif value.isString():
                    processed_value = str(value.toString())
                elif value.isNull() or value.isUndefined():
                    processed_value = None
                else:
                    try:
                        processed_value = value.toVariant()
                    except:
                        processed_value = str(value.toString()) if hasattr(value, 'toString') else None
            else:
                processed_value = value

            self.config_manager.update_quick_config(**{key: processed_value})
            self.operation_status.emit("config", "配置已保存")
            
            app_logger.info(f"快捷窗口配置更新成功: {key} = {processed_value}")
            
            # 如果是 配置发生变化，窗口显示
            if key == "show_on_startup":
                if hasattr(self, 'quick_window_manager'):
                    if processed_value:  # 如果 auto_start 为 True，则显示快捷窗口
                        self.quick_window_manager.show_window()
                    else:  # 如果 auto_start 为 False，则隐藏快捷窗口
                        self.quick_window_manager.hide_window()

            # 如果是 show_on_startup 配置发生变化，开机启动

             # 当show_on_startup被更改时，需要同步更新注册表中的开机启动项
            if key == "auto_start":
                if processed_value:
                    from main import setup_auto_start
                    setup_auto_start(True)
                elif not processed_value:
                    # 则取消开机启动
                    from main import setup_auto_start
                    setup_auto_start(False)
            
            # 如果是 app_order 配置发生变化，也要发出配置更新信号
            if key == "app_order":
                # 这里需要小心，不要发出通用的config_updated信号，以避免影响主窗口
                # 而是让快捷窗口后端自己处理配置更新
                pass
            
            # 如果是背景颜色配置发生变化，也要发出配置更新信号
            if key == "background_color":
                # 这里需要小心，不要发出通用的config_updated信号，以避免影响主窗口
                pass
            
            # 如果是透明度配置发生变化，也要发出配置更新信号
            if key in ["opacity", "opacity_tint", "opacity_noise", "radius_blur"]:
                # 这里需要小心，不要发出通用的config_updated信号，以避免影响主窗口
                # 透明度变化主要影响快捷窗口，让快捷窗口后端自己处理
                pass
            
            # 如果是行数或列数配置发生变化，也要发出快捷窗口配置更新信号
            if key in ["rows", "cols"]:
                # 发出快捷窗口配置更新信号，以便界面实时更新
                try:
                    self._on_quick_config_updated()
                except Exception as e:
                    app_logger.error(f"发出快捷窗口配置更新信号失败: {e}")
            
            return True
        except Exception as e:
            error_msg = f"更新配置失败: {str(e)}"
            app_logger.error(error_msg, exc_info=True)
            self.show_message.emit("错误", error_msg, "error")
            return False

    @Slot(result='QVariantMap')
    def get_quick_window_config(self) -> Dict[str, Any]:
        """获取快捷窗口配置"""
        try:
            from dataclasses import asdict
            return asdict(self.config_manager.quick_config)
        except Exception as e:
            print(f"获取配置失败: {e}")
            self.show_message.emit("错误", "获取配置失败", "error")
            return {}

    @Slot(str, 'QVariant', result=bool)
    def update_main_window_config(self, key: str, value: Any) -> bool:
        """更新主窗口配置"""
        try:
            app_logger.info(f"更新主窗口配置: {key} = {value}")
            
            # 从PySide6.QtQml导入QJSValue进行类型检查
            from PySide6.QtQml import QJSValue
            # 检查并处理QJSValue对象
            if isinstance(value, QJSValue):
                # 将QJSValue转换为Python原生类型
                if value.isBool():
                    processed_value = bool(value.toBool())
                elif value.isNumber():
                    num_val = value.toNumber()
                    processed_value = float(num_val) if '.' in str(num_val) else int(num_val)
                elif value.isString():
                    processed_value = str(value.toString())
                elif value.isNull() or value.isUndefined():
                    processed_value = None
                else:
                    try:
                        processed_value = value.toVariant()
                    except:
                        processed_value = str(value.toString()) if hasattr(value, 'toString') else None
            else:
                processed_value = value

            # 更新配置管理器中的主窗口配置
            self.config_manager.update_main_window_config(**{key: processed_value})
            
            self.operation_status.emit("config", "主窗口配置已保存")
            
            # 当auto_start配置发生变化时，需要更新系统的开机启动设置
            if key == "auto_start":
                if processed_value:  # 如果 auto_start 为 True，则设置开机启动
                    from main import setup_auto_start
                    setup_auto_start(True)
                else:  # 如果 auto_start 为 False，则取消开机启动
                    from main import setup_auto_start
                    setup_auto_start(False)
            
            # 发出配置更新信号，以便前端界面更新
            # 重要：只在主窗口相关的配置改变时才发出信号，避免影响快捷窗口
            if key in ["opacity", "background_image", "opacity_noise", "opacity_tint", "radius_blur", "background_opacity", "background_color", "luminosity", "enable_noise", "auto_start", "show_on_startup", "hide_on_startup_if_auto"]:
                self._on_main_window_config_updated()  # 调用正确的主窗口配置更新方法
            
            # 记录配置更新
            app_logger.info(f"主窗口配置更新成功: {key} = {processed_value}")
            return True
        except Exception as e:
            error_msg = f"更新主窗口配置失败: {str(e)}"
            app_logger.error(error_msg, exc_info=True)
            self.show_message.emit("错误", error_msg, "error")
            return False

    @Slot(result='QVariantMap')
    def get_main_window_config(self) -> Dict[str, Any]:
        """获取主窗口配置"""
        try:
            from dataclasses import asdict
            return asdict(self.config_manager.main_window_config)
        except Exception as e:
            print(f"获取主窗口配置失败: {e}")
            self.show_message.emit("错误", "获取主窗口配置失败", "error")
            return {}

    @Slot(str, result='QVariantMap')
    def get_application_by_id(self, app_id: str) -> Dict[str, Any]:
        """根据ID获取应用"""
        try:
            app = self.app_manager.get_application_by_id(app_id)
            if app:
                return app
            else:
                return {"error": "应用不存在"}
        except Exception as e:
            print(f"获取应用信息失败: {e}")
            return {"error": str(e)}

    @Slot(result='QVariantMap')
    def get_app_stats(self) -> Dict[str, Any]:
        """获取应用统计信息"""
        try:
            return self.app_manager.get_app_stats()
        except Exception as e:
            print(f"获取应用统计失败: {e}")
            return {
                'total_apps': 0,
                'recent_apps': 0,
                'total_usage': 0,
                'favorite_apps': 0,
                'most_used': None,
                'max_usage': 0,
                'success_rate': 100,
                'uptime': 0
            }

    @Slot()
    def refresh_app_list(self):
        """刷新应用列表"""
        try:
            apps = self.get_applications()
            self.app_list_updated.emit(apps)
            self.operation_status.emit("refresh", "应用列表已刷新")
        except Exception as e:
            print(f"刷新应用列表失败: {e}")

    @Slot(str, str, result='QVariantMap')
    def export_applications(self, file_path: str, format_type: str = "json") -> Dict[str, Any]:
        """导出应用列表"""
        try:
            result = self.app_manager.export_applications(file_path, format_type)

            if result["success"]:
                self.operation_status.emit("export", result["message"])
                self.import_export_status.emit("export", True, result["message"])
            else:
                self.import_export_status.emit("export", False, result["message"])

            return result

        except Exception as e:
            error_msg = f"导出应用列表失败: {str(e)}"
            self.import_export_status.emit("export", False, error_msg)
            self.show_message.emit("错误", error_msg, "error")
            return {"success": False, "message": error_msg}

    @Slot(str, str, result='QVariantMap')
    def import_applications(self, file_path: str, format_type: str = "json") -> Dict[str, Any]:
        """导入应用列表"""
        try:
            result = self.app_manager.import_applications(file_path, format_type)

            if result["success"]:
                self.operation_status.emit("import", result["message"])
                self.app_list_updated.emit(self.get_applications())
                self.import_export_status.emit("import", True, result["message"])
            else:
                self.import_export_status.emit("import", False, result["message"])

            return result

        except Exception as e:
            error_msg = f"导入应用列表失败: {str(e)}"
            self.import_export_status.emit("import", False, error_msg)
            self.show_message.emit("错误", error_msg, "error")
            return {"success": False, "message": error_msg}

    @Slot(str, 'QVariantList', result='QVariantMap')
    def manage_quick_window_apps(self, action: str, app_ids: List[str] = None) -> Dict[str, Any]:
        """管理快捷窗口显示的应用"""
        try:
            result = self.app_manager.manage_quick_window_apps(action, app_ids)
            return result
        except Exception as e:
            error_msg = f"管理快捷窗口应用失败: {str(e)}"
            self.show_message.emit("错误", error_msg, "error")
            return {"success": False, "message": error_msg}

    # 背景图片管理功能
    def _validate_image_path(self, image_path: str) -> Dict[str, Any]:
        """验证图片路径的安全性和有效性"""
        try:
            # 处理不同格式的路径
            import urllib.parse
            
            # 如果路径以file://开头，需要解码并移除协议部分
            if image_path.startswith('file://'):
                # 解码URL编码的路径，特别是处理中文等特殊字符
                decoded_path = urllib.parse.unquote(image_path[7:], encoding='utf-8')  # 移除 'file://' 前缀
                # 在Windows系统上，可能需要将/转换为\
                if os.name == 'nt':  # Windows系统
                    decoded_path = decoded_path.replace('/', os.sep)
                image_path = decoded_path
            
            # 验证文件是否存在
            # 使用原始字符串和适当的编码处理包含中文的路径
            if not os.path.exists(image_path):
                return {"success": False, "message": f"源文件不存在: {image_path}"}
            
            # 验证文件扩展名
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
            file_ext = Path(image_path).suffix.lower()
            if file_ext not in allowed_extensions:
                return {"success": False, "message": f"不支持的文件格式: {file_ext}，支持的格式: {', '.join(allowed_extensions)}"}
            
            # 检查文件大小（最大10MB）
            max_size = 10 * 1024 * 1024  # 10MB
            file_size = Path(image_path).stat().st_size
            if file_size > max_size:
                return {"success": False, "message": f"文件大小超过限制: {file_size} > {max_size} 字节 ({file_size/max_size:.2f}x)"}
            
            return {"success": True, "path": image_path, "file_size": file_size}
        except UnicodeDecodeError as e:
            return {"success": False, "message": f"路径包含无法解码的字符: {str(e)}"}
        except Exception as e:
            return {"success": False, "message": f"验证图片路径时出错: {str(e)}"}

    def _optimize_image(self, image_path: str) -> tuple:
        """优化图片尺寸，返回处理后的路径和是否需要清理的标志"""
        temp_path = None
        
        if PIL_AVAILABLE:
            try:
                with Image.open(image_path) as img:
                    width, height = img.size
                    app_logger.debug(f"原始图片尺寸: {width}x{height}")
                    
                    # 检查是否超过最大尺寸
                    max_dimension = 8000
                    if width > max_dimension or height > max_dimension:
                        # 计算新的尺寸，保持宽高比
                        scale_factor = min(max_dimension / width, max_dimension / height)
                        new_width = int(width * scale_factor)
                        new_height = int(height * scale_factor)
                        
                        app_logger.info(f"图片尺寸过大，将调整为: {new_width}x{new_height}")
                        
                        # 调整图片尺寸
                        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        
                        # 保存调整后的图片到临时位置
                        temp_path = str(Path(image_path).with_suffix('')) + '_resized' + Path(image_path).suffix
                        # 根据原始格式选择合适的保存参数
                        if img.format == 'JPEG':
                            resized_img.save(temp_path, format='JPEG', optimize=True, quality=85)
                        elif img.format == 'PNG':
                            resized_img.save(temp_path, format='PNG', optimize=True)
                        else:
                            resized_img.save(temp_path, optimize=True, quality=85)
                        
                        app_logger.info(f"调整后的图片已保存到: {temp_path}")
                        return temp_path, True  # 需要清理临时文件
                    
                    # 对于大文件进行压缩优化，即使尺寸未超过限制
                    file_size = Path(image_path).stat().st_size
                    if file_size > 2 * 1024 * 1024:  # 超过2MB则进行压缩优化
                        app_logger.info(f"图片文件过大({file_size} bytes)，进行压缩优化")
                        
                        # 尝试降低质量来减小文件大小
                        temp_path = str(Path(image_path).with_suffix('')) + '_optimized' + Path(image_path).suffix
                        if img.format == 'JPEG':
                            img.save(temp_path, format='JPEG', optimize=True, quality=80)
                        elif img.format == 'PNG':
                            # 对于PNG，使用不同的优化策略
                            img.save(temp_path, format='PNG', optimize=True)
                        else:
                            img.save(temp_path, optimize=True, quality=80)
                        
                        optimized_size = Path(temp_path).stat().st_size
                        app_logger.info(f"压缩后文件大小: {optimized_size} bytes (原大小: {file_size} bytes)")
                        return temp_path, True  # 需要清理临时文件
            except Exception as img_error:
                app_logger.warning(f"图片处理失败，将使用原始图片: {img_error}")
        
        return image_path, False  # 不需要清理临时文件

    def _get_background_cache_dir(self) -> Path:
        """获取背景图片缓存目录"""
        project_root = Path(__file__).parent.parent
        cache_dir = project_root / "cache" / "bg_main"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    def _delete_old_background_image(self, old_image_path: str):
        """删除旧的背景图片文件"""
        if old_image_path:
            project_root = Path(__file__).parent.parent
            old_full_path = project_root / old_image_path
            if old_full_path.exists():
                try:
                    os.remove(old_full_path)
                    app_logger.info(f"旧背景图片文件已删除: {old_full_path}")
                except Exception as file_error:
                    app_logger.warning(f"删除旧背景图片文件失败: {file_error}")

    @Slot(str, result='QVariantMap')
    def upload_background_image(self, image_path: str) -> Dict[str, Any]:
        """上传背景图片"""
        try:
            app_logger.info(f"开始上传背景图片: {image_path}")
            
            # 验证图片路径
            validation_result = self._validate_image_path(image_path)
            if not validation_result["success"]:
                app_logger.error(f"图片路径验证失败: {validation_result['message']}")
                return validation_result
            
            image_path = validation_result["path"]
            app_logger.debug(f"验证后的图片路径: {image_path}")
            
            # 优化图片
            optimized_path, needs_cleanup = self._optimize_image(image_path)
            app_logger.debug(f"优化后的图片路径: {optimized_path}, 需要清理: {needs_cleanup}")
            
            # 获取当前配置以获取旧的背景图片路径
            current_config = self.get_main_window_config()
            old_image_path = current_config.get('background_image', '')
            app_logger.debug(f"当前配置中的旧背景图片路径: {old_image_path}")
            
            # 获取缓存目录
            cache_dir = self._get_background_cache_dir()
            app_logger.debug(f"背景图片缓存目录: {cache_dir}")
            
            # 验证缓存目录是否可写
            if not os.access(cache_dir, os.W_OK):
                error_msg = f"缓存目录不可写: {cache_dir}"
                app_logger.error(error_msg)
                return {"success": False, "message": error_msg}
            
            # 上传文件到缓存目录
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
            max_size = 10 * 1024 * 1024  # 10MB
            result = FileHandler.upload_file(
                optimized_path,
                str(cache_dir),
                allowed_extensions=allowed_extensions,
                max_size=max_size
            )
            
            app_logger.debug(f"文件上传结果: {result}")
            
            # 清理临时文件（如果需要）
            if needs_cleanup and os.path.exists(optimized_path) and optimized_path != image_path:
                try:
                    os.remove(optimized_path)
                    app_logger.debug(f"已删除临时优化后的图片: {optimized_path}")
                except Exception as e:
                    app_logger.warning(f"删除临时文件失败: {e}")
            
            if result['success']:
                app_logger.info(f"背景图片上传成功: {result['path']}")
                
                # 删除旧的背景图片文件（如果存在且与新文件不同）
                self._delete_old_background_image(old_image_path)
                
                # 更新配置中的背景图片路径
                # 注意：配置中存储相对路径，前端使用协议前缀加载
                app_logger.info(f"正在更新配置中的背景图片路径: {result['path']}")
                self.config_manager.update_main_window_config(background_image=result['path'])
                
                # 验证配置是否已更新
                updated_config = self.get_main_window_config()
                new_background_image = updated_config.get('background_image', '')
                app_logger.info(f"更新后的背景图片路径: {new_background_image}")
                
                # 发出配置更新信号，以便前端界面更新
                self._on_main_window_config_updated()
            else:
                app_logger.error(f"背景图片上传失败: {result['message']}")
                
            return result
        except Exception as e:
            error_msg = f"上传背景图片失败: {str(e)}"
            app_logger.error(error_msg, exc_info=True)
            self.show_message.emit("错误", error_msg, "error")
            return {"success": False, "message": error_msg}

    @Slot(str, result='QVariantMap')
    def update_background_image(self, image_path: str) -> Dict[str, Any]:
        """更新背景图片（与上传功能相同，保持API一致性）"""
        return self.upload_background_image(image_path)

    @Slot(result='QVariantMap')
    def clear_background_image(self) -> Dict[str, Any]:
        """清除背景图片"""
        try:
            app_logger.info("开始清除背景图片")
            
            # 获取当前配置
            current_config = self.get_main_window_config()
            current_image_path = current_config.get('background_image', '')
            
            # 删除旧的背景图片文件
            self._delete_old_background_image(current_image_path)
            
            # 更新配置中的背景图片路径为空
            self.config_manager.update_main_window_config(background_image="")
            
            # 发出配置更新信号，以便前端界面更新
            self._on_main_window_config_updated()
            
            result = {"success": True, "message": "背景图片已清除"}
            app_logger.info(result["message"])
            return result
        except Exception as e:
            error_msg = f"清除背景图片失败: {str(e)}"
            app_logger.error(error_msg, exc_info=True)
            self.show_message.emit("错误", error_msg, "error")
            return {"success": False, "message": error_msg}

    @Slot(str, result='QVariantMap')
    def get_image_info(self, image_path: str) -> Dict[str, Any]:
        """获取图片信息（尺寸、大小等）"""
        try:
            app_logger.info(f"获取图片信息: {image_path}")
            
            # 验证图片路径
            validation_result = self._validate_image_path(image_path)
            if not validation_result["success"]:
                return validation_result
            
            image_path = validation_result["path"]
            
            if PIL_AVAILABLE:
                try:
                    with Image.open(image_path) as img:
                        width, height = img.size
                        format_name = img.format
                        mode = img.mode
                        
                        result = {
                            "success": True,
                            "width": width,
                            "height": height,
                            "format": format_name,
                            "mode": mode,
                            "size_bytes": validation_result["file_size"],
                            "path": image_path
                        }
                        app_logger.debug(f"图片信息: {width}x{height}, 格式: {format_name}, 模式: {mode}")
                        return result
                except Exception as img_error:
                    app_logger.warning(f"获取图片信息失败: {img_error}")
                    # 如果PIL处理失败，返回基本文件信息
                    return {
                        "success": True,
                        "width": 0,
                        "height": 0,
                        "format": "unknown",
                        "mode": "unknown",
                        "size_bytes": validation_result["file_size"],
                        "path": image_path,
                        "message": f"无法获取详细图片信息: {str(img_error)}"
                    }
            else:
                # PIL不可用时，返回基本文件信息
                return {
                    "success": True,
                    "width": 0,
                    "height": 0,
                    "format": "unknown",
                    "mode": "unknown",
                    "size_bytes": validation_result["file_size"],
                    "path": image_path,
                    "message": "PIL库不可用，无法获取图片尺寸信息"
                }
        except Exception as e:
            error_msg = f"获取图片信息失败: {str(e)}"
            app_logger.error(error_msg, exc_info=True)
            return {"success": False, "message": error_msg}

    @Slot(result='QVariantMap')
    def optimize_current_background_image(self) -> Dict[str, Any]:
        """优化当前背景图片"""
        try:
            app_logger.info("开始优化当前背景图片")
            
            # 获取当前配置
            current_config = self.get_main_window_config()
            current_image_path = current_config.get('background_image', '')
            
            if not current_image_path:
                return {"success": False, "message": "当前没有设置背景图片"}
            
            # 确保路径格式正确
            if not current_image_path.startswith('file://'):
                full_path = current_image_path
            else:
                full_path = current_image_path[7:]  # 移除 'file://' 前缀
            
            # 验证图片路径
            validation_result = self._validate_image_path(full_path)
            if not validation_result["success"]:
                app_logger.error(f"当前背景图片路径验证失败: {validation_result['message']}")
                return validation_result
            
            # 优化图片
            optimized_path, needs_cleanup = self._optimize_image(full_path)
            
            # 如果优化后路径不同，说明进行了优化
            if optimized_path != full_path:
                # 获取缓存目录
                cache_dir = self._get_background_cache_dir()
                
                # 上传优化后的图片到缓存目录
                allowed_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
                max_size = 10 * 1024 * 1024  # 10MB
                result = FileHandler.upload_file(
                    optimized_path,
                    str(cache_dir),
                    allowed_extensions=allowed_extensions,
                    max_size=max_size
                )
                
                # 清理临时文件（如果需要）
                if needs_cleanup and os.path.exists(optimized_path) and optimized_path != full_path:
                    try:
                        os.remove(optimized_path)
                        app_logger.debug(f"已删除临时优化后的图片: {optimized_path}")
                    except Exception as e:
                        app_logger.warning(f"删除临时文件失败: {e}")
                
                if result['success']:
                    app_logger.info(f"优化后的背景图片上传成功: {result['path']}")
                    
                    # 删除旧的背景图片文件
                    self._delete_old_background_image(current_image_path)
                    
                    # 更新配置中的背景图片路径
                    self.config_manager.update_main_window_config(background_image=result['path'])
                    
                    # 发出配置更新信号，以便前端界面更新
                    self._on_main_window_config_updated()
                    
                    result["message"] = f"背景图片已优化并更新: {result['message']}"
                    return result
                else:
                    app_logger.error(f"优化后的背景图片上传失败: {result['message']}")
                    return result
            else:
                # 图片未被优化，可能是因为尺寸已经合适
                app_logger.info("当前背景图片尺寸合适，无需优化")
                return {
                    "success": True,
                    "message": "当前背景图片尺寸合适，无需优化",
                    "path": current_image_path
                }
        except UnicodeDecodeError as e:
            error_msg = f"优化背景图片失败，路径包含无法解码的字符: {str(e)}"
            app_logger.error(error_msg, exc_info=True)
            self.show_message.emit("错误", error_msg, "error")
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"优化背景图片失败: {str(e)}"
            app_logger.error(error_msg, exc_info=True)
            self.show_message.emit("错误", error_msg, "error")
            return {"success": False, "message": error_msg}

    @Slot(result='QVariantMap')
    def get_config_info(self) -> Dict[str, Any]:
        """获取配置信息"""
        try:
            return self.config_manager.get_config_info()
        except Exception as e:
            print(f"获取配置信息失败: {e}")
            return {}

    @Slot(str, result='QVariantMap')
    def test_background_image_update(self, test_path: str) -> Dict[str, Any]:
        """测试背景图片更新功能 - 用于调试"""
        try:
            app_logger.info(f"测试背景图片更新功能，路径: {test_path}")
            
            # 首先获取当前配置
            current_config = self.get_main_window_config()
            app_logger.info(f"当前配置中的背景图片: {current_config.get('background_image', 'NOT_FOUND')}")
            
            # 更新配置
            self.config_manager.update_main_window_config(background_image=test_path)
            
            # 验证是否已更新
            updated_config = self.get_main_window_config()
            new_path = updated_config.get('background_image', 'NOT_FOUND')
            app_logger.info(f"更新后的背景图片: {new_path}")
            
            # 发出配置更新信号
            self._on_main_window_config_updated()
            
            success = new_path == test_path
            return {
                "success": success,
                "message": f"测试{'成功' if success else '失败'}: 背景图片{'已更新' if success else '未更新'}",
                "old_path": current_config.get('background_image', ''),
                "new_path": new_path
            }
        except Exception as e:
            error_msg = f"测试背景图片更新功能失败: {str(e)}"
            app_logger.error(error_msg, exc_info=True)
            return {"success": False, "message": error_msg}

    @Slot(result='QVariantMap')
    def cleanup_missing_apps(self) -> Dict[str, Any]:
        """清理不存在的应用"""
        try:
            result = self.app_manager.cleanup_missing_apps()

            if result["success"]:
                self.app_list_updated.emit(self.get_applications())
                if result.get("cleaned_count", 0) > 0:
                    message = f"已清理 {result['cleaned_count']} 个不存在的应用"
                else:
                    message = "没有发现不存在的应用"
                self.show_message.emit("成功", message, "success")
            else:
                self.show_message.emit("错误", result.get("message", "清理失败"), "error")

            return result

        except Exception as e:
            error_msg = f"清理不存在应用失败: {str(e)}"
            self.show_message.emit("错误", error_msg, "error")
            return {"success": False, "message": error_msg}

    @Slot(str, result='QVariantMap')
    def toggle_favorite(self, app_id: str) -> Dict[str, Any]:
        """切换收藏状态"""
        try:
            result = self.app_manager.toggle_favorite(app_id)

            if result["success"]:
                self.app_list_updated.emit(self.get_applications())

            return result

        except Exception as e:
            error_msg = f"切换收藏状态失败: {str(e)}"
            return {"success": False, "message": error_msg}

    @Slot()
    def save_config(self):
        """保存配置"""
        try:
            success = self.config_manager.save()
            if success:
                self.operation_status.emit("save", "配置已保存")
            else:
                self.operation_status.emit("save", "配置保存失败")
        except Exception as e:
            error_msg = f"保存配置失败: {str(e)}"
            self.operation_status.emit("save", error_msg)

    @Slot(result='QVariantMap')
    def reset_all_data(self) -> Dict[str, Any]:
        """重置所有数据"""
        try:
            result = self.app_manager.reset_all()

            if result["success"]:
                self.app_list_updated.emit([])
                self.show_message.emit("成功", "所有数据已重置", "success")
            else:
                self.show_message.emit("错误", result.get("message", "重置失败"), "error")

            return result

        except Exception as e:
            error_msg = f"重置数据失败: {str(e)}"
            self.show_message.emit("错误", error_msg, "error")
            return {"success": False, "message": error_msg}

    @Slot(result='QVariantMap')
    def clear_cache(self) -> Dict[str, Any]:
        """清空图标缓存"""
        try:
            if self.cache_available and self.icon_cache:
                success = self.icon_cache.clear_cache(memory_only=False)
                if success:
                    result = {
                        "success": True,
                        "message": "图标缓存已清空",
                        "cache_dir": str(self.icon_cache.cache_dir)
                    }
                    app_logger.info(result["message"])
                    return result
                else:
                    result = {
                        "success": False,
                        "message": "清空缓存失败"
                    }
                    app_logger.error(result["message"])
                    return result
            else:
                result = {
                    "success": False,
                    "message": "图标缓存不可用"
                }
                app_logger.warning(result["message"])
                return result
        except Exception as e:
            error_msg = f"清空缓存失败: {str(e)}"
            app_logger.error(error_msg, exc_info=True)
            self.show_message.emit("错误", error_msg, "error")
            return {"success": False, "message": error_msg}

    @Slot()
    def show_about_dialog(self):
        """显示关于对话框 - 现在通过QML组件显示"""
        # 此方法保留用于兼容性，实际的关于页面现在通过QML组件显示
        # 未来可以移除或用于显示其他关于信息
        # 发出信号通知前端加载关于页面
        pass








