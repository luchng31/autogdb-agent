"""
Tool Runner - 工具执行器
提供通用的工具调用和协调能力
"""

import asyncio
from typing import Any, Dict, List, Optional

from .config import Config
from .exceptions import ToolError
from ..utils.logger import get_logger


class ToolRunner:
    """
    工具执行器
    负责执行和协调各种调试工具
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.logger = get_logger(__name__)

        # 工具实例缓存
        self.tool_instances: Dict[str, Any] = {}

    async def run_tool(
        self,
        tool_name: str,
        action: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        运行工具

        Args:
            tool_name: 工具名称
            action: 工具操作类型
            **kwargs: 工具参数

        Returns:
            执行结果
        """
        # 动态导入工具模块
        try:
            tool_module = await self._import_tool(tool_name)
        except ImportError as e:
            raise ToolError(f"无法导入工具模块: {e}")

        # 查找工具类
        tool_class = None
        for attr_name in dir(tool_module):
            attr = getattr(tool_module, attr_name)
            if isinstance(attr, type) and hasattr(attr, "is_tool") and attr.is_tool:
                tool_class = attr
                break

        if not tool_class:
            raise ToolError(f"在模块 {tool_module.__name__} 中未找到工具")

        # 创建工具实例
        try:
            tool_config = self.config.get(f"tools.{tool_name}", {})
            tool = tool_class(tool_config)
            await tool.initialize()
            self.tool_instances[tool_name] = tool
            self.logger.info(f"工具 {tool_name} 已加载")
        except Exception as e:
            self.logger.error(f"初始化工具 {tool_name} 失败: {e}")
            raise ToolError(f"初始化工具失败: {e}")

        # 执行工具操作
        try:
            if action:
                return await tool.execute(action=action, **kwargs)
            else:
                # 默认执行操作
                return await tool.execute(**kwargs)

        except Exception as e:
            self.logger.error(f"工具 {tool_name} 执行失败: {e}")
            raise ToolError(f"工具执行失败: {e}")

        finally:
            # 保持工具实例可用，不在这里清理

    async def run_workflow(
        self,
        workflow_name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        运行工作流

        Args:
            workflow_name: 工作流名称
            **kwargs: 参数

        Returns:
            工作流执行结果
        """
        # 获取工作流配置
        workflows = self.config.get("workflows", {})
        if "workflows" not in workflows:
            raise ToolError("未配置工作流")

        workflow = workflows.get(workflow_name)
        if not workflow:
            raise ToolError(f"工作流不存在: {workflow_name}")

        self.logger.info(f"执行工作流: {workflow_name} - {workflow.get('description', '')}")

        results = {
            "workflow": workflow_name,
            "steps": [],
            "success": True,
        }

        # 执行工作流步骤
        for step in workflow.get("steps", []):
            try:
                step_result = await self._run_step(step, **kwargs)
                results["steps"].append({
                    "action": step["action"],
                    "plugin": step.get("plugin"),
                    "success": True,
                    "result": step_result,
                })

            except Exception as e:
                self.logger.error(f"工作流步骤失败: {step}")
                results["steps"].append({
                    "action": step["action"],
                    "plugin": step.get("plugin"),
                    "success": False,
                    "error": str(e),
                })
                results["success"] = False
                break

        # 清理工具实例
        await self.cleanup_tools()

        return results

    async def _run_step(self, step: Dict, **kwargs) -> Any:
        """运行单个工作流步骤"""
        action = step.get("action")
        plugin_name = step.get("plugin")

        self.logger.info(f"执行步骤: {action} (plugin: {plugin_name})")

        # 运行插件操作
        if action == "setup" or action == "initialize":
            return await self.run_tool(plugin_name, "initialize")

        elif action == "analyze":
            return await self.run_tool(plugin_name, "analyze", **kwargs)

        elif action == "debug":
            return await self.run_tool(plugin_name, "execute", **kwargs)

        elif action == "fuzz":
            return await self.run_tool(plugin_name, "fuzz", **kwargs)

        elif action == "collect_crashes":
            return await self.run_tool(plugin_name, "collect", **kwargs)

        elif action == "triage":
            return await self.run_tool(plugin_name, "triage", **kwargs)

        elif action == "run_tests":
            return await self.run_tool(plugin_name, "run", **kwargs)

        elif action == "compare":
            return await self.run_tool(plugin_name, "compare", **kwargs)

        else:
            raise ToolError(f"未知步骤操作: {action}")

    async def _import_tool(self, tool_name: str):
        """动态导入工具模块"""
        # 简化的导入逻辑
        # 实际实现中需要更复杂的模块查找机制
        module_map = {
            "debugger": "autogdb_agent.tools.debugger",
            "analyzer": "autogdb_agent.tools.analyzer",
            "poc_sender": "autogdb_agent.tools.poc_sender",
            "memory_inspector": "autogdb_agent.tools.memory_inspector",
            "stack_trace": "autogdb_agent.tools.stack_trace",
            "disassembler": "autogdb_agent.tools.disassembler",
            "protocol_sender": "autogdb_agent.tools.protocol_sender",
        }

        module_path = module_map.get(tool_name)
        if not module_path:
            raise ImportError(f"未知工具: {tool_name}")

        module = __import__(module_path, fromlist=[tool_name])
        return module

    async def cleanup_tools(self):
        """清理所有工具实例"""
        for tool_name, tool in self.tool_instances.items():
            try:
                if hasattr(tool, "cleanup"):
                    await tool.cleanup()
                self.logger.info(f"清理工具: {tool_name}")
            except Exception as e:
                self.logger.error(f"清理工具 {tool_name} 失败: {e}")

        self.tool_instances.clear()

    async def list_available_tools(self) -> List[Dict[str, Any]]:
        """列出所有可用工具"""
        available_tools = []

        # 动态扫描所有工具模块
        tools_modules = [
            "autogdb_agent.tools.debugger",
            "autogdb_agent.tools.analyzer",
            "autogdb_agent.tools.poc_sender",
            "autogdb_agent.tools.memory_inspector",
            "autogdb_agent.tools.stack_trace",
            "autogdb_agent.tools.disassembler",
            "autogdb_agent.tools.protocol_sender",
        ]

        for module_path in tools_modules:
            try:
                module = __import__(module_path, fromlist=[])
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and hasattr(attr, "is_tool") and attr.is_tool:
                        available_tools.append({
                            "name": getattr(attr, "tool_name", attr_name),
                            "class": attr_name,
                            "module": module_path,
                            "category": getattr(attr, "category", "general"),
                            "description": getattr(attr, "description", ""),
                            "version": getattr(attr, "version", "1.0.0"),
                        })
            except ImportError:
                continue

        return available_tools

    async def validate_tool_args(self, tool_name: str, args: Dict) -> bool:
        """验证工具参数"""
        # 获取工具类
        tool_class = None
        tools = await self.list_available_tools()
        for tool_info in tools:
            if tool_info["name"] == tool_name:
                # 导入并获取类
                module = __import__(tool_info["module"], fromlist=[tool_info["class"]])
                tool_class = getattr(module, tool_info["class"])
                break

        if not tool_class:
            return False

        # 验证参数
        if hasattr(tool_class, "validate_args"):
            return await tool_class.validate_args(args)

        # 基本验证
        if hasattr(tool_class, "parameters"):
            required = tool_class.parameters.get("required", [])
            for param in required:
                if param not in args:
                    return False

        return True