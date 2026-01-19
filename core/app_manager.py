# file: D:\Projects\PycharmProjects\QuickLauncher\core\app_manager.py
"""
应用管理器 - 优化版本
负责应用的添加、删除、搜索和管理
"""

import os
import hashlib
import time
import uuid
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import asdict
import logging

# 配置日志
logger = logging.getLogger(__name__)


class AppManager:
    """应用管理器 - 支持快捷方式解析和图标管理"""

    def __init__(self, config_manager=None):
        if config_manager is None:
            from .config_manager import ConfigManager
            self.config_manager = ConfigManager()
        else:
            self.config_manager = config_manager

        # 动态导入图标缓存
        try:
            from .icon_cache import IconCache
            self.icon_cache = IconCache()
            self.cache_available = True
        except ImportError as e:
            logger.warning(f"图标缓存模块导入失败: {e}")
            self.cache_available = False
            self.icon_cache = None

        # 性能统计
        self.start_time = time.time()
        self.total_operations = 0
        self.successful_operations = 0

    def _resolve_shortcut(self, lnk_path: str) -> Optional[str]:
        """解析快捷方式目标路径"""
        try:
            if not os.path.exists(lnk_path):
                return None

            # Windows系统使用win32com
            if os.name == 'nt':
                import pythoncom
                import win32com.client

                pythoncom.CoInitialize()
                try:
                    shell = win32com.client.Dispatch("WScript.Shell")
                    shortcut = shell.CreateShortCut(lnk_path)
                    target_path = shortcut.TargetPath

                    if target_path and os.path.exists(target_path):
                        return target_path

                    # 尝试在工作目录中查找
                    working_dir = shortcut.WorkingDirectory
                    if working_dir and target_path:
                        potential_path = os.path.join(working_dir, os.path.basename(target_path))
                        if os.path.exists(potential_path):
                            return potential_path

                    return target_path
                finally:
                    pythoncom.CoUninitialize()
            else:
                # Linux/Mac系统尝试读取.desktop文件
                if lnk_path.endswith('.desktop'):
                    with open(lnk_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        for line in content.split('\n'):
                            if line.startswith('Exec='):
                                exec_path = line[5:].strip()
                                # 移除可能的参数
                                exec_path = exec_path.split(' ')[0]
                                if os.path.exists(exec_path):
                                    return exec_path
            return None
        except Exception as e:
            logger.warning(f"解析快捷方式失败 {lnk_path}: {e}")
            return None

    def _generate_app_id(self, exe_path: str) -> str:
        """生成应用ID"""
        # 使用路径的MD5哈希作为ID
        path_hash = hashlib.md5(exe_path.encode('utf-8')).hexdigest()[:12]
        timestamp = int(time.time() * 1000) % 10000
        return f"app_{path_hash}_{timestamp}"

    def _get_app_info(self, exe_path: str) -> Dict[str, Any]:
        """获取应用信息"""
        try:
            # 获取文件信息
            path_obj = Path(exe_path)

            if not path_obj.exists():
                return {}

            # 获取文件信息
            file_stats = path_obj.stat()
            added_time = file_stats.st_ctime
            modified_time = file_stats.st_mtime
            file_size = file_stats.st_size

            # 生成应用名（使用文件名，不带扩展名）
            app_name = path_obj.stem
            if not app_name or app_name.isspace():
                app_name = path_obj.name

            # 生成图标路径
            icon_path = f"image://icon/{exe_path}"

            return {
                'name': app_name,
                'path': str(exe_path),
                'icon_path': icon_path,
                'added_time': added_time,
                'modified_time': modified_time,
                'file_size': file_size,
                'file_type': path_obj.suffix.lower(),
                'exists': True
            }

        except Exception as e:
            logger.error(f"获取应用信息失败 {exe_path}: {e}")
            return {}

    def _validate_application(self, exe_path: str) -> bool:
        """验证应用有效性"""
        try:
            if not os.path.exists(exe_path):
                logger.warning(f"文件不存在: {exe_path}")
                return False

            # 检查文件扩展名
            valid_extensions = ['.exe', '.lnk', '.msi', '.bat', '.cmd', '.ps1', '.sh', '.desktop', '.app']
            file_ext = Path(exe_path).suffix.lower()

            if file_ext not in valid_extensions:
                logger.warning(f"不支持的文件类型: {file_ext}")
                return False

            # 检查文件大小（最大500MB）
            try:
                file_size = os.path.getsize(exe_path)
                if file_size > 500 * 1024 * 1024:  # 500MB
                    logger.warning(f"文件过大: {file_size} bytes")
                    return False
            except:
                pass

            return True

        except Exception as e:
            logger.error(f"验证应用失败 {exe_path}: {e}")
            return False

    def add_application(self, exe_path: str, app_name: Optional[str] = None,
                       description: str = "", tags: List[str] = None) -> Dict[str, Any]:
        """添加应用 - 支持快捷方式"""
        self.total_operations += 1

        try:
            if not self._validate_application(exe_path):
                return {"success": False, "message": "无效的应用文件"}

            original_path = exe_path
            resolved_path = exe_path

            # 如果是快捷方式，解析目标
            if exe_path.lower().endswith(('.lnk', '.desktop')):
                real_path = self._resolve_shortcut(exe_path)
                if real_path:
                    resolved_path = real_path
                    logger.info(f"快捷方式 {original_path} 解析为: {resolved_path}")
                else:
                    logger.warning(f"无法解析快捷方式: {original_path}")

            # 检查是否已存在相同路径的应用
            existing_apps = self.config_manager.get_all_apps()
            for app_id, app in existing_apps.items():
                if app.path == resolved_path or app.path == original_path:
                    logger.info(f"应用已存在: {resolved_path}")
                    return {"success": False, "message": "应用已存在"}

            # 获取应用信息
            app_info = self._get_app_info(resolved_path)
            if not app_info:
                return {"success": False, "message": "无法获取应用信息"}

            # 使用自定义应用名或自动生成
            if not app_name or app_name.strip() == "":
                app_name = app_info['name']

            # 生成应用ID
            app_id = self._generate_app_id(resolved_path)

            # 创建应用配置
            from .config_manager import AppConfig
            app_config = AppConfig(
                name=app_name.strip(),
                path=resolved_path,
                icon_path=app_info['icon_path'],
                description=description.strip(),
                tags=tags or [],
                added_time=time.time(),
                last_used=0.0,
                usage_count=0,
                id=app_id,
                favorite=False
            )

            # 添加到配置管理器
            result_id = self.config_manager.add_app(app_config)

            if result_id:
                self.successful_operations += 1
                logger.info(f"成功添加应用: {app_name} (ID: {result_id}")

                # 预加载图标（仅预加载常用尺寸以节省内存）
                if self.cache_available and self.icon_cache:
                    try:
                        self.icon_cache.preload_icons([resolved_path], [48])  # 仅预加载最常用的尺寸
                    except:
                        pass

                return {
                    "success": True,
                    "app_id": result_id,
                    "message": f"成功添加应用: {app_name}"
                }
            else:
                return {"success": False, "message": "添加应用失败"}

        except Exception as e:
            logger.error(f"添加应用时出错 {exe_path}: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"添加应用失败: {str(e)}"}

    def batch_add_applications(self, app_paths: List[str]) -> Dict[str, Any]:
        """批量添加应用"""
        results = {
            "total": len(app_paths),
            "successful": 0,
            "failed": 0,
            "details": []
        }

        for path in app_paths:
            result = self.add_application(path)
            results["details"].append({
                "path": path,
                "success": result["success"],
                "message": result.get("message", "")
            })

            if result["success"]:
                results["successful"] += 1
            else:
                results["failed"] += 1

        return results

    def remove_application(self, app_id: str) -> Dict[str, Any]:
        """删除应用"""
        self.total_operations += 1

        try:
            app = self.config_manager.get_app(app_id)
            if not app:
                return {"success": False, "message": "应用不存在"}

            app_name = app.name

            if self.config_manager.remove_app(app_id):
                self.successful_operations += 1
                return {
                    "success": True,
                    "message": f"已删除应用: {app_name}"
                }
            else:
                return {"success": False, "message": "删除应用失败"}

        except Exception as e:
            logger.error(f"删除应用失败 {app_id}: {e}")
            return {"success": False, "message": f"删除应用失败: {str(e)}"}

    def remove_applications(self, app_ids: List[str]) -> Dict[str, Any]:
        """批量删除应用"""
        results = {
            "total": len(app_ids),
            "successful": 0,
            "failed": 0,
            "details": []
        }

        for app_id in app_ids:
            result = self.remove_application(app_id)
            results["details"].append({
                "app_id": app_id,
                "success": result["success"],
                "message": result.get("message", "")
            })

            if result["success"]:
                results["successful"] += 1
            else:
                results["failed"] += 1

        return results

    def update_application(self, app_id: str, **kwargs) -> Dict[str, Any]:
        """更新应用信息"""
        self.total_operations += 1

        try:
            app = self.config_manager.get_app(app_id)
            if not app:
                return {"success": False, "message": "应用不存在"}

            # 验证名称
            if 'name' in kwargs and not kwargs['name'].strip():
                return {"success": False, "message": "应用名称不能为空"}

            # 更新应用配置
            self.config_manager.update_app(app_id, **kwargs)
            self.successful_operations += 1

            return {
                "success": True,
                "message": "应用信息更新成功"
            }

        except Exception as e:
            logger.error(f"更新应用失败 {app_id}: {e}")
            return {"success": False, "message": f"更新应用失败: {str(e)}"}

    def toggle_favorite(self, app_id: str) -> Dict[str, Any]:
        """切换收藏状态"""
        try:
            app = self.config_manager.get_app(app_id)
            if not app:
                return {"success": False, "message": "应用不存在"}

            new_favorite = not app.favorite
            self.config_manager.update_app(app_id, favorite=new_favorite)

            return {
                "success": True,
                "favorite": new_favorite,
                "message": f"已{'收藏' if new_favorite else '取消收藏'}应用"
            }

        except Exception as e:
            logger.error(f"切换收藏状态失败 {app_id}: {e}")
            return {"success": False, "message": f"切换收藏状态失败: {str(e)}"}

    def get_applications(self, filter_type: str = "all") -> List[Dict[str, Any]]:
        """获取应用列表"""
        try:
            if filter_type == "favorites":
                apps = self.config_manager.get_favorite_apps()
            elif filter_type == "recent":
                apps = self.config_manager.get_recent_apps()
            else:
                apps = self.config_manager.get_all_apps()

            result = []
            for app_id, app in apps.items():
                try:
                    app_dict = asdict(app)
                    app_dict['id'] = app_id

                    # 检查文件是否存在
                    app_dict['exists'] = os.path.exists(app.path)

                    # 确保有图标路径
                    if not app_dict.get('icon_path') or app_dict['icon_path'] == "":
                        app_dict['icon_path'] = f"image://icon/{app.path}"

                    result.append(app_dict)
                except Exception as e:
                    logger.warning(f"转换应用数据失败 {app_id}: {e}")
                    continue

            return result

        except Exception as e:
            logger.error(f"获取应用列表失败: {e}")
            return []

    def search_applications(self, query: str, search_fields: List[str] = None) -> List[Dict[str, Any]]:
        """搜索应用"""
        try:
            if not query or query.strip() == "":
                return self.get_applications()

            search_fields = search_fields or ["name", "description", "tags", "path"]
            query_lower = query.lower().strip()
            apps = self.config_manager.get_all_apps()
            results = []

            for app_id, app in apps.items():
                try:
                    match_found = False

                    # 检查各个字段
                    if "name" in search_fields and query_lower in app.name.lower():
                        match_found = True
                    elif "description" in search_fields and query_lower in app.description.lower():
                        match_found = True
                    elif "path" in search_fields and query_lower in app.path.lower():
                        match_found = True
                    elif "tags" in search_fields:
                        for tag in app.tags:
                            if query_lower in tag.lower():
                                match_found = True
                                break

                    if match_found:
                        app_dict = asdict(app)
                        app_dict['id'] = app_id
                        app_dict['exists'] = os.path.exists(app.path)

                        if not app_dict.get('icon_path'):
                            app_dict['icon_path'] = f"image://icon/{app.path}"

                        results.append(app_dict)

                except Exception as e:
                    logger.debug(f"搜索应用时出错 {app_id}: {e}")
                    continue

            return results

        except Exception as e:
            logger.error(f"搜索应用失败: {e}")
            return []

    def get_application_by_id(self, app_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取应用"""
        try:
            app = self.config_manager.get_app(app_id)
            if app:
                app_dict = asdict(app)
                app_dict['id'] = app_id
                app_dict['exists'] = os.path.exists(app.path)
                return app_dict
            return None
        except Exception as e:
            logger.error(f"获取应用信息失败 {app_id}: {e}")
            return None

    def launch_application(self, app_id: str) -> Dict[str, Any]:
        """启动应用"""
        self.total_operations += 1

        try:
            app = self.config_manager.get_app(app_id)
            if not app:
                return {"success": False, "message": "应用不存在"}

            # 检查文件是否存在
            if not os.path.exists(app.path):
                return {"success": False, "message": "应用文件不存在"}

            # 更新使用统计
            current_time = time.time()
            self.config_manager.update_app(
                app_id,
                last_used=current_time,
                usage_count=app.usage_count + 1
            )

            # 启动应用
            import subprocess
            import platform

            try:
                system = platform.system()

                if system == "Windows":
                    # Windows系统
                    if app.path.lower().endswith('.lnk'):
                        # 对于快捷方式，使用os.startfile
                        os.startfile(app.path)
                    else:
                        # 对于可执行文件
                        cmd = f'"{app.path}"'
                        if app.arguments:
                            cmd += f' {app.arguments}'

                        CREATE_NO_WINDOW = 0x08000000
                        subprocess.Popen(
                            cmd,
                            shell=True,
                            creationflags=CREATE_NO_WINDOW
                        )
                elif system == "Darwin":  # macOS
                    if app.path.endswith('.app'):
                        subprocess.Popen(['open', app.path])
                    else:
                        subprocess.Popen(['open', '-a', app.path])
                else:  # Linux
                    if app.path.endswith('.desktop'):
                        subprocess.Popen(['gtk-launch', app.path])
                    else:
                        subprocess.Popen(['xdg-open', app.path])

                logger.info(f"启动应用: {app.name}")
                self.successful_operations += 1

                return {
                    "success": True,
                    "message": f"已启动应用: {app.name}"
                }

            except Exception as e:
                logger.error(f"启动应用失败 {app.path}: {e}")
                return {"success": False, "message": f"启动应用失败: {str(e)}"}

        except Exception as e:
            logger.error(f"启动应用时出错: {e}")
            return {"success": False, "message": f"启动应用失败: {str(e)}"}

    def get_app_stats(self) -> Dict[str, Any]:
        """获取应用统计信息"""
        try:
            apps = self.config_manager.get_all_apps()

            total_apps = len(apps)
            recent_apps = 0
            total_usage = 0
            favorite_apps = 0
            most_used = None
            max_usage = 0

            current_time = time.time()
            week_ago = current_time - (7 * 24 * 3600)  # 一周前

            for app_id, app in apps.items():
                total_usage += app.usage_count

                if app.last_used > week_ago:
                    recent_apps += 1

                if app.favorite:
                    favorite_apps += 1

                if app.usage_count > max_usage:
                    max_usage = app.usage_count
                    most_used = app.name

            # 计算成功率
            success_rate = 100
            if self.total_operations > 0:
                success_rate = (self.successful_operations / self.total_operations * 100)

            return {
                'total_apps': total_apps,
                'recent_apps': recent_apps,
                'total_usage': total_usage,
                'favorite_apps': favorite_apps,
                'most_used': most_used,
                'max_usage': max_usage,
                'success_rate': round(success_rate, 2),
                'uptime': round(time.time() - self.start_time, 2)
            }
        except Exception as e:
            logger.error(f"获取应用统计失败: {e}")
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

    def cleanup_missing_apps(self) -> Dict[str, Any]:
        """清理不存在的应用"""
        try:
            apps = self.config_manager.get_all_apps()
            missing_apps = []

            for app_id, app in apps.items():
                if not os.path.exists(app.path):
                    missing_apps.append(app_id)

            if missing_apps:
                result = self.remove_applications(missing_apps)
                return {
                    "success": True,
                    "cleaned_count": len(missing_apps),
                    "details": result
                }
            else:
                return {
                    "success": True,
                    "cleaned_count": 0,
                    "message": "没有发现不存在的应用"
                }

        except Exception as e:
            logger.error(f"清理不存在应用失败: {e}")
            return {"success": False, "message": f"清理不存在应用失败: {str(e)}"}

    def export_applications(self, file_path: str, format_type: str = "json") -> Dict[str, Any]:
        """导出应用列表"""
        try:
            success = self.config_manager.export_apps(Path(file_path), format_type)
            if success:
                return {
                    "success": True,
                    "message": f"应用列表已导出到: {file_path}",
                    "file_path": file_path,
                    "format": format_type
                }
            else:
                return {"success": False, "message": "导出应用列表失败"}
        except Exception as e:
            logger.error(f"导出应用列表失败: {e}")
            return {"success": False, "message": f"导出应用列表失败: {str(e)}"}

    def import_applications(self, file_path: str, format_type: str = "json") -> Dict[str, Any]:
        """导入应用列表"""
        try:
            success = self.config_manager.import_apps(Path(file_path), format_type)
            if success:
                return {
                    "success": True,
                    "message": f"成功从 {file_path} 导入应用列表",
                    "file_path": file_path,
                    "format": format_type
                }
            else:
                return {"success": False, "message": "导入应用列表失败"}
        except Exception as e:
            logger.error(f"导入应用列表失败: {e}")
            return {"success": False, "message": f"导入应用列表失败: {str(e)}"}

    def reset_all(self) -> Dict[str, Any]:
        """重置所有数据"""
        try:
            success = self.config_manager.reset_config()
            if success:
                # 重置统计
                self.start_time = time.time()
                self.total_operations = 0
                self.successful_operations = 0

                return {
                    "success": True,
                    "message": "所有数据已重置"
                }
            else:
                return {"success": False, "message": "重置数据失败"}
        except Exception as e:
            logger.error(f"重置数据失败: {e}")
            return {"success": False, "message": f"重置数据失败: {str(e)}"}

    def manage_quick_window_apps(self, action: str, app_ids: List[str] = None) -> Dict[str, Any]:
        """管理快捷窗口显示的应用"""
        try:
            # 获取当前快捷窗口配置
            quick_config = self.config_manager.quick_config

            if action == "get":
                # 返回当前快捷窗口中的应用
                current_apps = []
                for app_id in quick_config.app_order:
                    app = self.config_manager.get_app(app_id)
                    if app:
                        current_apps.append({
                            "id": app_id,
                            "name": app.name,
                            "path": app.path
                        })

                return {
                    "success": True,
                    "apps": current_apps,
                    "total": len(current_apps)
                }

            elif action == "add" and app_ids:
                # 添加应用到快捷窗口
                added_count = 0
                for app_id in app_ids:
                    if app_id not in quick_config.app_order:
                        app = self.config_manager.get_app(app_id)
                        if app:
                            quick_config.app_order.append(app_id)
                            added_count += 1

                # 更新配置
                self.config_manager.quick_config = quick_config

                # 发出应用列表更新信号，以便快捷窗口更新显示
                self.config_manager.app_list_updated.emit()

                return {
                    "success": True,
                    "added_count": added_count,
                    "message": f"已添加 {added_count} 个应用到快捷窗口"
                }

            elif action == "remove" and app_ids:
                # 从快捷窗口移除应用
                removed_count = 0
                for app_id in app_ids:
                    if app_id in quick_config.app_order:
                        quick_config.app_order.remove(app_id)
                        removed_count += 1

                # 更新配置
                self.config_manager.quick_config = quick_config

                # 发出应用列表更新信号，以便快捷窗口更新显示
                self.config_manager.app_list_updated.emit()

                return {
                    "success": True,
                    "removed_count": removed_count,
                    "message": f"已从快捷窗口移除 {removed_count} 个应用"
                }

            elif action == "reorder" and app_ids:
                # 重新排序应用
                quick_config.app_order = app_ids
                self.config_manager.quick_config = quick_config

                # 发出应用列表更新信号，以便快捷窗口更新显示
                self.config_manager.app_list_updated.emit()

                return {
                    "success": True,
                    "message": "应用顺序已更新"
                }

            else:
                return {
                    "success": False,
                    "message": "无效的操作或缺少参数"
                }

        except Exception as e:
            logger.error(f"管理快捷窗口应用失败: {e}")
            return {"success": False, "message": f"管理快捷窗口应用失败: {str(e)}"}