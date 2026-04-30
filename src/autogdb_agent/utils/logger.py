"""
Logger - 日志工具
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional

from ..core.config import Config


def get_logger(name: str, config: Optional[Config] = None) -> logging.Logger:
    """
    获取日志记录器

    Args:
        name: 日志记录器名称
        config: 配置对象

    Returns:
        日志记录器实例
    """
    logger = logging.getLogger(name)

    # 如果已经有处理器，直接返回
    if logger.handlers:
        return logger

    # 从配置获取日志设置
    if config:
        log_level = config.get("debug.log_level", "INFO")
        log_file = config.get("debug.log_file")
        max_size = config.get("debug.max_log_size", "100MB")
        backup_count = config.get("debug.backup_count", 5)
    else:
        log_level = "INFO"
        log_file = None
        max_size = "100MB"
        backup_count = 5

    # 设置日志级别
    logger.setLevel(getattr(logging, log_level.upper()))

    # 创建格式化器
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器
    if log_file:
        # 展开环境变量
        log_file = os.path.expanduser(log_file)
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # 解析文件大小
        size_bytes = parse_size(max_size)

        # 使用RotatingFileHandler
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=size_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def parse_size(size_str: str) -> int:
    """
    解析大小字符串为字节数

    Args:
        size_str: 大小字符串，如 "100MB", "1GB"

    Returns:
        字节数
    """
    size_str = size_str.upper()
    if size_str.endswith("KB"):
        return int(size_str[:-2]) * 1024
    elif size_str.endswith("MB"):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith("GB"):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    else:
        return int(size_str)