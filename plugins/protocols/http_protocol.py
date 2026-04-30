"""
HTTP协议插件
"""

import httpx
from typing import Any, Dict, Optional

from .base import ProtocolPlugin
from ..core.exceptions import ProtocolError


class HTTPProtocol(ProtocolPlugin):
    """
    HTTP协议插件
    """

    protocol_name = "http"
    protocol_type = "application"
    description = "HTTP应用层协议"
    version = "1.0.0"
    default_port = 80

    # 参数定义
    config_schema = {
        "type": "object",
        "required": ["url"],
        "properties": {
            "url": {"type": "string", "description": "HTTP URL"},
            "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"], "default": "POST"},
            "timeout": {"type": "number", "default": 30, "description": "超时时间（秒）"},
            "retries": {"type": "integer", "default": 3, "description": "重试次数"},
            "headers": {"type": "object", "description": "HTTP请求头"},
            "verify_ssl": {"type": "boolean", "default": True, "description": "验证SSL证书"},
            "proxy": {"type": "string", "description": "代理地址"},
            "json": {"type": "object", "description": "JSON请求体"},
        },
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)

        # HTTP配置
        self.url: str = self.config.get("url", "")
        self.method: str = self.config.get("method", "POST")
        self.timeout: int = self.config.get("timeout", 30)
        self.retries: int = self.config.get("retries", 3)
        self.headers: Dict[str, str] = self.config.get("headers", {})
        self.verify_ssl: bool = self.config.get("verify_ssl", True)
        self.proxy: Optional[str] = self.config.get("proxy")
        self.json_data: Optional[Dict] = self.config.get("json")

        # 客户端
        self.client = None

    async def initialize(self):
        """初始化HTTP客户端"""
        self.logger.info(f"初始化HTTP协议: {self.method} {self.url}")

        # 配置HTTP客户端
        client_kwargs = {
            "timeout": httpx.Timeout(self.timeout),
            "verify": self.verify_ssl,
            "follow_redirects": True,
        }

        if self.proxy:
            client_kwargs["proxy"] = self.proxy

        self.client = httpx.AsyncClient(**client_kwargs)

    async def connect(self, url: Optional[str] = None, **kwargs) -> bool:
        """
        连接到HTTP服务器

        Args:
            url: HTTP URL (可选，会覆盖初始化配置)
            **kwargs: 额外参数

        Returns:
            是否连接成功
        """
        if url:
            self.url = url

        # 验证URL
        if not self.url:
            raise ProtocolError("未提供HTTP URL")

        self.logger.info(f"HTTP连接到: {self.method} {self.url}")
        return True

    async def disconnect(self):
        """断开HTTP连接"""
        if self.client:
            try:
                await self.client.aclose()
                self.logger.info("HTTP客户端已关闭")
            except Exception as e:
                self.logger.error(f"关闭HTTP客户端时出错: {e}")
            finally:
                self.client = None

    async def send(self, data: Optional[bytes] = None, json: Optional[Dict] = None, **kwargs) -> bytes:
        """
        发送HTTP请求

        Args:
            data: 请求体数据 (bytes)
            json: JSON请求体
            **kwargs: 额外参数

        Returns:
            响应内容
        """
        if not self.client:
            raise ProtocolError("HTTP未初始化")

        # 合并参数
        request_data = kwargs.get("data") or data or self.json_data or json
        request_headers = {**self.headers, **kwargs.get("headers", {})}

        # 确定请求方法
        request_method = kwargs.get("method") or self.method

        # 发送请求
        for attempt in range(self.retries):
            try:
                self.logger.debug(f"HTTP请求尝试 {attempt + 1}/{self.retries}: {request_method} {self.url}")

                if request_method == "GET":
                    response = await self.client.get(self.url, headers=request_headers)
                elif request_method == "POST":
                    response = await self.client.post(self.url, data=request_data, json=json, headers=request_headers)
                elif request_method == "PUT":
                    response = await self.client.put(self.url, data=request_data, json=json, headers=request_headers)
                elif request_method == "DELETE":
                    response = await self.client.delete(self.url, headers=request_headers)
                elif request_method == "PATCH":
                    response = await self.client.patch(self.url, data=request_data, json=json, headers=request_headers)
                else:
                    raise ProtocolError(f"不支持的HTTP方法: {request_method}")

                response.raise_for_status()

                self.logger.info(f"HTTP响应成功: {response.status_code}")
                return response.content

            except httpx.TimeoutException:
                self.logger.warning(f"HTTP请求超时: {self.url}")
            except httpx.HTTPStatusError as e:
                self.logger.error(f"HTTP请求失败: {e.response.status_code}")
                if attempt == self.retries - 1:
                    raise ProtocolError(f"HTTP请求失败: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                self.logger.error(f"HTTP请求失败: {e}")

            # 重试前等待
            if attempt < self.retries - 1:
                await asyncio.sleep(1 * (attempt + 1))

        raise ProtocolError(f"HTTP请求失败，已重试 {self.retries} 次")

    async def listen(self, callback, **kwargs) -> bool:
        """
        监听HTTP请求（不支持）

        Args:
            callback: 回调函数
            **kwargs: 额外参数

        Returns:
            不支持监听
        """
        raise ProtocolError("HTTP协议不支持监听模式")

    async def close(self):
        """关闭HTTP协议"""
        await self.disconnect()

    async def get_status(self) -> Dict[str, Any]:
        """获取协议状态"""
        return {
            "protocol": self.protocol_name,
            "connected": self.client is not None,
            "url": self.url,
            "method": self.method,
            "timeout": self.timeout,
            "retries": self.retries,
            "verify_ssl": self.verify_ssl,
        }

    async def cleanup(self):
        """清理资源"""
        await self.close()