"""
Tool Registry - 工具注册中心
"""

import asyncio
from typing import Any, Dict, List, Optional, Type

from .config import Config
from .exceptions import ToolError
from ..utils.logger import get_logger


class ToolRegistry:
    """
    工具注册中心
    管理所有可用工具，提供统一的接口
    """

    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(__name__)

        # 工具存储
        self.tools: Dict[str, Type] = {}
        self.tool_instances: Dict[str, Any] = {}

        # 工具状态
        self.initialized = False

    async def initialize(self):
        """初始化工具注册中心"""
        if self.initialized:
            return

        self.logger.info("初始化工具注册中心...")

        # 注册内置工具
        await self._register_builtin_tools()

        # 从配置加载工具
        await self._load_configured_tools()

        # 初始化工具
        await self._initialize_tools()

        self.initialized = True
        self.logger.info(f"工具注册中心初始化完成，共注册 {len(self.tools)} 个工具")

    async def shutdown(self):
        """关闭工具注册中心"""
        self.logger.info("关闭工具注册中心...")

        # 清理工具实例
        for instance in self.tool_instances.values():
            if hasattr(instance, "cleanup"):
                await instance.cleanup()

        self.tool_instances.clear()
        self.tools.clear()

    async def _register_builtin_tools(self):
        """注册内置工具"""
        from ..tools.debugger import DebuggerTool
        from ..tools.analyzer import CrashAnalyzerTool
        from ..tools.poc_sender import POCSenderTool
        from ..tools.memory_inspector import MemoryInspectorTool
        from ..tools.stack_trace import StackTraceTool

        builtin_tools = [
            DebuggerTool,
            CrashAnalyzerTool,
            POCSenderTool,
            MemoryInspectorTool,
            StackTraceTool,
        ]

        for tool_class in builtin_tools:
            await self.register(tool_class)

    async def _load_configured_tools(self):
        """从配置加载工具"""
        configured_tools = self.config.get("tools", [])
        for tool_config in configured_tools:
            tool_name = tool_config.get("name")
            tool_path = tool_config.get("path")

            if tool_name and tool_path:
                try:
                    await self.register_custom_tool(tool_name, tool_path)
                except Exception as e:
                    self.logger.error(f"加载自定义工具失败 {tool_name}: {e}")

    async def _initialize_tools(self):
        """初始化所有工具"""
        for tool_name, tool_class in self.tools.items():
            try:
                # 创建工具实例
                instance = await self._create_tool_instance(tool_class)
                if instance:
                    self.tool_instances[tool_name] = instance
                    self.logger.debug(f"初始化工具: {tool_name}")

            except Exception as e:
                self.logger.error(f"初始化工具失败 {tool_name}: {e}")

    async def _create_tool_instance(self, tool_class: Type) -> Optional[Any]:
        """创建工具实例"""
        try:
            # 获取工具配置
            tool_name = getattr(tool_class, "tool_name", tool_class.__name__)
            tool_config = self.config.get(f"tools.{tool_name}", {})

            # 创建实例
            instance = tool_class(tool_config)

            # 如果工具有初始化方法，调用它
            if hasattr(instance, "initialize"):
                await instance.initialize()

            return instance

        except Exception as e:
            self.logger.error(f"创建工具实例失败: {e}")
            return None

    async def register(self, tool_class: Type):
        """注册工具"""
        tool_name = getattr(tool_class, "tool_name", tool_class.__name__)
        self.tools[tool_name] = tool_class

        self.logger.debug(f"注册工具: {tool_name}")

    async def unregister(self, tool_name: str) -> bool:
        """注销工具"""
        if tool_name in self.tools:
            del self.tools[tool_name]

            # 清理实例
            instance = self.tool_instances.pop(tool_name, None)
            if instance and hasattr(instance, "cleanup"):
                await instance.cleanup()

            self.logger.debug(f"注销工具: {tool_name}")
            return True

        return False

    async def register_custom_tool(self, name: str, path: str):
        """注册自定义工具"""
        try:
            # 动态导入模块
            import importlib.util
            spec = importlib.util.spec_from_file_location(name, path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # 查找工具类
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and hasattr(attr, "is_tool")
                        and attr.is_tool
                    ):
                        self.tools[name] = attr
                        self.logger.info(f"注册自定义工具: {name}")
                        return

                raise ToolError(f"在模块中未找到工具类: {path}")

        except Exception as e:
            self.logger.error(f"注册自定义工具失败 {name}: {e}")
            raise ToolError(f"注册自定义工具失败: {e}")

    async def get_tool(self, tool_name: str) -> Optional[Type]:
        """获取工具类"""
        return self.tools.get(tool_name)

    async def get_tool_instance(self, tool_name: str) -> Optional[Any]:
        """获取工具实例"""
        return self.tool_instances.get(tool_name)

    async def execute(self, tool_name: str, **kwargs) -> Any:
        """执行工具"""
        tool_class = self.tools.get(tool_name)
        if not tool_class:
            raise ToolError(f"工具不存在: {tool_name}")

        try:
            # 如果没有实例，创建一个
            if tool_name not in self.tool_instances:
                instance = await self._create_tool_instance(tool_class)
                self.tool_instances[tool_name] = instance

            # 执行工具
            instance = self.tool_instances[tool_name]
            return await instance.execute(**kwargs)

        except Exception as e:
            self.logger.error(f"执行工具失败 {tool_name}: {e}")
            raise ToolError(f"执行工具失败: {e}")

    async def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有工具"""
        tools_info = []

        for name, tool_class in self.tools.items():
            tool_info = {
                "name": name,
                "class": tool_class.__name__,
                "module": tool_class.__module__,
                "instance_loaded": name in self.tool_instances,
                "configurable": hasattr(tool_class, "config_schema"),
            }

            # 获取工具描述
            if hasattr(tool_class, "description"):
                tool_info["description"] = tool_class.description

            # 获取工具版本
            if hasattr(tool_class, "version"):
                tool_info["version"] = tool_class.version

            # 获取工具类别
            if hasattr(tool_class, "category"):
                tool_info["category"] = tool_class.category

            # 获取工具参数
            if hasattr(tool_class, "parameters"):
                tool_info["parameters"] = tool_class.parameters

            tools_info.append(tool_info)

        return tools_info

    async def validate_tool_args(self, tool_name: str, args: Dict) -> bool:
        """验证工具参数"""
        tool_class = self.tools.get(tool_name)
        if not tool_class:
            return False

        # 如果工具有参数验证方法
        if hasattr(tool_class, "validate_args"):
            return await tool_class.validate_args(args)

        # 基本参数检查
        if hasattr(tool_class, "parameters"):
            required_params = tool_class.parameters.get("required", [])
            for param in required_params:
                if param not in args:
                    return False

        return True

    async def get_tool_by_category(self, category: str) -> List[Dict[str, Any]]:
        """根据类别获取工具"""
        return [
            tool_info
            for tool_info in await self.list_tools()
            if tool_info.get("category") == category
        ]

    def get_tool_categories(self) -> Dict[str, List[str]]:
        """获取工具分类"""
        categories = {}

        for name, tool_class in self.tools.items():
            category = getattr(tool_class, "category", "general")
            if category not in categories:
                categories[category] = []
            categories[category].append(name)

        return categories