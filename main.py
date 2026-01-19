#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QuickLauncher 主程序入口
版本: 1.0.0
作者: QuickLauncher Team
"""

import sys
import os
import traceback
from pathlib import Path
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PySide6.QtGui import QIcon, QAction, QTextOption, QPalette, QColor, QPixmap, QPainter
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QUrl, QTimer, QObject, Signal, Slot, Qt, QThread
from ui.main_window import MainWindowBackend
from ui.quick_window import QuickWindowBackend
from core.config_manager import ConfigManager
from ui.icon_provider_safe import SafeIconProvider

# 导入资源路径处理工具
from utils.resource_path import get_qml_path, get_ui_path, get_resource_path
from utils.memory_monitor import start_global_monitoring


class QuickWindowManager:
    """快捷窗口管理器"""

    def __init__(self, quick_backend, main_backend, config_manager, tray_manager=None):
        self.quick_backend = quick_backend
        self.main_backend = main_backend
        self.config_manager = config_manager
        self.tray_manager = tray_manager
        self.engine = None

    def setup_quick_window(self, engine, icon_provider):
        """设置快捷窗口"""
        self.engine = engine

        # 注册后端对象
        self.engine.rootContext().setContextProperty("quickWindowBackend", self.quick_backend)
        self.engine.rootContext().setContextProperty("mainWindowBackend", self.main_backend)

        # 添加图标提供者
        self.engine.addImageProvider("icon", icon_provider)

        # 加载快捷窗口 QML
        qml_path_str = get_qml_path("QuickWindow.qml")
        qml_path = Path(qml_path_str)

        print(f"加载快捷窗口 QML 文件: {qml_path_str}")

        if not self.check_qml_file(qml_path):
            print("快捷窗口 QML 文件检查失败")
            return False

        # 加载 QML
        url = QUrl.fromLocalFile(qml_path_str)
        self.engine.load(url)

        # 检查是否成功加载
        if not self.engine.rootObjects():
            print("加载快捷窗口 QML 失败 - 没有根对象")
            return False

        # 初始化时根据配置设置快捷窗口可见性，而不是依赖QML中的默认设置
        if self.engine.rootObjects():
            quick_window = self.engine.rootObjects()[0]
            # 根据配置决定初始是否显示
            auto_start = self.config_manager.quick_config.auto_start
            show_on_startup = self.config_manager.quick_config.show_on_startup
            quick_window.setProperty("visible", auto_start or show_on_startup)

        print("快捷窗口初始化成功")
        return True

    def check_qml_file(self, qml_path: Path) -> bool:
        """检查 QML 文件是否存在且可读"""
        if not qml_path.exists():
            print(f"错误: QML 文件不存在: {qml_path}")
            return False

        if not os.access(qml_path, os.R_OK):
            print(f"错误: 无法读取 QML 文件: {qml_path}")
            return False

        try:
            with open(qml_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if len(content) < 10:
                    print(f"警告: QML 文件内容过短: {qml_path}")
            return True
        except Exception as e:
            print(f"错误: 无法读取 QML 文件内容: {e}")
            return False

    def show_window(self):
        """显示快捷窗口"""
        if self.engine and self.engine.rootObjects():
            quick_window = self.engine.rootObjects()[0]
            quick_window.setProperty("visible", True)
            quick_window.raise_()
            quick_window.requestActivate()

    def hide_window(self):
        """隐藏快捷窗口"""
        if self.engine and self.engine.rootObjects():
            quick_window = self.engine.rootObjects()[0]
            quick_window.setProperty("visible", False)

    def toggle_visibility(self):
        """切换快捷窗口可见性"""
        if self.engine and self.engine.rootObjects():
            quick_window = self.engine.rootObjects()[0]
            current_visibility = quick_window.property("visible")
            if current_visibility:
                self.hide_window()
            else:
                self.show_window()

    def is_visible(self):
        """检查快捷窗口是否可见"""
        if self.engine and self.engine.rootObjects():
            quick_window = self.engine.rootObjects()[0]
            return quick_window.property("visible")
        return False

    def update_config(self):
        """根据配置更新快捷窗口显示状态"""
        if self.config_manager.quick_config.auto_start:
            self.show_window()
        else:
            self.hide_window()


class SystemTrayManager(QObject):
    """系统托盘管理器"""

    show_main_window = Signal()
    show_quick_window = Signal()
    hide_main_window = Signal()
    toggle_main_window = Signal()
    exit_app = Signal()

    def __init__(self):
        super().__init__()
        self.tray_icon = None
        self.menu = None
        self.main_window = None  # 保存主窗口引用
        self.backend = None  # 保存后端引用

    def setup_tray(self, parent=None, app_instance=None):
        """设置系统托盘"""
        try:
            # 创建系统托盘图标
            self.tray_icon = QSystemTrayIcon(parent)

            # 使用统一的图标路径工具
            from utils.icon_utils import get_app_icon_path, ensure_app_icon_exists
            icon_path = get_app_icon_path()
            
            # 确保图标文件存在
            ensure_app_icon_exists(icon_path, app_instance)
            
            if os.path.exists(icon_path):
                self.tray_icon.setIcon(QIcon(icon_path))
            else:
                # 创建一个简单的图标作为后备
                from PySide6.QtGui import QPixmap, QPainter, QColor, QTextOption
                # 确保此时已有QApplication实例
                if not QApplication.instance():
                    import sys
                    QApplication(sys.argv)
                pixmap = QPixmap(64, 64)
                pixmap.fill(QColor(0, 122, 204, 180))
                painter = QPainter(pixmap)
                painter.setPen(QColor(255, 255, 255))
                painter.setFont(painter.font())
                painter.drawText(pixmap.rect(), "QL", QTextOption(Qt.AlignCenter))
                painter.end()
                self.tray_icon.setIcon(QIcon(pixmap))

            self.tray_icon.setToolTip("QuickLauncher")

            # 连接双击事件到显示主窗口
            self.tray_icon.activated.connect(self._on_tray_icon_activated)

            # 创建右键菜单
            self.menu = QMenu()
            
            # 设置菜单样式，字体颜色为黑色
            self.menu.setStyleSheet(
                "QMenu {" \
                "    background-color: white;" \
                "    color: black;" \
                "    border: 1px solid gray;" \
                "}" \
                "QMenu::item {" \
                "    background-color: transparent;" \
                "    color: black;" \
                "    padding: 4px 20px 4px 20px;" \
                "}" \
                "QMenu::item:selected {" \
                "    background-color: lightgray;" \
                "    color: black;" \
                "}" \
                "QMenu::item:pressed {" \
                "    background-color: gray;" \
                "    color: white;" \
                "}"
            )

            # 添加菜单项
            self.toggle_main_action = QAction("隐藏主窗口", self.menu)  # 初始文本为隐藏
            self.toggle_main_action.triggered.connect(self.toggle_main_window.emit)
            self.menu.addAction(self.toggle_main_action)

            show_quick_action = QAction("显示快捷窗口", self.menu)
            show_quick_action.triggered.connect(self.show_quick_window.emit)
            self.menu.addAction(show_quick_action)

            self.menu.addSeparator()

            # 添加应用管理相关菜单项
            refresh_action = QAction("刷新应用列表", self.menu)
            refresh_action.triggered.connect(self._refresh_app_list)
            self.menu.addAction(refresh_action)

            cleanup_action = QAction("清理不存在应用", self.menu)
            cleanup_action.triggered.connect(self._cleanup_missing_apps)
            self.menu.addAction(cleanup_action)

            # 添加清空缓存菜单项
            clear_cache_action = QAction("清空缓存", self.menu)
            clear_cache_action.triggered.connect(self._clear_cache)
            self.menu.addAction(clear_cache_action)

            self.menu.addSeparator()

            exit_action = QAction("退出", self.menu)
            exit_action.triggered.connect(self.exit_app.emit)
            self.menu.addAction(exit_action)

            # 设置菜单
            self.tray_icon.setContextMenu(self.menu)

            # 显示托盘图标
            self.tray_icon.show()

            print("系统托盘已设置")
            return True

        except Exception as e:
            print(f"设置系统托盘失败: {e}")
            traceback.print_exc()
            return False

    def _refresh_app_list(self):
        """刷新应用列表"""
        # 这里需要获取到 main_window_backend 实例
        # 在实际使用时，需要将这个函数连接到实际的刷新逻辑
        print("刷新应用列表")

    def _on_tray_icon_activated(self, reason):
        """处理托盘图标激活事件"""
        # 当双击或中键点击托盘图标时显示主窗口
        if reason in (QSystemTrayIcon.ActivationReason.DoubleClick, QSystemTrayIcon.ActivationReason.MiddleClick):
            self.show_main_window.emit()

    def set_main_window(self, main_window):
        """设置主窗口引用"""
        self.main_window = main_window

    def set_backend(self, backend):
        """设置后端引用"""
        self.backend = backend

    def update_toggle_action_text(self):
        """更新切换动作的文本"""
        if self.main_window:
            is_visible = self.main_window.property("visible")
            if is_visible:
                self.toggle_main_action.setText("隐藏主窗口")
            else:
                self.toggle_main_action.setText("显示主窗口")

    def _cleanup_missing_apps(self):
        """清理不存在应用"""
        # 这里需要获取到 main_window_backend 实例
        print("清理不存在应用")

    def _clear_cache(self):
        """清空缓存"""
        try:
            # 优先使用后端对象清空缓存
            if self.backend and hasattr(self.backend, 'clear_cache'):
                result = self.backend.clear_cache()
                if result.get('success', False):
                    self.show_message("缓存", result.get('message', '缓存已清空'), QSystemTrayIcon.Information, 2000)
                else:
                    self.show_message("缓存", result.get('message', '清空缓存失败'), QSystemTrayIcon.Warning, 2000)
                return
            
            # 如果无法通过后端清空，直接使用图标缓存类清空
            from core.icon_cache import IconCache
            icon_cache = IconCache()
            success = icon_cache.clear_cache(memory_only=False)
            if success:
                self.show_message("缓存", "图标缓存已清空", QSystemTrayIcon.Information, 2000)
            else:
                self.show_message("缓存", "清空缓存失败", QSystemTrayIcon.Warning, 2000)
        except Exception as e:
            print(f"清空缓存时出错: {e}")
            self.show_message("缓存", f"清空缓存失败: {str(e)}", QSystemTrayIcon.Critical, 3000)

    def show_message(self, title, message, icon=QSystemTrayIcon.Information, timeout=2000):
        """显示托盘消息"""
        if self.tray_icon:
            self.tray_icon.showMessage(title, message, icon, timeout)


def setup_auto_start(enabled: bool):
    """设置开机自启"""
    try:
        import winreg
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"

        # 获取当前可执行文件路径
        if getattr(sys, 'frozen', False):
            app_path = sys.executable  # PyInstaller打包后的exe路径
        else:
            app_path = str(Path(sys.executable).parent / "quicklauncher.exe")

        app_name = "QuickLauncher"

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            if enabled:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
                print(f"已设置开机自启: {app_path}")
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                    print("已取消开机自启")
                except FileNotFoundError:
                    pass
    except Exception as e:
        print(f"设置开机自启失败: {e}")
        traceback.print_exc()


def handle_exception(exc_type, exc_value, exc_traceback):
    """全局异常处理"""
    print("发生未处理的异常:")
    traceback.print_exception(exc_type, exc_value, exc_traceback)

    # 尝试保存状态
    try:
        config_manager = ConfigManager()
        config_manager.save()
        print("已保存配置")
    except:
        pass

    sys.exit(1)


def check_qml_file(qml_path: Path) -> bool:
    """检查 QML 文件是否存在且可读"""
    if not qml_path.exists():
        print(f"错误: QML 文件不存在: {qml_path}")
        return False

    if not os.access(qml_path, os.R_OK):
        print(f"错误: 无法读取 QML 文件: {qml_path}")
        return False

    try:
        with open(qml_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if len(content) < 10:
                print(f"警告: QML 文件内容过短: {qml_path}")
        return True
    except Exception as e:
        print(f"错误: 无法读取 QML 文件内容: {e}")
        return False


def setup_application_style(app):
    """设置应用程序样式"""
    # 设置暗色主题
    from PySide6.QtGui import QPalette, QColor
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(30, 30, 30))
    palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(30, 30, 30))
    palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
    palette.setColor(QPalette.Text, QColor(255, 255, 255))
    palette.setColor(QPalette.Button, QColor(50, 50, 50))
    palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.Highlight, QColor(0, 122, 204))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)


def initialize_qml_engine():
    """初始化 QML 引擎"""
    engine = QQmlApplicationEngine()

    # 设置导入路径
    qml_dir_str = get_ui_path("qml")
    components_dir_str = get_ui_path("qml/components")

    engine.addImportPath(qml_dir_str)
    import os
    if os.path.exists(components_dir_str):
        engine.addImportPath(components_dir_str)
    engine.addImportPath(get_resource_path('.'))

    return engine


def main():
    """主函数"""
    # 设置全局异常处理
    sys.excepthook = handle_exception

    # 创建应用程序
    app = QApplication(sys.argv)
    app.setApplicationName("QuickLauncher")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("QuickLauncher")
    
    # 设置应用程序图标
    from utils.icon_utils import get_app_icon_path, ensure_app_icon_exists
    icon_path = get_app_icon_path()
    ensure_app_icon_exists(icon_path, app)  # 确保图标文件存在，并传入app实例
    
    # 设置应用程序图标，确保任务栏和托盘图标一致
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # 在Windows系统上设置AppUserModelID，确保任务栏图标正确显示
    if sys.platform == 'win32':
        try:
            import ctypes
            from ctypes import wintypes
            myappid = 'com.quicklauncher.app.1.0.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            
            # 同时为Windows应用设置适当的窗口属性，以确保任务栏按钮正常显示
            if hasattr(ctypes.windll.kernel32, "SetConsoleTitleW"):
                ctypes.windll.kernel32.SetConsoleTitleW("QuickLauncher")
        except AttributeError:
            pass  # Windows版本太老，不支持此功能
        except Exception as e:
            print(f"设置Windows应用属性时出错: {e}")

    # 设置应用程序样式
    setup_application_style(app)

    try:
        print("正在启动 QuickLauncher...")

        # 加载配置
        print("正在加载配置...")
        config_manager = ConfigManager()
        config_info = config_manager.get_config_info()
        print(f"配置文件: {config_info['config_file']}")
        print(f"应用数量: {config_info['app_count']}")

        quick_window_config = config_manager.quick_config

        # 设置开机自启
        setup_auto_start(quick_window_config.auto_start)

        # 初始化系统托盘
        print("正在初始化系统托盘...")
        tray_manager = SystemTrayManager()
        tray_manager.setup_tray(app_instance=app)

        # 初始化 QML 引擎
        engine = initialize_qml_engine()

        # 创建后端对象
        print("正在初始化后端...")
        main_window_backend = MainWindowBackend()
        quick_window_backend = QuickWindowBackend()

        # 注册到 QML 上下文
        engine.rootContext().setContextProperty("mainWindowBackend", main_window_backend)
        engine.rootContext().setContextProperty("quickWindowBackend", quick_window_backend)
        engine.rootContext().setContextProperty("trayManager", tray_manager)

        # 添加安全图标提供者
        print("正在初始化图标提供者...")
        icon_provider = SafeIconProvider()
        engine.addImageProvider("icon", icon_provider)

        # 加载主窗口 QML
        qml_path_str = get_qml_path("MainWindow.qml")
        qml_path = Path(qml_path_str)

        print(f"加载 QML 文件: {qml_path_str}")

        if not check_qml_file(qml_path):
            print("QML 文件检查失败")
            return -1

        # 加载 QML
        url = QUrl.fromLocalFile(qml_path_str)
        engine.load(url)

        # 检查是否成功加载
        if not engine.rootObjects():
            print("加载 QML 失败 - 没有根对象")
            # 在PySide6中，正确的获取QML错误信息的方法
            print("请检查QML文件语法是否正确")
            return -1

        print("应用程序启动成功")

        # 获取主窗口对象
        main_window = engine.rootObjects()[0]
        
        # 确保主窗口也具有正确的图标
        try:
            if os.path.exists(icon_path):
                main_window.setProperty("windowIcon", QIcon(icon_path))
                # 尝试直接设置窗口图标
                main_window.setIcon(QIcon(icon_path))
        except Exception as e:
            print(f"设置主窗口图标时出错: {e}")

        # 创建快捷窗口管理器
        print("正在初始化快捷窗口...")
        quick_engine = initialize_qml_engine()
        quick_window_manager = QuickWindowManager(quick_window_backend, main_window_backend, config_manager, tray_manager)
        quick_window_manager.setup_quick_window(quick_engine, icon_provider)
        
        # 确保快捷窗口也有正确的图标
        try:
            if os.path.exists(icon_path) and quick_window_manager.engine and quick_window_manager.engine.rootObjects():
                quick_window = quick_window_manager.engine.rootObjects()[0]
                # 设置快捷窗口图标
                quick_window.setProperty("windowIcon", QIcon(icon_path))
                
        except Exception as e:
            print(f"设置快捷窗口图标时出错: {e}")

        # 将快捷窗口管理器连接到主窗口后端
        main_window_backend.quick_window_manager = quick_window_manager

        # 连接系统托盘信号
        def show_main_window():
            """显示主窗口"""
            if main_window:
                main_window.show()
                main_window.raise_()
                main_window.requestActivate()
                # 更新菜单文本
                tray_manager.update_toggle_action_text()

        def hide_main_window():
            """隐藏主窗口"""
            if main_window:
                main_window.hide()
                # 更新菜单文本
                tray_manager.update_toggle_action_text()

        def toggle_main_window():
            """切换主窗口显示/隐藏"""
            if main_window:
                is_visible = main_window.property("visible")
                if is_visible:
                    main_window.hide()
                else:
                    main_window.show()
                    main_window.raise_()
                    main_window.requestActivate()
                # 更新菜单文本
                tray_manager.update_toggle_action_text()

        def show_quick_window():
            """显示快捷窗口"""
            quick_window_manager.show_window()
            tray_manager.show_message("快捷窗口", "快捷窗口已显示", QSystemTrayIcon.Information, 1000)

        def exit_application():
            """退出应用程序"""
            # 保存配置
            config_manager.save()
            
            # 隐藏托盘图标
            if tray_manager.tray_icon:
                tray_manager.tray_icon.hide()
            
            # 关闭快捷窗口
            if quick_window_manager.engine and quick_window_manager.engine.rootObjects():
                quick_window = quick_window_manager.engine.rootObjects()[0]
                quick_window.close()
            
            # 关闭主窗口
            if main_window:
                main_window.close()
            
            # 退出应用程序
            app.quit()

        # 设置主窗口引用
        tray_manager.set_main_window(main_window)
        
        # 连接托盘信号
        tray_manager.show_main_window.connect(show_main_window)
        tray_manager.hide_main_window.connect(hide_main_window)
        tray_manager.toggle_main_window.connect(toggle_main_window)
        tray_manager.show_quick_window.connect(show_quick_window)
        tray_manager.exit_app.connect(exit_application)

        # 连接托盘菜单功能到后端
        def refresh_app_list():
            main_window_backend.refresh_app_list()
            tray_manager.show_message("刷新", "应用列表已刷新", QSystemTrayIcon.Information, 1000)

        def cleanup_missing_apps():
            result = main_window_backend.cleanup_missing_apps()
            if result["success"]:
                tray_manager.show_message("清理完成", result.get("message", "清理完成"),
                                        QSystemTrayIcon.Information, 2000)

        # 获取托盘菜单并连接信号
        if tray_manager.menu:
            actions = tray_manager.menu.actions()
            for action in actions:
                if action.text() == "刷新应用列表":
                    action.triggered.disconnect()
                    action.triggered.connect(refresh_app_list)
                elif action.text() == "清理不存在应用":
                    action.triggered.disconnect()
                    action.triggered.connect(cleanup_missing_apps)

        # 主窗口关闭时最小化到托盘
        def on_window_closing():
            """窗口关闭事件处理"""
            main_window.hide()
            # 更新菜单文本
            tray_manager.update_toggle_action_text()
            tray_manager.show_message("QuickLauncher", "应用程序已最小化到系统托盘")
            return True

        # 连接窗口关闭事件
        try:
            main_window.closing.connect(on_window_closing)
        except:
            pass

        # 显示启动信息
        def show_startup_info():
            try:
                apps = main_window_backend.get_applications()
                print(f"已加载 {len(apps)} 个应用")

                # 根据配置决定是否显示快捷窗口
                if quick_window_config.show_on_startup:
                    print("快捷窗口已设置为启动时显示，正在显示快捷窗口...")
                    quick_window_manager.show_window()
                else:
                    print("快捷窗口未设置为启动时显示")

                # 根据主窗口配置决定是否显示主窗口
                # 如果是开机自启动，但设置了隐藏主窗口，则不显示
                current_main_window_config = config_manager.main_window_config
                if current_main_window_config.show_on_startup and not (current_main_window_config.auto_start and current_main_window_config.hide_on_startup_if_auto):
                    print("主窗口已设置为启动时显示，正在显示主窗口...")
                    main_window.show()
                    # 更新托盘菜单文本为"隐藏主窗口"
                    tray_manager.update_toggle_action_text()
                else:
                    print("主窗口已设置为启动时不显示或开机自启动时隐藏")
                    # 即使不显示主窗口，也要更新托盘菜单文本为"显示主窗口"
                    tray_manager.update_toggle_action_text()

            except Exception as e:
                print(f"启动信息显示失败: {e}")

        QTimer.singleShot(1000, show_startup_info)

        # 应用程序退出时保存配置
        def on_application_about_to_quit():
            print("应用程序即将退出，保存配置...")
            config_manager.save()

        app.aboutToQuit.connect(on_application_about_to_quit)

        # 启动内存监控
        start_global_monitoring()
        
        # 运行应用程序
        return app.exec()

    except Exception as e:
        print(f"启动失败: {e}")
        traceback.print_exc()
        return -1


if __name__ == "__main__":
    sys.exit(main())