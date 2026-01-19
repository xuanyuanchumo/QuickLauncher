"""
日志配置工具
用于统一配置应用日志
"""

import logging
import os
from pathlib import Path


def setup_logger(name: str = __name__, log_file: str = None, level: int = logging.DEBUG) -> logging.Logger:
    """
    设置日志记录器
    :param name: 记录器名称
    :param log_file: 日志文件路径
    :param level: 日志级别
    :return: 配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # 创建格式器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    # 添加处理器到记录器
    logger.addHandler(console_handler)

    # 如果指定了日志文件，则添加文件处理器
    if log_file:
        # 确保日志目录存在
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_app_logger(name: str = "QuickLauncher") -> logging.Logger:
    """
    获取应用主日志记录器
    :param name: 记录器名称
    :return: 应用主日志记录器
    """
    # 设置日志文件路径
    log_file = Path(__file__).parent.parent /"cache"/ "logs" / "quicklauncher.log"
    
    # 确保日志目录存在
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    return setup_logger(name, str(log_file))


# 全局日志记录器
app_logger = get_app_logger()