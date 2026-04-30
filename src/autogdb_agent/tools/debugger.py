"""
Debugger Tool - 调试器工具
"""

import re
from typing import Any, Dict, List, Optional

import pexpect
from pathlib import Path

from .base import Tool
from ..core.exceptions import ToolError
from ..utils.helpers import expand_vars


class DebuggerTool(Tool):
    """
    GDB调试器工具
    """

    tool_name = "debugger"
    category = "debugger"
    description = "GDB调试器接口"
    version = "1.0.0"

    # 参数定义
    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "GDB命令",
            },
            "target": {
                "type": "string",
                "description": "调试目标（可执行文件或核心文件）",
            },
            "workdir": {
                "type": "string",
                "description": "工作目录",
            },
            "timeout": {
                "type": "number",
                "default": 60,
                "description": "命令超时时间（秒）",
            },
        },
        "required": ["command"],
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)

        # 调试器配置
        self.debugger_path = self.config.get("path", "/usr/bin/gdb")
        self.prompt_pattern = self.config.get("prompt_pattern", r"\(gdb\)")
        self.init_commands = self.config.get("init_commands", [])
        self.timeout = self.config.get("timeout", 60)

        # GDB进程
        self.process = None
        self.workdir = None

    async def initialize(self):
        """初始化调试器工具"""
        self.debugger_path = expand_vars(self.debugger_path)
        self.workdir = Path(expand_vars(self.config.get("workdir", ".")))

    async def execute(self, **kwargs) -> Any:
        """
        执行调试器命令

        Args:
            **kwargs: 参数

        Returns:
            执行结果
        """
        command = kwargs.get("command")
        target = kwargs.get("target")
        workdir = kwargs.get("workdir", self.workdir)
        timeout = kwargs.get("timeout", self.timeout)

        if not command:
            raise ToolError("命令不能为空")

        # 如果指定了目标，先启动调试器
        if target and not self.process:
            await self.start(target, workdir)

        # 执行命令
        try:
            if command == "start":
                target = kwargs.get("target")
                if not target:
                    raise ToolError("启动调试器需要指定目标")
                await self.start(target, workdir)
                return {"status": "started", "target": target}

            elif command == "stop":
                await self.stop()
                return {"status": "stopped"}

            elif command == "restart":
                target = kwargs.get("target")
                if target:
                    await self.restart(target, workdir)
                else:
                    await self.restart()
                return {"status": "restarted"}

            elif command == "status":
                return await self.get_status()

            else:
                # 执行普通GDB命令
                output = await self.execute_command(command, timeout)
                return {
                    "output": output,
                    "command": command,
                }

        except Exception as e:
            raise ToolError(f"执行命令失败: {e}")

    async def start(self, target: str, workdir: Optional[Path] = None):
        """启动GDB"""
        if self.process:
            raise ToolError("调试器已在运行")

        target_path = Path(expand_vars(target))
        if not target_path.exists():
            raise ToolError(f"目标文件不存在: {target_path}")

        # 创建工作目录
        workdir = Path(workdir or self.workdir)
        workdir.mkdir(parents=True, exist_ok=True)

        # 启动GDB
        self.process = pexpect.spawn(
            str(self.debugger_path),
            [f"--cd={workdir}"],
            encoding="utf-8",
            timeout=self.timeout,
        )

        # 等待提示符
        self.process.expect(self.prompt_pattern, timeout=10)

        # 执行初始化命令
        for cmd in self.init_commands:
            await self.execute_command(cmd, timeout)

        # 加载目标文件
        await self.execute_command(f"file {target_path}", timeout)

    async def stop(self):
        """停止GDB"""
        if self.process:
            self.process.sendline("quit")
            self.process.expect(pexpect.EOF, timeout=5)
            self.process.close()
            self.process = None

    async def restart(self, target: Optional[str] = None, workdir: Optional[Path] = None):
        """重启GDB"""
        await self.stop()
        if target:
            await self.start(target, workdir)
        else:
            # 重新启动上一个目标
            if hasattr(self, "last_target"):
                await self.start(self.last_target, workdir)
            else:
                raise ToolError("没有指定目标且没有之前的会话")

    async def execute_command(self, command: str, timeout: int = None) -> str:
        """执行GDB命令"""
        if not self.process:
            raise ToolError("调试器未启动")

        timeout = timeout or self.timeout

        # 发送命令
        self.process.sendline(command)
        self.process.expect(self.prompt_pattern, timeout=timeout)

        # 获取输出
        output = self.process.before or ""
        output = self._clean_output(output)

        # 特殊命令处理
        if command.strip() == "run":
            # 如果是运行命令，需要等待程序退出
            try:
                self.process.expect([self.prompt_pattern, pexpect.EOF], timeout=300)
                if "Program exited" in self.process.before:
                    output += self.process.before
            except pexpect.TIMEOUT:
                output += "\n[Timeout] Program is still running"

        return output

    async def get_status(self) -> Dict[str, Any]:
        """获取调试器状态"""
        return {
            "running": self.process is not None,
            "prompt_pattern": self.prompt_pattern,
            "workdir": str(self.workdir),
            "last_command": getattr(self, "last_command", ""),
            "target": getattr(self, "last_target", ""),
        }

    def _clean_output(self, output: str) -> str:
        """清理输出"""
        # 移除ANSI颜色代码
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        output = ansi_escape.sub('', output)

        # 移除多余空白
        output = '\n'.join(line.strip() for line in output.split('\n') if line.strip())

        return output

    async def cleanup(self):
        """清理资源"""
        await self.stop()