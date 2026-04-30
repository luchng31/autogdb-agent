"""
Session - 调试会话管理
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from .config import Config
from .message import Message
from .plugin_manager import PluginManager
from .tool_registry import ToolRegistry
from ..utils.logger import get_logger


class Session:
    """
    调试会话类
    管理单个调试任务的状态和上下文
    """

    def __init__(
        self,
        session_id: str,
        config: Config,
        plugin_manager: PluginManager,
        tool_registry: ToolRegistry,
    ):
        self.id = session_id
        self.config = config
        self.plugin_manager = plugin_manager
        self.tool_registry = tool_registry

        self.logger = get_logger(f"session.{self.id}")

        # 会话状态
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.metadata: Dict[str, Any] = {}

        # 调试状态
        self.debug_target: Optional[str] = None
        self.debug_type: Optional[str] = None
        self.status: str = "created"  # created, running, paused, completed, failed

        # 上下文管理
        self.context: Dict[str, Any] = {}
        self.message_history: List[Message] = []

        # 插件实例
        self.active_plugins: Dict[str, Any] = {}

        # 任务队列
        self.task_queue: List[Dict[str, Any]] = []

    async def initialize(self, **kwargs):
        """初始化会话"""
        self.logger.info(f"初始化会话: {self.id}")

        # 设置会话参数
        self.debug_target = kwargs.get("debug_target")
        self.debug_type = kwargs.get("debug_type", "gdb")

        # 添加初始消息
        await self.add_message(
            Message(
                role="system",
                content="调试会话已创建",
                timestamp=datetime.now(),
            )
        )

        self.status = "ready"
        self.updated_at = datetime.now()

    async def close(self):
        """关闭会话"""
        self.logger.info(f"关闭会话: {self.id}")

        # 清理插件
        for plugin in self.active_plugins.values():
            if hasattr(plugin, "cleanup"):
                await plugin.cleanup()

        # 保存会话记录
        await self.save_session()

        self.status = "closed"
        self.updated_at = datetime.now()

    async def process_message(self, message: Message) -> Message:
        """处理用户消息"""
        self.logger.info(f"处理消息: {message.role} - {message.content[:50]}...")

        # 添加到历史
        await self.add_message(message)

        # 根据消息类型处理
        if message.role == "user":
            response = await self._handle_user_message(message)
        elif message.role == "system":
            response = await self._handle_system_message(message)
        else:
            response = Message(
                role="assistant",
                content=f"未知的消息类型: {message.role}",
                timestamp=datetime.now(),
            )

        await self.add_message(response)
        return response

    async def _handle_user_message(self, message: Message) -> Message:
        """处理用户消息"""
        content = message.content.strip()

        # 命令解析
        if content.startswith("/"):
            return await self._handle_command(content[1:])

        # 调试任务处理
        if self.status == "ready":
            return await self._start_debug_task(content)

        # 普通对话
        return await self._handle_conversation(content)

    async def _handle_command(self, command: str) -> Message:
        """处理系统命令"""
        parts = command.split()
        cmd = parts[0]
        args = parts[1:]

        commands = {
            "start": self._cmd_start_debug,
            "stop": self._cmd_stop_debug,
            "pause": self._cmd_pause,
            "resume": self._cmd_resume,
            "status": self._cmd_status,
            "help": self._cmd_help,
            "clear": self._cmd_clear,
        }

        if cmd in commands:
            result = await commands[cmd](*args)
            return Message(
                role="assistant",
                content=result,
                timestamp=datetime.now(),
            )
        else:
            return Message(
                role="assistant",
                content=f"未知命令: {cmd}\n使用 /help 查看帮助",
                timestamp=datetime.now(),
            )

    async def _cmd_start_debug(self, target: str) -> str:
        """启动调试"""
        if not target:
            return "请指定调试目标"

        self.debug_target = target
        self.status = "running"
        self.context["debug_started"] = True

        # 启动调试器插件
        debugger_plugin = await self.plugin_manager.get_plugin("debugger")
        if debugger_plugin:
            self.active_plugins["debugger"] = await debugger_plugin.create_instance(
                {"target": target}
            )

        return f"开始调试: {target}"

    async def _cmd_stop_debug(self) -> str:
        """停止调试"""
        self.status = "completed"

        # 清理插件
        for plugin in self.active_plugins.values():
            if hasattr(plugin, "stop"):
                await plugin.stop()

        self.active_plugins.clear()
        return "调试已停止"

    async def _cmd_pause(self) -> str:
        """暂停调试"""
        if self.status == "running":
            self.status = "paused"
            return "调试已暂停"
        return "当前没有运行中的调试任务"

    async def _cmd_resume(self) -> str:
        """恢复调试"""
        if self.status == "paused":
            self.status = "running"
            return "调试已恢复"
        return "当前没有暂停的调试任务"

    async def _cmd_status(self) -> str:
        """查看状态"""
        return f"""
会话状态: {self.status}
调试目标: {self.debug_target or "未设置"}
活跃插件: {len(self.active_plugins)}
消息数量: {len(self.message_history)}
创建时间: {self.created_at}
更新时间: {self.updated_at}
        """

    async def _cmd_help(self) -> str:
        """帮助信息"""
        return """
可用命令:
  /start <target> - 启动调试
  /stop - 停止调试
  /pause - 暂停调试
  /resume - 恢复调试
  /status - 查看状态
  /clear - 清除上下文
  /help - 显示帮助
        """

    async def _cmd_clear(self) -> str:
        """清除上下文"""
        self.context.clear()
        self.message_history.clear()
        return "上下文已清除"

    async def _start_debug_task(self, content: str) -> Message:
        """启动调试任务"""
        # 这里实现具体的调试逻辑
        return Message(
            role="assistant",
            content=f"开始调试任务: {content}\n正在初始化调试环境...",
            timestamp=datetime.now(),
        )

    async def _handle_conversation(self, content: str) -> Message:
        """处理普通对话"""
        # 使用LLM处理对话
        # 这里简化处理，实际应该调用LLM服务
        return Message(
            role="assistant",
            content=f"收到消息: {content}\n当前会话状态: {self.status}",
            timestamp=datetime.now(),
        )

    async def _handle_system_message(self, message: Message) -> Message:
        """处理系统消息"""
        return Message(
            role="assistant",
            content=f"系统消息已处理: {message.content}",
            timestamp=datetime.now(),
        )

    async def add_message(self, message: Message):
        """添加消息到历史"""
        self.message_history.append(message)
        self.updated_at = datetime.now()

    async def execute_command(self, command: str, **kwargs) -> Any:
        """执行命令"""
        # 使用工具注册器执行命令
        return await self.tool_registry.execute(command, **kwargs)

    async def save_session(self):
        """保存会话数据"""
        # 这里可以保存到数据库或文件
        self.logger.info(f"保存会话数据: {self.id}")

    def get_context(self) -> Dict[str, Any]:
        """获取会话上下文"""
        return {
            "session_id": self.id,
            "status": self.status,
            "debug_target": self.debug_target,
            "debug_type": self.debug_type,
            "metadata": self.metadata,
            "context": self.context,
            "message_count": len(self.message_history),
        }

    @property
    def age(self) -> float:
        """会话持续时间（秒）"""
        return (datetime.now() - self.created_at).total_seconds()