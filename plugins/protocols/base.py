"""
协议插件基类 - 支持多种网络协议
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class ProtocolPlugin(ABC):
    """
    协议插件基类
    所有协议插件都必须继承这个类
    """

    # 协议标志
    is_protocol = True

    # 协议信息
    protocol_name: str = ""  # 协议名称
    protocol_type: str = "network"  # 协议类型: network, transport, application
    description: str = ""  # 协议描述
    version: str = "1.0.0"  # 协议版本
    default_port: int = 0  # 默认端口

    # 协议配置
    config_schema: Dict[str, Any] = {}  # 配置模式

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化协议插件

        Args:
            config: 协议配置
        """
        self.config = config or {}
        self.enabled = True

        # 连接状态
        self.connected = False
        self.connection = None

    @abstractmethod
    async def initialize(self):
        """
        初始化协议
        在插件加载时调用
        """
        pass

    @abstractmethod
    async def connect(self, target: str, **kwargs) -> bool:
        """
        连接到目标

        Args:
            target: 目标地址 (host:port 或 URL)
            **kwargs: 额外参数

        Returns:
            是否连接成功
        """
        pass

    @abstractmethod
    async def disconnect(self):
        """
        断开连接
        """
        pass

    @abstractmethod
    async def send(self, data: bytes, **kwargs) -> Any:
        """
        发送数据

        Args:
            data: 要发送的数据
            **kwargs: 额外参数

        Returns:
            响应数据
        """
        pass

    @abstractmethod
    async def listen(self, callback, **kwargs) -> bool:
        """
        监听连接

        Args:
            callback: 回调函数
            **kwargs: 额外参数

        Returns:
            是否监听成功
        """
        pass

    @abstractmethod
    async def close(self):
        """
        关闭协议
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
        获取协议信息

        Returns:
            协议信息字典
        """
        return {
            "name": self.protocol_name,
            "type": self.protocol_type,
            "description": self.description,
            "version": self.version,
            "enabled": self.enabled,
            "connected": self.connected,
            "default_port": self.default_port,
            "config": self.config,
        }

    def get_supported_targets(self) -> List[str]:
        """获取支持的目标类型"""
        return self.config.get("supported_targets", ["any"])

    async def execute(self, **kwargs) -> Any:
        """
        执行协议操作

        Args:
            **kwargs: 参数

        Returns:
            执行结果
        """
        action = kwargs.get("action")

        if action == "connect":
            target = kwargs.get("target")
            return await self.connect(target, **kwargs)
        elif action == "disconnect":
            await self.disconnect()
            return {"status": "disconnected"}
        elif action == "send":
            data = kwargs.get("data")
            return await self.send(data, **kwargs)
        elif action == "listen":
            callback = kwargs.get("callback")
            return await self.listen(callback, **kwargs)
        elif action == "close":
            await self.close()
            return {"status": "closed"}
        elif action == "status":
            return await self.get_status()
        else:
            raise ValueError(f"未知操作: {action}")