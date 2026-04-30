"""
TCP协议插件
"""

import asyncio
from typing import Any, Dict, Optional

from .base import ProtocolPlugin
from ..core.exceptions import ProtocolError


class TCPProtocol(ProtocolPlugin):
    """
    TCP协议插件
    """

    protocol_name = "tcp"
    protocol_type = "transport"
    description = "TCP传输层协议"
    version = "1.0.0"
    default_port = 80

    # 参数定义
    config_schema = {
        "type": "object",
        "required": ["target", "port"],
        "properties": {
            "target": {"type": "string", "description": "目标主机"},
            "port": {"type": "integer", "description": "目标端口"},
            "timeout": {"type": "number", "default": 10, "description": "超时时间（秒）"},
            "retries": {"type": "integer", "default": 3, "description": "重试次数"},
            "keep_alive": {"type": "boolean", "default": True, "description": "保持连接"},
        },
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)

        # TCP配置
        self.target: str = self.config.get("target", "localhost")
        self.port: int = self.config.get("port", 80)
        self.timeout: int = self.config.get("timeout", 10)
        self.retries: int = self.config.get("retries", 3)
        self.keep_alive: bool = self.config.get("keep_alive", True)

        # 连接
        self.connection = None

    async def initialize(self):
        """初始化协议"""
        self.logger.info(f"初始化TCP协议: {self.target}:{self.port}")

    async def connect(self, target: Optional[str] = None, port: Optional[int] = None, **kwargs) -> bool:
        """
        连接到TCP服务器

        Args:
            target: 目标地址 (可选，会覆盖初始化配置)
            port: 端口 (可选，会覆盖初始化配置)
            **kwargs: 额外参数

        Returns:
            是否连接成功
        """
        if target:
            self.target = target
        if port:
            self.port = port

        # 清除之前的连接
        await self.disconnect()

        # 尝试连接
        for attempt in range(self.retries):
            try:
                self.logger.info(f"TCP连接尝试 {attempt + 1}/{self.retries}: {self.target}:{self.port}")

                # 创建连接
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(self.target, self.port),
                    timeout=self.timeout
                )

                self.connection = (reader, writer)
                self.connected = True
                self.logger.info(f"TCP连接成功: {self.target}:{self.port}")
                return True

            except asyncio.TimeoutError:
                self.logger.warning(f"TCP连接超时: {self.target}:{self.port}")
            except ConnectionRefusedError:
                self.logger.warning(f"TCP连接被拒绝: {self.target}:{self.port}")
            except Exception as e:
                self.logger.error(f"TCP连接失败: {e}")

            # 重试前等待
            if attempt < self.retries - 1:
                await asyncio.sleep(1 * (attempt + 1))

        self.logger.error(f"TCP连接失败，已重试 {self.retries} 次")
        return False

    async def disconnect(self):
        """断开TCP连接"""
        if self.connection:
            try:
                writer = self.connection[1]
                writer.close()
                await writer.wait_closed()
                self.logger.info("TCP连接已关闭")
            except Exception as e:
                self.logger.error(f"关闭TCP连接时出错: {e}")
            finally:
                self.connection = None
                self.connected = False

    async def send(self, data: bytes, **kwargs) -> bytes:
        """
        发送数据

        Args:
            data: 要发送的数据
            **kwargs: 额外参数

        Returns:
            响应数据
        """
        if not self.connected:
            raise ProtocolError("未连接到服务器")

        try:
            writer = self.connection[1]
            writer.write(data)
            await writer.drain()

            # 读取响应
            reader = self.connection[0]
            response = await reader.read(4096)

            return response

        except Exception as e:
            raise ProtocolError(f"发送TCP数据失败: {e}")

    async def listen(self, callback, **kwargs) -> bool:
        """
        监听TCP连接

        Args:
            callback: 连接回调函数
            **kwargs: 额外参数

        Returns:
            是否监听成功
        """
        raise ProtocolError("TCP监听功能未实现，请使用WebSocket协议")

    async def close(self):
        """关闭TCP协议"""
        await self.disconnect()

    async def get_status(self) -> Dict[str, Any]:
        """获取协议状态"""
        return {
            "protocol": self.protocol_name,
            "connected": self.connected,
            "target": self.target,
            "port": self.port,
            "timeout": self.timeout,
            "retries": self.retries,
        }

    async def cleanup(self):
        """清理资源"""
        await self.close()