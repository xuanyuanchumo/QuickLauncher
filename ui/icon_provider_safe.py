# file: D:\Projects\PycharmProjects\QuickLauncher\ui\icon_provider_safe.py
"""
安全图标提供者 - 使用优化后的图标缓存
支持EXE、LNK等文件图标提取，自动缓存为PNG到cache/icons文件夹
"""

import sys
import os
import time
import urllib.parse
import threading
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from PySide6.QtQuick import QQuickImageProvider
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QFont, QLinearGradient, QBrush
from PySide6.QtCore import Qt, QSize, QRect, QObject, Signal, Slot

# 导入资源路径处理工具
from utils.resource_path import get_cache_path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
#缓存目录
cache_dir0 = Path(get_cache_path("icons"))

class IconProviderSignals(QObject):
    """图标提供者信号"""
    cacheCleared = Signal()
    statsUpdated = Signal(dict)
    errorOccurred = Signal(str)


class SafeIconProvider(QQuickImageProvider):
    """安全图标提供者 - 优化版本"""


    def __init__(self, cache_dir: str = cache_dir0):
        super().__init__(QQuickImageProvider.Pixmap)

        # 初始化信号
        self.signals = IconProviderSignals()

        # 动态导入图标缓存
        try:
            from core.icon_cache import IconCache
            self.cache = IconCache(max_size=50, cache_dir=cache_dir)  # 减少缓存大小以节省内存
            self.cache_available = True
        except ImportError as e:
            logger.error(f"图标缓存模块导入失败: {e}")
            self.cache_available = False
            self.cache = None

        # 性能统计
        self.stats = {
            'total_requests': 0,
            'successful': 0,
            'failed': 0,
            'cache_hits': 0,
            'avg_response_time': 0,
            'start_time': time.time()
        }
        self.response_times = []

        # 请求队列（用于去重）
        self.pending_requests = set()
        self.request_lock = threading.Lock()

        logger.info(f"安全图标提供者初始化完成 - 缓存可用: {self.cache_available}")
        logger.info(f"缓存目录: {cache_dir}")

    def requestPixmap(self, id: str, size: QSize, requestedSize: QSize) -> QPixmap:
        """处理图标请求 - Qt Quick调用"""
        request_start = time.time()

        # 更新统计
        self.stats['total_requests'] += 1

        try:
            # 解码路径
            file_path = self._decode_request_id(id)

            if not file_path:
                logger.warning(f"无效的图标请求ID: {id}")
                self.stats['failed'] += 1
                return self._create_error_icon(requestedSize)

            # 确定图标大小
            icon_size = self._determine_icon_size(size, requestedSize)

            # 检查是否在请求中（防止重复请求）
            request_key = f"{file_path}_{icon_size}"
            with self.request_lock:
                if request_key in self.pending_requests:
                    # 正在请求中，返回加载中图标
                    return self._create_loading_icon(icon_size)
                self.pending_requests.add(request_key)

            try:
                # 获取图标
                if self.cache_available and self.cache:
                    pixmap = self.cache.get_icon(file_path, icon_size)
                else:
                    # 缓存不可用时使用备用方法
                    pixmap = self._create_backup_icon(file_path, icon_size)

                if pixmap and not pixmap.isNull():
                    self.stats['successful'] += 1

                    # 记录响应时间
                    response_time = time.time() - request_start
                    self.response_times.append(response_time)
                    if len(self.response_times) > 100:
                        self.response_times.pop(0)

                    if self.response_times:
                        self.stats['avg_response_time'] = sum(self.response_times) / len(self.response_times)

                    # 定期记录性能
                    if self.stats['total_requests'] % 100 == 0:
                        self._log_performance_stats()

                    return pixmap
                else:
                    self.stats['failed'] += 1
                    logger.warning(f"无法获取图标: {file_path}")
                    return self._create_filetype_icon(file_path, icon_size)

            finally:
                with self.request_lock:
                    self.pending_requests.discard(request_key)

        except Exception as e:
            self.stats['failed'] += 1
            logger.error(f"图标请求失败: {e}")
            self.signals.errorOccurred.emit(str(e))
            return self._create_error_icon(requestedSize)

    def _decode_request_id(self, id_str: str) -> Optional[str]:
        """解码请求ID为文件路径"""
        try:
            # 移除URL编码，使用UTF-8编码处理中文字符
            decoded = urllib.parse.unquote(id_str, encoding='utf-8')

            # 移除可能的image://icon/前缀
            if decoded.startswith("image://icon/"):
                decoded = decoded[len("image://icon/"):]
            elif decoded.startswith("file:///"):
                decoded = decoded[len("file:///"):]
            elif decoded.startswith("file://"):
                decoded = decoded[len("file://"):]

            # 处理Windows路径
            if sys.platform == 'win32':
                # 移除开头的斜杠
                if decoded.startswith('/'):
                    decoded = decoded[1:]
                # 统一路径分隔符
                decoded = decoded.replace('/', '\\')
                # 处理网络路径
                if decoded.startswith('\\\\'):
                    decoded = '\\\\' + decoded[2:].replace('/', '\\')
            else:
                decoded = decoded.replace('\\', '/')

            # 清理路径
            decoded = decoded.strip()

            # 检查是否为绝对路径
            if os.path.isabs(decoded):
                # 使用原始路径检查是否存在，确保中文路径正确处理
                if os.path.exists(decoded):
                    return decoded
                else:
                    # 尝试在系统路径中查找
                    return self._find_in_system_path(decoded)

            # 相对路径
            abs_path = os.path.abspath(decoded)
            if os.path.exists(abs_path):
                return abs_path

            return None

        except UnicodeDecodeError as e:
            logger.error(f"解码请求ID失败，路径包含无法解码的字符: {id_str}, 错误: {e}")
            return None
        except Exception as e:
            logger.error(f"解码请求ID失败: {id_str}, 错误: {e}")
            return None

    def _find_in_system_path(self, filename: str) -> Optional[str]:
        """在系统路径中查找文件"""
        try:
            # 如果是完整路径但不存在，尝试仅用文件名查找
            basename = os.path.basename(filename)

            # 检查常见系统目录
            system_dirs = []
            if sys.platform == 'win32':
                system_dirs = [
                    os.environ.get("SystemRoot", r"C:\Windows"),
                    os.environ.get("SystemRoot", r"C:\Windows") + r"\System32",
                    os.environ.get("ProgramFiles", r"C:\Program Files"),
                    os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
                ]
            else:
                system_dirs = [
                    "/usr/bin",
                    "/usr/local/bin",
                    "/usr/share/applications",
                    os.path.expanduser("~/.local/share/applications")
                ]

            for sys_dir in system_dirs:
                if os.path.exists(sys_dir):
                    potential_path = os.path.join(sys_dir, basename)
                    if os.path.exists(potential_path):
                        return potential_path

            # 在PATH环境变量中查找
            path_dirs = os.environ.get("PATH", "").split(os.pathsep)
            for path_dir in path_dirs:
                if path_dir:
                    potential_path = os.path.join(path_dir, basename)
                    if os.path.exists(potential_path):
                        return potential_path

            return None
        except Exception as e:
            logger.debug(f"系统路径查找失败: {e}")
            return None

    def _determine_icon_size(self, size: QSize, requestedSize: QSize) -> int:
        """确定图标大小"""
        # 优先级：requestedSize > size > 默认32

        if requestedSize.isValid():
            # 使用请求的大小
            if requestedSize.width() > 0 and requestedSize.height() > 0:
                return min(requestedSize.width(), requestedSize.height())
            elif requestedSize.width() > 0:
                return requestedSize.width()
            elif requestedSize.height() > 0:
                return requestedSize.height()

        if size.isValid():
            # 使用size参数
            if size.width() > 0 and size.height() > 0:
                return min(size.width(), size.height())
            elif size.width() > 0:
                return size.width()
            elif size.height() > 0:
                return size.height()

        # 默认大小
        return 32

    def _create_backup_icon(self, path: str, size: int) -> QPixmap:
        """创建备用图标（当缓存不可用时）"""
        try:
            # 尝试使用Qt内置方法
            from PySide6.QtGui import QIcon
            icon = QIcon(path)
            if not icon.isNull():
                pixmap = icon.pixmap(size, size)
                if not pixmap.isNull():
                    return pixmap

            # 创建文件类型图标
            return self._create_filetype_icon(path, size)
        except Exception as e:
            logger.error(f"创建备用图标失败: {e}")
            return self._create_default_icon(size)

    def _create_loading_icon(self, size: int) -> QPixmap:
        """创建加载中图标"""
        try:
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # 绘制背景
            gradient = QLinearGradient(0, 0, size, size)
            gradient.setColorAt(0, QColor(240, 240, 240, 200))
            gradient.setColorAt(1, QColor(220, 220, 220, 200))

            margin = max(2, size // 16)
            rect = pixmap.rect().adjusted(margin, margin, -margin, -margin)

            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, size // 8, size // 8)

            # 绘制加载动画（旋转圆点）
            import time
            current_time = time.time()
            angle = (current_time * 360) % 360

            dot_size = size // 8
            center = rect.center()
            radius = rect.width() // 3

            painter.setBrush(QColor(66, 133, 244, 200))

            for i in range(4):
                dot_angle = angle + (i * 90)
                rad = dot_angle * 3.14159 / 180
                x = center.x() + radius * (rad.cos())
                y = center.y() + radius * (rad.sin())

                dot_rect = QRect(
                    int(x - dot_size // 2),
                    int(y - dot_size // 2),
                    dot_size, dot_size
                )
                painter.drawEllipse(dot_rect)

            # 绘制"加载中"文字
            if size >= 32:
                font = QFont()
                font.setPixelSize(max(size // 6, 8))
                font.setBold(True)
                painter.setFont(font)
                painter.setPen(QColor(100, 100, 100, 200))
                painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "...")

            painter.end()
            return pixmap

        except Exception as e:
            logger.error(f"创建加载图标失败: {e}")
            return self._create_default_icon(size)

    def _create_filetype_icon(self, path: str, size: int) -> QPixmap:
        """创建文件类型图标"""
        try:
            # 文件类型颜色映射
            filetype_colors = {
                '.exe': QColor(0, 120, 215),  # Windows蓝
                '.lnk': QColor(255, 165, 0),  # 橙色
                '.msi': QColor(16, 124, 16),  # 深绿
                '.dll': QColor(106, 0, 95),  # 紫红
                '.sys': QColor(178, 0, 32),  # 深红
                '.bat': QColor(64, 64, 64),  # 深灰
                '.cmd': QColor(64, 64, 64),
                '.ps1': QColor(0, 51, 153),  # PowerShell蓝
                '.zip': QColor(251, 140, 0),
                '.rar': QColor(251, 140, 0),
                '.7z': QColor(251, 140, 0),
                '.iso': QColor(139, 195, 74),  # 浅绿
            }

            ext = os.path.splitext(path)[1].lower()
            color = filetype_colors.get(ext, QColor(96, 125, 139))

            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # 绘制背景
            margin = max(2, size // 16)
            rect = pixmap.rect().adjusted(margin, margin, -margin, -margin)

            # 创建渐变
            gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
            gradient.setColorAt(0, color.lighter(120))
            gradient.setColorAt(1, color.darker(120))

            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, size // 8, size // 8)

            # 绘制扩展名
            if ext and len(ext) > 1:
                ext_text = ext[1:].upper()
                if len(ext_text) > 4:
                    ext_text = ext_text[:4]

                font = QFont()
                font.setPixelSize(max(size // 3, 8))
                font.setBold(True)
                painter.setFont(font)
                painter.setPen(QColor(255, 255, 255))

                painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, ext_text)

            painter.end()
            return pixmap

        except Exception as e:
            logger.error(f"创建文件类型图标失败: {e}")
            return self._create_default_icon(size)

    def _create_default_icon(self, size: int) -> QPixmap:
        """创建默认图标"""
        try:
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # 绘制背景
            gradient = QLinearGradient(0, 0, size, size)
            gradient.setColorAt(0, QColor(66, 133, 244, 180))
            gradient.setColorAt(1, QColor(26, 115, 232, 180))

            margin = max(2, size // 16)
            rect = pixmap.rect().adjusted(margin, margin, -margin, -margin)

            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, size // 8, size // 8)

            # 绘制应用图标
            painter.setPen(QPen(QColor(255, 255, 255), max(1, size // 32)))
            painter.setBrush(QColor(255, 255, 255, 100))

            # 绘制窗口
            inner_margin = size // 6
            inner_rect = rect.adjusted(inner_margin, inner_margin, -inner_margin, -inner_margin)
            painter.drawRoundedRect(inner_rect, size // 16, size // 16)

            painter.end()
            return pixmap

        except Exception as e:
            logger.error(f"创建默认图标失败: {e}")
            pixmap = QPixmap(size, size)
            pixmap.fill(QColor(66, 133, 244))
            return pixmap

    def _create_error_icon(self, size: QSize) -> QPixmap:
        """创建错误图标"""
        icon_size = 32
        if size.isValid():
            icon_size = min(size.width(), size.height()) if size.width() > 0 and size.height() > 0 else 32

        try:
            pixmap = QPixmap(icon_size, icon_size)
            pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # 绘制背景
            gradient = QLinearGradient(0, 0, icon_size, icon_size)
            gradient.setColorAt(0, QColor(244, 67, 54, 180))
            gradient.setColorAt(1, QColor(211, 47, 47, 180))

            margin = max(2, icon_size // 16)
            rect = pixmap.rect().adjusted(margin, margin, -margin, -margin)

            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, icon_size // 8, icon_size // 8)

            # 绘制感叹号
            painter.setPen(QPen(QColor(255, 255, 255), max(2, icon_size // 16)))
            painter.setBrush(Qt.BrushStyle.NoBrush)

            # 绘制感叹号竖线
            line_x = rect.center().x()
            line_top = rect.top() + rect.height() // 4
            line_bottom = rect.bottom() - rect.height() // 4
            painter.drawLine(line_x, line_top, line_x, line_bottom)

            # 绘制感叹号点
            dot_radius = max(2, icon_size // 32)
            painter.setBrush(QColor(255, 255, 255))
            painter.drawEllipse(
                line_x - dot_radius,
                line_bottom + dot_radius,
                dot_radius * 2,
                dot_radius * 2
            )

            painter.end()
            return pixmap

        except Exception as e:
            logger.error(f"创建错误图标失败: {e}")
            pixmap = QPixmap(icon_size, icon_size)
            pixmap.fill(QColor(244, 67, 54))
            return pixmap

    def _log_performance_stats(self):
        """记录性能统计"""
        try:
            cache_stats = {}
            if self.cache_available and self.cache:
                cache_stats = self.cache.get_stats()

            logger.info(f"图标提供者性能统计:")
            logger.info(f"  总请求数: {self.stats['total_requests']}")
            if self.stats['total_requests'] > 0:
                success_rate = (self.stats['successful'] / self.stats['total_requests'] * 100)
                logger.info(f"  成功: {self.stats['successful']} ({success_rate:.1f}%)")
            logger.info(f"  失败: {self.stats['failed']}")
            logger.info(f"  平均响应时间: {self.stats['avg_response_time']:.3f}s")

            # 发出统计更新信号
            combined_stats = {
                'provider': self.stats.copy(),
                'cache': cache_stats
            }
            self.signals.statsUpdated.emit(combined_stats)

        except Exception as e:
            logger.error(f"记录性能统计失败: {e}")

    @Slot()
    def clear_cache(self):
        """清理缓存"""
        try:
            if self.cache_available and self.cache:
                self.cache.clear_cache()
            self.signals.cacheCleared.emit()
            logger.info("图标缓存已清空")
        except Exception as e:
            logger.error(f"清空缓存失败: {e}")
            self.signals.errorOccurred.emit(f"清空缓存失败: {e}")

    @Slot()
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            provider_stats = self.stats.copy()
            cache_stats = {}
            if self.cache_available and self.cache:
                cache_stats = self.cache.get_stats()

            # 计算总体成功率
            total_requests = self.stats['total_requests']
            successful = self.stats['successful']
            success_rate = (successful / total_requests * 100) if total_requests > 0 else 0

            return {
                'provider': {
                    'total_requests': provider_stats['total_requests'],
                    'successful_requests': provider_stats['successful'],
                    'failed_requests': provider_stats['failed'],
                    'success_rate': round(success_rate, 2),
                    'average_response_time': round(provider_stats['avg_response_time'], 3)
                },
                'cache': cache_stats,
                'performance': {
                    'uptime_hours': round((time.time() - self.stats['start_time']) / 3600, 2)
                }
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}

    @Slot(str, int, str)
    def export_icon(self, file_path: str, size: int, output_path: str) -> bool:
        """导出图标到文件"""
        try:
            if self.cache_available and self.cache:
                success = self.cache.export_icon(file_path, output_path, size)
                if success:
                    logger.info(f"图标已导出: {output_path}")
                return success
            return False
        except Exception as e:
            logger.error(f"导出图标失败: {e}")
            self.signals.errorOccurred.emit(f"导出图标失败: {e}")
            return False

    @Slot(list, list)
    def preload_icons(self, file_paths: list, sizes: list = None):
        """预加载图标"""
        try:
            if sizes is None:
                sizes = [48]  # 仅预加载最常用尺寸以节省内存

            if self.cache_available and self.cache:
                self.cache.preload_icons(file_paths, sizes)
                logger.info(f"预加载了 {len(file_paths)} 个文件的图标")
        except Exception as e:
            logger.error(f"预加载图标失败: {e}")
            self.signals.errorOccurred.emit(f"预加载图标失败: {e}")

    @Slot(int, int)
    def cleanup_cache(self, max_age_days: int = 7, max_size_mb: int = 500):
        """清理缓存"""
        try:
            cleaned = 0
            if self.cache_available and self.cache:
                cleaned = self.cache.cleanup_old_cache(max_age_days, max_size_mb)

            logger.info(f"清理了 {cleaned} 个缓存文件")

            # 发出信号
            self.signals.statsUpdated.emit(self.get_statistics())
        except Exception as e:
            logger.error(f"清理缓存失败: {e}")
            self.signals.errorOccurred.emit(f"清理缓存失败: {e}")

    @Slot()
    def shutdown(self):
        """关闭图标提供者"""
        try:
            if self.cache_available and self.cache:
                self.cache.shutdown()
            logger.info("图标提供者已关闭")
        except Exception as e:
            logger.error(f"关闭图标提供者失败: {e}")


def register_icon_provider(engine, cache_dir: str = cache_dir0):
    """注册图标提供者到Qt Quick引擎"""
    try:
        provider = SafeIconProvider(cache_dir)

        # 注册提供者
        engine.addImageProvider("icon", provider)

        # 将提供者暴露给QML
        engine.rootContext().setContextProperty("iconProvider", provider.signals)

        logger.info("图标安全提供者已注册到Qt Quick引擎")
        return provider
    except Exception as e:
        logger.error(f"注册图标提供者失败: {e}")
        return None