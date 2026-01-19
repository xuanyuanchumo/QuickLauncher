"""
内存监控工具
用于监控QuickLauncher的内存使用情况
"""

import psutil
import os
import time
import threading
from typing import Dict, Callable
import logging

# 配置日志
logger = logging.getLogger(__name__)

class MemoryMonitor:
    """内存监控器"""
    
    def __init__(self, check_interval: int = 30):
        """
        初始化内存监控器
        :param check_interval: 检查间隔（秒）
        """
        self.check_interval = check_interval
        self.process = psutil.Process(os.getpid())
        self.monitoring = False
        self.callbacks = []
        
    def add_callback(self, callback: Callable[[Dict], None]):
        """添加内存使用回调函数"""
        self.callbacks.append(callback)
        
    def get_memory_info(self) -> Dict:
        """获取内存使用信息"""
        try:
            # 获取进程内存信息
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()
            
            # 获取系统整体内存信息
            system_memory = psutil.virtual_memory()
            
            return {
                'process_rss': memory_info.rss,  # 实际物理内存使用量
                'process_vms': memory_info.vms,  # 虚拟内存使用量
                'process_memory_percent': memory_percent,
                'system_total': system_memory.total,
                'system_available': system_memory.available,
                'system_used': system_memory.used,
                'system_percent': system_memory.percent,
                'timestamp': time.time()
            }
        except Exception as e:
            logger.error(f"获取内存信息失败: {e}")
            return {}
    
    def log_memory_info(self):
        """记录内存使用信息"""
        mem_info = self.get_memory_info()
        if mem_info:
            logger.info(f"内存使用 - 进程RSS: {mem_info['process_rss']/1024/1024:.2f}MB, "
                       f"进程占比: {mem_info['process_memory_percent']:.2f}%, "
                       f"系统占比: {mem_info['system_percent']:.2f}%")
    
    def start_monitoring(self):
        """开始监控"""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.log_memory_info()  # 立即记录一次
        
        def monitor_loop():
            while self.monitoring:
                try:
                    mem_info = self.get_memory_info()
                    if mem_info:
                        # 调用所有回调
                        for callback in self.callbacks:
                            try:
                                callback(mem_info)
                            except Exception as e:
                                logger.error(f"内存监控回调执行失败: {e}")
                                
                        # 如果内存使用过高，记录警告
                        if mem_info['process_memory_percent'] > 80:
                            logger.warning(f"内存使用过高: {mem_info['process_memory_percent']:.2f}%")
                            
                    time.sleep(self.check_interval)
                except Exception as e:
                    logger.error(f"内存监控循环出错: {e}")
                    time.sleep(self.check_interval)
        
        # 在后台线程中运行监控
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False

# 全局内存监控器实例
_memory_monitor = None

def get_memory_monitor() -> MemoryMonitor:
    """获取全局内存监控器实例"""
    global _memory_monitor
    if _memory_monitor is None:
        _memory_monitor = MemoryMonitor()
    return _memory_monitor

def start_global_monitoring():
    """启动全局内存监控"""
    monitor = get_memory_monitor()
    monitor.start_monitoring()
    logger.info("内存监控已启动")

def stop_global_monitoring():
    """停止全局内存监控"""
    global _memory_monitor
    if _memory_monitor:
        _memory_monitor.stop_monitoring()
        _memory_monitor = None
        logger.info("内存监控已停止")

# 内存优化建议
MEMORY_OPTIMIZATION_TIPS = [
    "减少图标缓存大小",
    "及时清理不用的对象",
    "使用生成器而非列表存储大量数据",
    "定期清理缓存",
    "优化QML组件的内存使用",
    "减少不必要的全局变量"
]

def suggest_optimizations(mem_info: Dict):
    """根据内存使用情况提供建议"""
    if not mem_info:
        return
        
    suggestions = []
    
    if mem_info['process_memory_percent'] > 70:
        suggestions.extend([
            "内存使用较高，考虑清理缓存",
            "检查是否有内存泄漏"
        ])
        
    if mem_info['system_percent'] > 85:
        suggestions.append("系统内存紧张，考虑优化整体内存使用")
        
    if suggestions:
        logger.warning(f"内存优化建议: {', '.join(suggestions)}")

# 注册优化建议回调
def init_memory_monitoring():
    """初始化内存监控"""
    monitor = get_memory_monitor()
    monitor.add_callback(suggest_optimizations)
    return monitor