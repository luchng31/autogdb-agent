"""
UDP协议插件
"""

import asyncio
from typing import Any, Dict, Optional

from .base import ProtocolPlugin
from ..core.exceptions import ProtocolError


class UDPProtocol(ProtocolPlugin):
    """
    UDP协议插件
    """

    protocol_name = "udp"
    protocol_type = "transport"
    description = "UDP传输层协议"
    version = "1.0.0"
    default_port = 53

    # 参数定义
    config_schema = {
        "type": "object",
        "required": ["target", "port"],
        "properties": {
            "target": {"type": "string", "description": "目标主机"},
            "port": {"type": "integer", "description": "目标端口"},
            "timeout": {"type": "number", "default": 5, "description": "超时时间（秒）"},
            "retries": {"type": "integer", "default": 3, "description": "重试次数"},
        },
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)

        # UDP配置
        self.target: str = self.config.get("target", "localhost")
        self.port: int = self.config.get("port", 53)
        self.timeout: int = self.config.get("timeout", 5)
        self.retries: int = self.config.get("retries", 3)

        # Socket
        self.socket = None

    async def initialize(self):
        """初始化协议"""
        self.logger.info(f"初始化UDP协议: {self.target}:{self.port}")

        # 创建socket
        self.socket = await asyncio.get_event_loop().create_datagram_endpoint(
            lambda: asyncio.DatagramProtocol(),
            local_addr=(None, 0),
        )

    async def connect(self, target: Optional[str] = None, port: Optional[int] = None, **kwargs) -> bool:
        """
        连接到UDP服务器

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

        self.logger.info(f"UDP连接到: {self.target}:{self.port}")
        return True

    async def disconnect(self):
        """断开UDP连接"""
        if self.socket:
            try:
                self.socket[0].close()
                self.socket[1].close()
                self.logger.info("UDP连接已关闭")
            except Exception as e:
                self.logger.error(f"关闭UDP连接时出错: {e}")
            finally:
                self.socket = None
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
        if not self.socket:
            raise ProtocolError("UDP未初始化")

        # 尝试发送
        for attempt in range(self.retries):
            try:
                self.socket[0].sendto(data, (self.target, self.port))

                # 读取响应
                loop = asyncio.get_event_loop()
                response, addr = await asyncio.wait_for(
                    loop.sock_recvfrom(self.socket[0], 4096),
                    timeout=self.timeout
                )

                self.logger.debug(f"UDP收到响应: {len(response)} bytes")
                return response

            except asyncio.TimeoutError:
                self.logger.warning(f"UDP接收超时: {self.target}:{self.port}")
            except Exception as e:
                self.logger.error(f"UDP通信失败: {e}")

            # 重试前等待
            if attempt < self.retries - 1:
                await asyncio.sleep(0.1 * (attempt + 1))

        raise ProtocolError(f"UDP通信失败，已重试 {self.retries} 次")

    async def listen(self, callback, **kwargs) -> bool:
        """
        监听UDP数据包

        Args:
            callback: 数据包回调函数
            **kwargs: 额外参数

        Returns:
            是否监听成功
        """
        if not self.socket:
            raise ProtocolError("UDP未初始化")

        self.logger.info(f"开始监听UDP: {self.target}:{self.port}")

        # 创建数据包接收任务
        async def receive():
            loop = asyncio.get_event_loop()
            while self.connected:
                try:
                    data, addr = await asyncio.wait_for(
                        loop.sock_recvfrom(self.socket[0], 4096),
                        timeout=1.0
                    )

                    # 调用回调
                    if callback:
                        await callback(data, addr)

                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    self.logger.error(f"UDP接收错误: {e}")
                    break

        self.receive_task = asyncio.create_task(receive())
        return True

    async def close(self):
        """关闭UDP协议"""
        if self.receive_task:
            self.receive_task.cancel()
            try:
                await self.receive_task
            except asyncio.CancelledError:
                pass

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