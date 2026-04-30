"""
Agent - 智能调试代理的核心类
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

from .config import Config
from .message import Message
from .plugin_manager import PluginManager
from .session import Session
from .tool_registry import ToolRegistry
from ..utils.logger import get_logger


class Agent:
    """
    智能调试代理核心类
    负责协调各个组件，管理会话，处理用户请求
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.logger = get_logger(__name__)

        # 核心组件
        self.plugin_manager = PluginManager(config)
        self.tool_registry = ToolRegistry(config)
        self.sessions: Dict[str, Session] = {}

        # 状态
        self.running = False
        self.start_time = None

        # 注册默认工具
        self._register_default_tools()

    async def start(self):
        """启动代理"""
        if self.running:
            return

        self.logger.info("启动 AutoGDB Agent...")
        self.running = True
        self.start_time = datetime.now()

        # 初始化组件
        await self.plugin_manager.initialize()
        await self.tool_registry.initialize()

        self.logger.info("AutoGDB Agent 启动完成")

    async def stop(self):
        """停止代理"""
        if not self.running:
            return

        self.logger.info("停止 AutoGDB Agent...")
        self.running = False

        # 清理会话
        for session in self.sessions.values():
            await session.close()

        # 关闭组件
        await self.plugin_manager.shutdown()
        await self.tool_registry.shutdown()

        self.logger.info("AutoGDB Agent 已停止")

    async def create_session(self, session_id: str, **kwargs) -> Session:
        """创建新的调试会话"""
        if session_id in self.sessions:
            raise ValueError(f"会话 {session_id} 已存在")

        session = Session(session_id, self.config, self.plugin_manager, self.tool_registry)
        await session.initialize(**kwargs)
        self.sessions[session_id] = session

        self.logger.info(f"创建会话: {session_id}")
        return session

    async def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        return self.sessions.get(session_id)

    async def close_session(self, session_id: str):
        """关闭会话"""
        session = self.sessions.pop(session_id, None)
        if session:
            await session.close()
            self.logger.info(f"关闭会话: {session_id}")

    async def process_message(self, session_id: str, message: Message) -> Message:
        """处理用户消息"""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"会话 {session_id} 不存在")

        return await session.process_message(message)

    async def get_status(self) -> Dict[str, Any]:
        """获取代理状态"""
        return {
            "running": self.running,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "uptime": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            "sessions": len(self.sessions),
            "plugins": len(self.plugin_manager.plugins),
            "tools": len(self.tool_registry.tools),
            "session_ids": list(self.sessions.keys()),
        }

    def _register_default_tools(self):
        """注册默认工具"""
        # 这里可以注册一些核心工具
        from ..tools.debugger import DebuggerTool
        from ..tools.analyzer import CrashAnalyzerTool
        from ..tools.poc_sender import POCSenderTool

        self.tool_registry.register(DebuggerTool)
        self.tool_registry.register(CrashAnalyzerTool)
        self.tool_registry.register(POCSenderTool)

    async def list_plugins(self) -> List[Dict[str, Any]]:
        """列出所有插件"""
        return await self.plugin_manager.list_plugins()

    async def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有工具"""
        return await self.tool_registry.list_tools()

    async def execute_command(self, session_id: str, command: str, **kwargs) -> Any:
        """执行命令"""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"会话 {session_id} 不存在")

        return await session.execute_command(command, **kwargs)