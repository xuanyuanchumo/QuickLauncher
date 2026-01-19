# file: D:\Projects\PycharmProjects\QuickLauncher\core\icon_cache.py
"""
图标缓存管理器 - 优化完善版本
支持EXE、LNK等文件图标提取，自动缓存为PNG格式到cache/icons文件夹
"""

import os
import sys
import time
import hashlib
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, Any, List
from concurrent.futures import ThreadPoolExecutor
import threading
from datetime import datetime, timedelta

from PySide6.QtGui import QPixmap, QImage, QPainter, QColor, QPen, QFont, QIcon, QLinearGradient, QBrush
from PySide6.QtCore import Qt, QSize

# 配置日志
logger = logging.getLogger(__name__)


class IconCache:
    """图标缓存管理器 - 优化版本"""
    cache_dir0 = Path(__file__).parent.parent / "cache" / "icons"

    def __init__(self, max_size: int = 100, cache_dir: str = cache_dir0):
        self.max_size = max_size
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 缓存
        self.memory_cache: Dict[str, QPixmap] = {}
        self.access_order: List[str] = []
        self.cache_mutex = threading.RLock()
        
        # 内存监控
        self._estimated_memory_usage = 0
        self._max_memory_mb = 50  # 限制图标缓存占用的最大内存量(MB)

        # 文件类型颜色映射
        self.filetype_colors = {
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

        # 统计信息
        self.stats = {
            'total_requests': 0,
            'memory_hits': 0,
            'extractions': 0,
            'failed_extractions': 0,
            'start_time': time.time()
        }

        # 线程池
        self.thread_pool = ThreadPoolExecutor(max_workers=2)

        logger.info(f"图标缓存初始化完成: {self.cache_dir}")
        logger.info(f"内存缓存大小: {max_size}")

    def _get_cache_key(self, path: str, size: int) -> str:
        """生成缓存键"""
        try:
            abs_path = os.path.abspath(path).lower()

            # 获取文件修改时间
            mtime = 0
            if os.path.exists(path):
                try:
                    mtime = int(os.path.getmtime(path))
                except:
                    pass

            # 生成哈希
            key_data = f"{abs_path}_{size}_{mtime}"
            return hashlib.md5(key_data.encode('utf-8')).hexdigest()
        except Exception as e:
            logger.error(f"生成缓存键失败: {e}")
            return hashlib.md5(f"{path}_{size}".encode('utf-8')).hexdigest()

    def _get_disk_cache_path(self, key: str) -> Path:
        """获取磁盘缓存路径"""
        # 使用两级目录结构
        subdir = key[:2]
        return self.cache_dir / subdir / f"{key}.png"

    def _save_to_disk_cache(self, disk_path: Path, pixmap: QPixmap):
        """保存图标到磁盘缓存"""
        try:
            # 确保父目录存在
            disk_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存图标为PNG格式
            if not pixmap.isNull():
                success = pixmap.save(str(disk_path), "PNG", quality=90)
                if success:
                    logger.debug(f"图标已保存到磁盘缓存: {disk_path}")
                else:
                    logger.warning(f"保存图标到磁盘缓存失败: {disk_path}")
        except Exception as e:
            logger.error(f"保存图标到磁盘缓存异常: {e}")

    def _extract_icon_windows(self, path: str, size: int) -> Optional[QPixmap]:
        """Windows系统图标提取"""
        try:
            if sys.platform != 'win32':
                return None

            # 使用Qt内置方法提取图标，处理中文路径
            icon = QIcon(path)
            if not icon.isNull():
                pixmap = icon.pixmap(size, size)
                if not pixmap.isNull():
                    return pixmap

            # 尝试使用系统API，确保路径正确编码
            try:
                import ctypes
                from ctypes import wintypes

                # 定义常量
                SHGFI_ICON = 0x100
                SHGFI_LARGEICON = 0x0
                SHGFI_SMALLICON = 0x1
                SHGFI_USEFILEATTRIBUTES = 0x10

                class SHFILEINFO(ctypes.Structure):
                    _fields_ = [
                        ("hIcon", wintypes.HANDLE),
                        ("iIcon", ctypes.c_int),
                        ("dwAttributes", wintypes.DWORD),
                        ("szDisplayName", ctypes.c_wchar * 260),
                        ("szTypeName", ctypes.c_wchar * 80)
                    ]

                shell32 = ctypes.windll.shell32
                shfi = SHFILEINFO()

                flags = SHGFI_ICON | SHGFI_USEFILEATTRIBUTES
                if size <= 16:
                    flags |= SHGFI_SMALLICON
                else:
                    flags |= SHGFI_LARGEICON

                # 确保路径使用Unicode版本的API并正确处理中文字符
                result = shell32.SHGetFileInfoW(
                    ctypes.c_wchar_p(path),
                    0,
                    ctypes.byref(shfi),
                    ctypes.sizeof(shfi),
                    flags
                )

                if result and shfi.hIcon:
                    # 转换HICON为QPixmap
                    from PySide6.QtGui import QImage
                    image = QImage.fromHICON(shfi.hIcon)
                    if not image.isNull():
                        pixmap = QPixmap.fromImage(image)
                        if size != pixmap.width() or size != pixmap.height():
                            pixmap = pixmap.scaled(size, size,
                                                   Qt.AspectRatioMode.KeepAspectRatio,
                                                   Qt.TransformationMode.SmoothTransformation)
                        return pixmap
            except UnicodeDecodeError as e:
                logger.warning(f"Windows图标提取失败，路径包含无法解码的字符: {e}")
            except Exception as e:
                logger.debug(f"Windows图标提取失败: {e}")

        except Exception as e:
            logger.debug(f"Windows图标提取失败: {e}")

        return None

    def _extract_icon_linux(self, path: str, size: int) -> Optional[QPixmap]:
        """Linux系统图标提取"""
        try:
            # 尝试使用Qt内置方法
            icon = QIcon(path)
            if not icon.isNull():
                pixmap = icon.pixmap(size, size)
                if not pixmap.isNull():
                    return pixmap

            # 对于.desktop文件，尝试解析图标
            if path.endswith('.desktop'):
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for line in content.split('\n'):
                        if line.startswith('Icon='):
                            icon_name = line[5:].strip()
                            # 尝试从主题加载图标
                            icon = QIcon.fromTheme(icon_name)
                            if not icon.isNull():
                                pixmap = icon.pixmap(size, size)
                                if not pixmap.isNull():
                                    return pixmap
        except:
            pass

        return None

    def _extract_icon_mac(self, path: str, size: int) -> Optional[QPixmap]:
        """macOS系统图标提取"""
        try:
            # 使用Qt内置方法
            icon = QIcon(path)
            if not icon.isNull():
                pixmap = icon.pixmap(size, size)
                if not pixmap.isNull():
                    return pixmap

            # 对于.app包，尝试获取图标
            if path.endswith('.app'):
                icon_path = os.path.join(path, 'Contents', 'Resources', 'AppIcon.icns')
                if os.path.exists(icon_path):
                    icon = QIcon(icon_path)
                    if not icon.isNull():
                        pixmap = icon.pixmap(size, size)
                        if not pixmap.isNull():
                            return pixmap
        except:
            pass

        return None

    def _extract_icon(self, path: str, size: int) -> Optional[QPixmap]:
        """提取图标"""
        self.stats['extractions'] += 1

        try:
            # 根据系统选择提取方法
            if sys.platform == 'win32':
                pixmap = self._extract_icon_windows(path, size)
            elif sys.platform == 'darwin':
                pixmap = self._extract_icon_mac(path, size)
            else:
                pixmap = self._extract_icon_linux(path, size)

            if pixmap and not pixmap.isNull():
                return pixmap
            else:
                self.stats['failed_extractions'] += 1
                return None

        except Exception as e:
            self.stats['failed_extractions'] += 1
            logger.error(f"图标提取失败: {e}")
            return None

    def _create_filetype_icon(self, path: str, size: int) -> QPixmap:
        """创建文件类型图标"""
        try:
            ext = os.path.splitext(path)[1].lower()
            color = self.filetype_colors.get(ext, QColor(96, 125, 139))

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

            painter.end()
            return pixmap

        except Exception as e:
            logger.error(f"创建默认图标失败: {e}")
            pixmap = QPixmap(size, size)
            pixmap.fill(QColor(66, 133, 244))
            return pixmap

    def get_icon(self, path: str, size: int = 32) -> QPixmap:
        """获取图标 - 主要入口点"""
        with self.cache_mutex:
            self.stats['total_requests'] += 1

            # 清理路径
            clean_path = os.path.abspath(path.strip())
            cache_key = self._get_cache_key(clean_path, size)

            # 1. 检查内存缓存
            if cache_key in self.memory_cache:
                self.stats['memory_hits'] += 1
                pixmap = self.memory_cache[cache_key]

                # 更新访问顺序
                if cache_key in self.access_order:
                    self.access_order.remove(cache_key)
                self.access_order.append(cache_key)

                return pixmap

            # 2. 检查磁盘缓存
            disk_cache_path = self._get_disk_cache_path(cache_key)
            if disk_cache_path.exists():
                try:
                    # 从磁盘加载缓存的图标
                    pixmap = QPixmap(str(disk_cache_path))
                    if not pixmap.isNull():
                        # 添加到内存缓存
                        self._add_to_memory_cache(cache_key, pixmap)
                        return pixmap
                except Exception as e:
                    logger.warning(f"从磁盘加载缓存图标失败: {e}")

            # 3. 检查文件是否存在
            if not os.path.exists(clean_path):
                logger.warning(f"文件不存在: {clean_path}")
                pixmap = self._create_filetype_icon(clean_path, size)
                # 保存到磁盘缓存
                self._save_to_disk_cache(disk_cache_path, pixmap)
                self._add_to_memory_cache(cache_key, pixmap)
                return pixmap

            # 4. 提取图标
            pixmap = self._extract_icon(clean_path, size)

            # 5. 如果提取失败，创建文件类型图标
            if not pixmap or pixmap.isNull():
                pixmap = self._create_filetype_icon(clean_path, size)

            # 6. 调整大小
            if pixmap and (pixmap.width() != size or pixmap.height() != size):
                pixmap = pixmap.scaled(
                    size, size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )

            # 7. 缓存图标
            if pixmap and not pixmap.isNull():
                # 保存到磁盘缓存
                self._save_to_disk_cache(disk_cache_path, pixmap)
                self._add_to_memory_cache(cache_key, pixmap)

            return pixmap if pixmap else self._create_default_icon(size)

    def _estimate_pixmap_memory(self, pixmap: QPixmap) -> int:
        """估算QPixmap占用的内存大小（字节）"""
        if pixmap.isNull():
            return 0
        # 计算像素数量 * 每像素字节数 (RGBA = 4 bytes)
        return pixmap.width() * pixmap.height() * 4
    
    def _add_to_memory_cache(self, key: str, pixmap: QPixmap):
        """添加到内存缓存"""
        with self.cache_mutex:
            estimated_size = self._estimate_pixmap_memory(pixmap)
            
            if key in self.memory_cache:
                # 更新现有，调整内存使用估计
                old_pixmap = self.memory_cache[key]
                old_size = self._estimate_pixmap_memory(old_pixmap)
                self._estimated_memory_usage = self._estimated_memory_usage - old_size + estimated_size
                
                self.memory_cache[key] = pixmap
                if key in self.access_order:
                    self.access_order.remove(key)
                self.access_order.append(key)
            else:
                # 检查缓存大小限制
                while (len(self.memory_cache) >= self.max_size or 
                       (self._estimated_memory_usage + estimated_size) > (self._max_memory_mb * 1024 * 1024)):
                    # LRU淘汰
                    if self.access_order:
                        oldest_key = self.access_order.pop(0)
                        if oldest_key in self.memory_cache:
                            old_pixmap = self.memory_cache[oldest_key]
                            old_size = self._estimate_pixmap_memory(old_pixmap)
                            self._estimated_memory_usage -= old_size
                            del self.memory_cache[oldest_key]
                    else:
                        break

                # 添加新缓存
                self.memory_cache[key] = pixmap
                self.access_order.append(key)
                self._estimated_memory_usage += estimated_size

    def clear_cache(self, memory_only: bool = False) -> bool:
        """清理缓存"""
        try:
            with self.cache_mutex:
                # 清理内存缓存
                self.memory_cache.clear()
                self.access_order.clear()
                self._estimated_memory_usage = 0  # 重置内存使用估计

                if not memory_only:
                    # 清理磁盘缓存
                    import shutil
                    if self.cache_dir.exists():
                        shutil.rmtree(self.cache_dir)
                        self.cache_dir.mkdir(parents=True, exist_ok=True)

                # 重置统计
                self.stats = {
                    'total_requests': 0,
                    'memory_hits': 0,
                    'extractions': 0,
                    'failed_extractions': 0,
                    'start_time': time.time()
                }

                logger.info(f"缓存已清理 (内存{'仅' if memory_only else '和磁盘'})")
                return True

        except Exception as e:
            logger.error(f"清理缓存失败: {e}")
            return False

    def cleanup_old_cache(self, max_age_days: int = 7, max_size_mb: int = 500) -> int:
        """清理旧的和过大的缓存"""
        try:
            cleaned_count = 0
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 3600

            # 计算当前缓存大小
            total_size = 0
            cache_files = []

            for file in self.cache_dir.rglob("*.png"):
                if file.is_file():
                    try:
                        file_size = file.stat().st_size
                        total_size += file_size
                        cache_files.append((file, file_size, file.stat().st_mtime))
                    except:
                        pass

            # 按修改时间排序
            cache_files.sort(key=lambda x: x[2])

            # 清理旧文件
            for file, file_size, mtime in cache_files:
                if current_time - mtime > max_age_seconds:
                    try:
                        file.unlink()
                        cleaned_count += 1
                        total_size -= file_size
                    except Exception as e:
                        logger.warning(f"删除旧缓存文件失败: {e}")

            # 如果仍然太大，继续清理最旧的文件
            max_size_bytes = max_size_mb * 1024 * 1024
            if total_size > max_size_bytes:
                for file, file_size, mtime in cache_files:
                    if file.exists():  # 可能已经被删除
                        try:
                            file.unlink()
                            cleaned_count += 1
                            total_size -= file_size

                            if total_size <= max_size_bytes:
                                break
                        except Exception as e:
                            logger.warning(f"删除大缓存文件失败: {e}")

            # 清理空目录
            for dir_path in list(self.cache_dir.rglob("*")):
                if dir_path.is_dir() and not any(dir_path.iterdir()):
                    try:
                        dir_path.rmdir()
                    except:
                        pass

            logger.info(f"清理了 {cleaned_count} 个缓存文件")
            return cleaned_count

        except Exception as e:
            logger.error(f"清理旧缓存失败: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.cache_mutex:
            total_time = time.time() - self.stats['start_time']

            # 计算命中率
            memory_hit_rate = 0
            if self.stats['total_requests'] > 0:
                memory_hit_rate = (self.stats['memory_hits'] / self.stats['total_requests'] * 100)

            # 计算提取成功率
            extraction_success_rate = 0
            if self.stats['extractions'] > 0:
                extraction_success_rate = ((self.stats['extractions'] - self.stats['failed_extractions']) /
                                           self.stats['extractions'] * 100)

            return {
                'memory_cache': {
                    'size': len(self.memory_cache),
                    'max_size': self.max_size,
                    'hits': self.stats['memory_hits'],
                    'hit_rate': round(memory_hit_rate, 2)
                },
                'extractions': {
                    'total': self.stats['extractions'],
                    'failed': self.stats['failed_extractions'],
                    'success_rate': round(extraction_success_rate, 2)
                },
                'performance': {
                    'total_requests': self.stats['total_requests'],
                    'requests_per_second': round(self.stats['total_requests'] / total_time, 2) if total_time > 0 else 0,
                    'uptime_hours': round(total_time / 3600, 2)
                },
                'cache_dir': str(self.cache_dir)
            }

    def preload_icons(self, paths: List[str], sizes: Optional[List[int]] = None):
        """预加载图标"""
        if sizes is None:
            sizes = [ 32, 48, 64]

        for path in paths:
            if os.path.exists(path):
                for size in sizes:
                    # 异步预加载
                    self.thread_pool.submit(self.get_icon, path, size)

        logger.info(f"开始预加载 {len(paths) * len(sizes)} 个图标")

    def export_icon(self, path: str, output_path: str, size: int = 256) -> bool:
        """导出图标到文件"""
        try:
            pixmap = self.get_icon(path, size)
            if pixmap and not pixmap.isNull():
                # 确保输出目录存在
                output_dir = Path(output_path).parent
                output_dir.mkdir(parents=True, exist_ok=True)

                # 保存为PNG
                success = pixmap.save(output_path, "PNG", quality=100)
                if success:
                    logger.info(f"图标已导出: {output_path}")
                return success
            return False
        except Exception as e:
            logger.error(f"导出图标失败: {e}")
            return False

    def shutdown(self):
        """关闭图标缓存，清理资源"""
        try:
            self.thread_pool.shutdown(wait=True)
            logger.info("图标缓存已关闭")
        except Exception as e:
            logger.error(f"关闭图标缓存失败: {e}")