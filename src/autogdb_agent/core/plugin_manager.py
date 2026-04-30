"""
Plugin Manager - 插件管理器
"""

import asyncio
import importlib
import inspect
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from .config import Config
from .exceptions import PluginError
from ..utils.logger import get_logger


class PluginManager:
    """
    插件管理器
    负责加载、管理和协调插件
    """

    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(__name__)

        # 插件存储
        self.plugins: Dict[str, Type] = {}
        self.plugin_instances: Dict[str, Any] = {}
        self.plugin_paths: List[Path] = []

        # 插件状态
        self.initialized = False

    async def initialize(self):
        """初始化插件管理器"""
        if self.initialized:
            return

        self.logger.info("初始化插件管理器...")

        # 设置插件路径
        await self._setup_plugin_paths()

        # 加载插件
        await self._load_plugins()

        # 初始化插件
        await self._initialize_plugins()

        self.initialized = True
        self.logger.info(f"插件管理器初始化完成，共加载 {len(self.plugins)} 个插件")

    async def shutdown(self):
        """关闭插件管理器"""
        self.logger.info("关闭插件管理器...")

        # 停止所有插件实例
        for instance in self.plugin_instances.values():
            if hasattr(instance, "shutdown"):
                await instance.shutdown()

        self.plugin_instances.clear()
        self.plugins.clear()

    async def _setup_plugin_paths(self):
        """设置插件路径"""
        # 默认插件路径
        default_paths = [
            Path(__file__).parent.parent / "plugins",
            Path.home() / ".autogdb-agent" / "plugins",
        ]

        # 从配置中获取额外的插件路径
        custom_paths = self.config.get("plugins.paths", [])
        default_paths.extend([Path(p) for p in custom_paths])

        # 过滤并验证路径
        for path in default_paths:
            if path.exists():
                self.plugin_paths.append(path)
                self.logger.debug(f"添加插件路径: {path}")

    async def _load_plugins(self):
        """加载所有插件"""
        for plugin_path in self.plugin_paths:
            await self._load_plugins_from_path(plugin_path)

    async def _load_plugins_from_path(self, path: Path):
        """从指定路径加载插件"""
        self.logger.debug(f"从路径加载插件: {path}")

        # 搜索插件文件
        for plugin_file in path.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue

            try:
                # 导入模块
                module_name = plugin_file.stem
                spec = importlib.util.spec_from_file_location(module_name, plugin_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    # 查找插件类
                    for name, obj in inspect.getmembers(module):
                        if (
                            inspect.isclass(obj)
                            and hasattr(obj, "is_plugin")
                            and obj.is_plugin
                        ):
                            plugin_name = getattr(obj, "plugin_name", name)
                            self.plugins[plugin_name] = obj
                            self.logger.debug(f"发现插件: {plugin_name}")

            except Exception as e:
                self.logger.error(f"加载插件失败 {plugin_file}: {e}")

    async def _initialize_plugins(self):
        """初始化插件"""
        for plugin_name, plugin_class in self.plugins.items():
            try:
                # 创建插件实例
                instance = await self._create_plugin_instance(plugin_class)
                if instance:
                    self.plugin_instances[plugin_name] = instance
                    self.logger.debug(f"初始化插件: {plugin_name}")

            except Exception as e:
                self.logger.error(f"初始化插件失败 {plugin_name}: {e}")

    async def _create_plugin_instance(self, plugin_class: Type) -> Optional[Any]:
        """创建插件实例"""
        try:
            # 获取插件配置
            plugin_name = getattr(plugin_class, "plugin_name", plugin_class.__name__)
            plugin_config = self.config.get(f"plugins.{plugin_name}", {})

            # 创建实例
            instance = plugin_class(plugin_config)

            # 如果插件有初始化方法，调用它
            if hasattr(instance, "initialize"):
                await instance.initialize()

            return instance

        except Exception as e:
            self.logger.error(f"创建插件实例失败: {e}")
            return None

    async def get_plugin(self, plugin_name: str) -> Optional[Type]:
        """获取插件类"""
        return self.plugins.get(plugin_name)

    async def get_plugin_instance(self, plugin_name: str) -> Optional[Any]:
        """获取插件实例"""
        return self.plugin_instances.get(plugin_name)

    async def create_plugin_instance(self, plugin_name: str, config: Dict = None) -> Optional[Any]:
        """创建新的插件实例"""
        plugin_class = self.plugins.get(plugin_name)
        if not plugin_class:
            raise PluginError(f"插件不存在: {plugin_name}")

        try:
            plugin_config = config or self.config.get(f"plugins.{plugin_name}", {})
            instance = plugin_class(plugin_config)

            if hasattr(instance, "initialize"):
                await instance.initialize()

            return instance

        except Exception as e:
            self.logger.error(f"创建插件实例失败 {plugin_name}: {e}")
            raise PluginError(f"创建插件实例失败: {e}")

    async def list_plugins(self) -> List[Dict[str, Any]]:
        """列出所有插件"""
        plugins_info = []

        for name, plugin_class in self.plugins.items():
            plugin_info = {
                "name": name,
                "class": plugin_class.__name__,
                "file": getattr(plugin_class, "__module__", ""),
                "instance_loaded": name in self.plugin_instances,
                "configurable": hasattr(plugin_class, "config_schema"),
            }

            # 获取插件描述
            if hasattr(plugin_class, "description"):
                plugin_info["description"] = plugin_class.description

            # 获取插件版本
            if hasattr(plugin_class, "version"):
                plugin_info["version"] = plugin_class.version

            plugins_info.append(plugin_info)

        return plugins_info

    async def enable_plugin(self, plugin_name: str) -> bool:
        """启用插件"""
        if plugin_name not in self.plugins:
            return False

        try:
            if plugin_name not in self.plugin_instances:
                instance = await self.create_plugin_instance(plugin_name)
                self.plugin_instances[plugin_name] = instance

            return True

        except Exception as e:
            self.logger.error(f"启用插件失败 {plugin_name}: {e}")
            return False

    async def disable_plugin(self, plugin_name: str) -> bool:
        """禁用插件"""
        try:
            instance = self.plugin_instances.pop(plugin_name, None)
            if instance:
                if hasattr(instance, "shutdown"):
                    await instance.shutdown()

            return True

        except Exception as e:
            self.logger.error(f"禁用插件失败 {plugin_name}: {e}")
            return False

    async def reload_plugin(self, plugin_name: str) -> bool:
        """重新加载插件"""
        # 先禁用
        await self.disable_plugin(plugin_name)

        # 重新加载模块
        for plugin_class in self.plugins.values():
            if getattr(plugin_class, "plugin_name", plugin_class.__name__) == plugin_name:
                # 重新导入
                module = importlib.import_module(plugin_class.__module__)
                importlib.reload(module)

                # 更新插件类
                new_class = getattr(module, plugin_class.__name__)
                self.plugins[plugin_name] = new_class

                # 重新启用
                await self.enable_plugin(plugin_name)
                return True

        return False

    def get_plugin_by_type(self, plugin_type: str) -> List[Type]:
        """根据类型获取插件"""
        return [
            plugin_class
            for plugin_class in self.plugins.values()
            if getattr(plugin_class, "plugin_type", "") == plugin_type
        ]

    def get_plugin_categories(self) -> Dict[str, List[str]]:
        """获取插件分类"""
        categories = {}

        for name, plugin_class in self.plugins.items():
            plugin_type = getattr(plugin_class, "plugin_type", "general")
            if plugin_type not in categories:
                categories[plugin_type] = []
            categories[plugin_type].append(name)

        return categories