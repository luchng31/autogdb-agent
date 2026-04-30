"""
Protocol Sender Tool - 协议发送工具
支持TCP、UDP、HTTP等多种协议
"""

import asyncio
import json
from typing import Any, Dict, List, Optional

from ..core.config import Config
from ..core.exceptions import ToolError
from ..utils.helpers import expand_vars, validate_ip_address, validate_port


class ProtocolSenderTool:
    """
    协议发送工具
    支持多种网络协议
    """

    tool_name = "protocol_sender"
    category = "network"
    description = "通过多种协议发送数据包"
    version = "2.0.0"

    # 参数定义
    parameters = {
        "type": "object",
        "properties": {
            "protocol": {
                "type": "string",
                "enum": ["tcp", "udp", "http"],
                "description": "协议类型",
            },
            "target": {
                "type": "string",
                "description": "目标地址",
            },
            "port": {
                "type": "integer",
                "description": "目标端口",
            },
            "data": {
                "type": "string",
                "description": "要发送的数据",
            },
            "timeout": {
                "type": "number",
                "default": 10,
                "description": "超时时间（秒）",
            },
            "retries": {
                "type": "integer",
                "default": 3,
                "description": "重试次数",
            },
        },
        "required": ["protocol", "target", "data"],
    }

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.protocol = None
        self.connection = None
        self.sender = None

    async def initialize(self):
        """初始化工具"""
        self.logger = __import__("logging").getLogger(__name__)
        self.logger.info("初始化协议发送工具")

    async def execute(self, **kwargs) -> Any:
        """
        执行协议发送

        Args:
            **kwargs: 参数

        Returns:
            发送结果
        """
        protocol = kwargs.get("protocol")
        target = kwargs.get("target")
        data = kwargs.get("data")
        port = kwargs.get("port")
        timeout = kwargs.get("timeout", 10)
        retries = kwargs.get("retries", 3)

        # 解析数据
        try:
            if isinstance(data, str):
                data_bytes = data.encode("utf-8")
            elif isinstance(data, bytes):
                data_bytes = data
            else:
                data_bytes = str(data).encode("utf-8")
        except Exception as e:
            raise ToolError(f"数据编码失败: {e}")

        # 验证参数
        if not protocol or not target:
            raise ToolError("必须指定协议和目标地址")

        # 选择协议发送器
        protocol_lower = protocol.lower()
        if protocol_lower == "tcp":
            sender = TCPProtocolSender(target, port, timeout, retries)
        elif protocol_lower == "udp":
            sender = UDPProtocolSender(target, port, timeout, retries)
        elif protocol_lower == "http":
            sender = HTTPProtocolSender(target, data_bytes, timeout, retries)
        else:
            raise ToolError(f"不支持的协议: {protocol}")

        # 执行发送
        try:
            result = await sender.send(data_bytes)

            return {
                "success": True,
                "protocol": protocol,
                "target": target,
                "data_size": len(data_bytes),
                "response_size": len(result) if result else 0,
                "response": result.decode("utf-8", errors="replace") if result else None,
            }

        except Exception as e:
            raise ToolError(f"协议发送失败: {e}")

        finally:
            await sender.close()

    async def cleanup(self):
        """清理资源"""
        if self.sender:
            await self.sender.close()


class TCPProtocolSender:
    """TCP发送器"""

    def __init__(self, target: str, port: int, timeout: int, retries: int):
        self.target = target
        self.port = port
        self.timeout = timeout
        self.retries = retries
        self.connection = None

    async def send(self, data: bytes) -> bytes:
        """发送数据"""
        for attempt in range(self.retries):
            try:
                self.logger = __import__("logging").getLogger(__name__)
                self.logger.info(f"TCP发送尝试 {attempt + 1}/{self.retries}")

                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(self.target, self.port),
                    timeout=self.timeout
                )

                writer.write(data)
                await writer.drain()

                response = await reader.read(4096)

                writer.close()
                await writer.wait_closed()

                return response

            except asyncio.TimeoutError:
                self.logger.warning(f"TCP超时: {self.target}:{self.port}")
            except ConnectionRefusedError:
                self.logger.warning(f"TCP连接被拒绝")
            except Exception as e:
                self.logger.error(f"TCP发送失败: {e}")

            if attempt < self.retries - 1:
                await asyncio.sleep(1)

        raise Exception(f"TCP发送失败，已重试 {self.retries} 次")

    async def close(self):
        """关闭连接"""
        if self.connection:
            try:
                self.connection[1].close()
            except:
                pass


class UDPProtocolSender:
    """UDP发送器"""

    def __init__(self, target: str, port: int, timeout: int, retries: int):
        self.target = target
        self.port = port
        self.timeout = timeout
        self.retries = retries
        self.socket = None

    async def send(self, data: bytes) -> bytes:
        """发送数据"""
        loop = asyncio.get_event_loop()

        for attempt in range(self.retries):
            try:
                self.logger = __import__("logging").getLogger(__name__)
                self.logger.info(f"UDP发送尝试 {attempt + 1}/{self.retries}")

                # 创建socket
                if not self.socket:
                    self.socket, _ = await loop.create_datagram_endpoint(
                        lambda: asyncio.DatagramProtocol(),
                        local_addr=(None, 0),
                    )

                # 发送
                self.socket[0].sendto(data, (self.target, self.port))

                # 接收
                response, addr = await asyncio.wait_for(
                    loop.sock_recvfrom(self.socket[0], 4096),
                    timeout=self.timeout
                )

                return response

            except asyncio.TimeoutError:
                self.logger.warning(f"UDP超时: {self.target}:{self.port}")
            except Exception as e:
                self.logger.error(f"UDP发送失败: {e}")

            if attempt < self.retries - 1:
                await asyncio.sleep(0.1)

        raise Exception(f"UDP发送失败，已重试 {self.retries} 次")

    async def close(self):
        """关闭socket"""
        if self.socket:
            try:
                self.socket[0].close()
            except:
                pass


class HTTPProtocolSender:
    """HTTP发送器"""

    def __init__(self, target: str, data: bytes, timeout: int, retries: int):
        self.target = target
        self.data = data
        self.timeout = timeout
        self.retries = retries
        self.client = None

    async def send(self, data: Optional[bytes] = None) -> bytes:
        """发送HTTP请求"""
        import httpx

        request_data = data or self.data

        for attempt in range(self.retries):
            try:
                self.logger = __import__("logging").getLogger(__name__)
                self.logger.info(f"HTTP发送尝试 {attempt + 1}/{self.retries}")

                # 创建客户端
                if not self.client:
                    self.client = httpx.AsyncClient(
                        timeout=httpx.Timeout(self.timeout),
                        follow_redirects=True
                    )

                # 发送请求
                response = await self.client.post(
                    self.target,
                    content=request_data,
                    headers={"Content-Type": "application/octet-stream"}
                )

                response.raise_for_status()
                return response.content

            except Exception as e:
                self.logger.error(f"HTTP发送失败: {e}")

            if attempt < self.retries - 1:
                await asyncio.sleep(1)

        raise Exception(f"HTTP发送失败，已重试 {self.retries} 次")

    async def close(self):
        """关闭客户端"""
        if self.client:
            try:
                await self.client.aclose()
            except:
                pass