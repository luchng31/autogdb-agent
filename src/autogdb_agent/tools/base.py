"""
Tool Base Class - 工具基类
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ..core.plugin import Plugin


class Tool(Plugin):
    """
    工具基类
    所有工具都必须继承这个类
    """

    # 工具标志
    is_tool = True

    # 工具信息
    tool_name: str = ""  # 工具名称
    category: str = "general"  # 工具类别
    description: str = ""  # 工具描述
    version: str = "1.0.0"  # 工具版本

    # 参数定义
    parameters: Dict[str, Any] = {}  # 参数定义

    # 工具配置
    config_schema: Dict[str, Any] = {}  # 配置模式

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化工具

        Args:
            config: 工具配置
        """
        super().__init__(config)
        self.enabled = True

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """
        执行工具功能

        Args:
            **kwargs: 参数

        Returns:
            执行结果
        """
        pass

    def validate_args(self, args: Dict[str, Any]) -> bool:
        """
        验证参数

        Args:
            args: 参数字典

        Returns:
            参数是否有效
        """
        # 检查必需参数
        required = self.parameters.get("required", [])
        for param in required:
            if param not in args:
                return False

        # 检查参数类型
        properties = self.parameters.get("properties", {})
        for param, param_type in properties.items():
            if param in args:
                if not isinstance(args[param], param_type):
                    return False

        return True

    def get_info(self) -> Dict[str, Any]:
        """
        获取工具信息

        Returns:
            工具信息字典
        """
        info = super().get_info()
        info.update({
            "category": self.category,
            "parameters": self.parameters,
            "config_schema": self.config_schema,
        })
        return info