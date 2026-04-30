"""
Plugin Base Class - 插件基类
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class Plugin(ABC):
    """
    插件基类
    所有插件都必须继承这个类
    """

    # 插件标志
    is_plugin = True

    # 插件信息
    plugin_name: str = ""  # 插件名称
    plugin_type: str = "general"  # 插件类型
    description: str = ""  # 插件描述
    version: str = "1.0.0"  # 插件版本

    # 插件配置
    config_schema: Dict[str, Any] = {}  # 配置模式

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化插件

        Args:
            config: 插件配置
        """
        self.config = config or {}
        self.enabled = True

    @abstractmethod
    async def initialize(self):
        """
        初始化插件
        在插件加载时调用
        """
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """
        执行插件功能

        Args:
            **kwargs: 参数

        Returns:
            执行结果
        """
        pass

    async def cleanup(self):
        """
        清理插件
        在插件卸载时调用
        """
        pass

    def validate_config(self) -> bool:
        """
        验证配置

        Returns:
            配置是否有效
        """
        # 基本验证，子类可以重写
        required_keys = self.config_schema.get("required", [])
        for key in required_keys:
            if key not in self.config:
                return False

        return True

    def get_info(self) -> Dict[str, Any]:
        """
        获取插件信息

        Returns:
            插件信息字典
        """
        return {
            "name": self.plugin_name,
            "type": self.plugin_type,
            "description": self.description,
            "version": self.version,
            "enabled": self.enabled,
            "config": self.config,
        }