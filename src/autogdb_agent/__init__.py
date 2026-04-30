"""
AutoGDB Agent - 智能GDB调试助手

一个基于大语言模型的智能调试代理系统，提供插件化架构和丰富的扩展能力。
"""

__version__ = "1.0.0"
__author__ = "AutoGDB Agent Team"
__email__ = "support@autogdb-agent.com"

from .core.agent import Agent
from .core.session import Session
from .core.plugin_manager import PluginManager
from .core.tool_registry import ToolRegistry

__all__ = [
    "Agent",
    "Session",
    "PluginManager",
    "ToolRegistry",
]