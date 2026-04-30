"""
Helpers - 辅助函数
"""

import os
import re
import subprocess
import time
from typing import Any, Dict, List, Optional, Union


def expand_vars(text: str) -> str:
    """
    展开环境变量
    支持 ${VAR} 和 $VAR 格式

    Args:
        text: 包含环境变量的文本

    Returns:
        展开后的文本
    """
    def replace_var(match):
        var = match.group(1) or match.group(2)
        return os.environ.get(var, match.group(0))

    return re.sub(r'\$\{(\w+)\}|(\$)(\w+)', replace_var, text)


def safe_eval(expr: str) -> Any:
    """
    安全地评估表达式

    Args:
        expr: 要评估的表达式

    Returns:
        评估结果

    Raises:
        ValueError: 表达式不安全
    """
    # 不允许的字符和函数
    blacklist = [
        "__", "import", "exec", "eval", "open", "file", "globals",
        "locals", "vars", "dir", "help", "copyright", "credits",
        "license", "abs", "bytes", "chr", "complex", "dict", "dir",
        "divmod", "enumerate", "filter", "float", "frozenset", "hasattr",
        "hash", "hex", "id", "int", "isinstance", "issubclass", "iter",
        "len", "list", "map", "max", "min", "next", "oct", "ord", "pow",
        "print", "range", "repr", "reversed", "round", "set", "slice",
        "sorted", "str", "sum", "tuple", "type", "zip",
    ]

    # 检查黑名单
    for item in blacklist:
        if item in expr:
            raise ValueError(f"不安全的表达式: {item}")

    # 只允许基本运算
    allowed_chars = set(
        "0123456789+-*/.() \t\n"
        "'\""
        "[]"
    )
    if not all(c in allowed_chars for c in expr):
        raise ValueError("表达式包含不允许的字符")

    # 使用ast.literal_eval的安全子集
    try:
        # 简单的数学表达式
        return eval(expr, {"__builtins__": {}}, {})
    except:
        raise ValueError("表达式评估失败")


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小

    Args:
        size_bytes: 字节数

    Returns:
        格式化后的字符串
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)

    while size >= 1024 and i < len(size_names) - 1:
        size /= 1024
        i += 1

    return f"{size:.2f} {size_names[i]}"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本

    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 后缀

    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def run_command(
    command: Union[str, List[str]],
    timeout: Optional[int] = None,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    运行命令

    Args:
        command: 命令
        timeout: 超时时间（秒）
        cwd: 工作目录
        env: 环境变量

    Returns:
        结果字典
    """
    if isinstance(command, str):
        command = command.split()

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env=env or os.environ,
        )

        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": " ".join(command),
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": f"Command timed out after {timeout} seconds",
            "command": " ".join(command),
        }
    except Exception as e:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "command": " ".join(command),
        }


def wait_for_condition(
    condition_func,
    timeout: float = 30,
    interval: float = 0.1,
    timeout_message: str = "Condition not met within timeout",
) -> bool:
    """
    等待条件满足

    Args:
        condition_func: 条件函数，返回bool
        timeout: 超时时间（秒）
        interval: 检查间隔（秒）
        timeout_message: 超时消息

    Returns:
        条件是否满足
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        if condition_func():
            return True

        time.sleep(interval)

    return False


def parse_memory_address(addr_str: str) -> Optional[int]:
    """
    解析内存地址

    Args:
        addr_str: 地址字符串

    Returns:
        地址整数
    """
    try:
        # 移除 0x 前缀
        addr_str = addr_str.lower().replace("0x", "")

        # 转换为整数
        return int(addr_str, 16)
    except ValueError:
        return None


def validate_ip_address(ip_str: str) -> bool:
    """
    验证IP地址

    Args:
        ip_str: IP地址字符串

    Returns:
        是否有效
    """
    try:
        parts = ip_str.split(".")
        if len(parts) != 4:
            return False

        for part in parts:
            num = int(part)
            if num < 0 or num > 255:
                return False

        return True
    except ValueError:
        return False


def validate_port(port: int) -> bool:
    """
    验证端口

    Args:
        port: 端口号

    Returns:
        是否有效
    """
    return 1 <= port <= 65535