"""
POC Sender Tool - POC发送工具
"""

import socket
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import Tool
from ..core.exceptions import ToolError
from ..utils.helpers import expand_vars


class POCSenderTool(Tool):
    """
    POC数据包发送工具
    支持多种协议和重试机制
    """

    tool_name = "poc_sender"
    category = "network"
    description = "发送POC数据包到目标服务"
    version = "1.0.0"

    # 参数定义
    parameters = {
        "type": "object",
        "properties": {
            "target": {
                "type": "string",
                "description": "目标地址 (host:port)",
            },
            "poc_file": {
                "type": "string",
                "description": "POC文件路径",
            },
            "poc_dir": {
                "type": "string",
                "description": "POC目录路径",
            },
            "protocol": {
                "type": "string",
                "enum": ["udp", "tcp", "http"],
                "default": "udp",
                "description": "发送协议",
            },
            "retries": {
                "type": "integer",
                "default": 3,
                "description": "重试次数",
            },
            "timeout": {
                "type": "number",
                "default": 5,
                "description": "超时时间（秒）",
            },
            "delay": {
                "type": "number",
                "default": 0.1,
                "description": "包间延迟（秒）",
            },
            "batch_size": {
                "type": "integer",
                "default": 1,
                "description": "批量大小",
            },
        },
        "required": ["target"],
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)

        # 默认配置
        self.default_port = self.config.get("default_port", 47808)
        self.default_protocol = self.config.get("default_protocol", "udp")
        self.default_retries = self.config.get("retries", 3)
        self.default_timeout = self.config.get("timeout", 5)

        # 网络配置
        self.socket_options = {
            "tcp": {
                "type": socket.SOCK_STREAM,
                "setup": self._setup_tcp,
            },
            "udp": {
                "type": socket.SOCK_DGRAM,
                "setup": self._setup_udp,
            },
            "http": {
                "type": None,
                "setup": self._setup_http,
            },
        }

    async def execute(self, **kwargs) -> Any:
        """
        发送POC数据包

        Args:
            **kwargs: 参数

        Returns:
            发送结果
        """
        target = kwargs.get("target")
        poc_file = kwargs.get("poc_file")
        poc_dir = kwargs.get("poc_dir")
        protocol = kwargs.get("protocol", self.default_protocol)
        retries = kwargs.get("retries", self.default_retries)
        timeout = kwargs.get("timeout", self.default_timeout)
        delay = kwargs.get("delay", 0.1)
        batch_size = kwargs.get("batch_size", 1)

        # 解析目标地址
        host, port = self._parse_target(target)

        # 准备数据
        if poc_file:
            files = [Path(expand_vars(poc_file))]
        elif poc_dir:
            files = self._get_poc_files(Path(expand_vars(poc_dir)))
        else:
            raise ToolError("必须指定POC文件或目录")

        # 发送数据
        results = []
        total_sent = 0

        for file in files:
            if not file.exists():
                results.append({
                    "file": str(file),
                    "status": "failed",
                    "error": "文件不存在",
                })
                continue

            # 读取文件内容
            try:
                data = file.read_bytes()
            except Exception as e:
                results.append({
                    "file": str(file),
                    "status": "failed",
                    "error": str(e),
                })
                continue

            # 发送文件
            file_results = await self._send_data(
                data, host, port, protocol, retries, timeout, delay, batch_size
            )

            # 添加文件信息
            for result in file_results:
                result["file"] = str(file)
                result["size"] = len(data)
                results.append(result)

            total_sent += sum(1 for r in file_results if r["status"] == "success")

        # 汇总结果
        summary = {
            "total_files": len(files),
            "total_sent": total_sent,
            "total_failed": len(results) - total_sent,
            "protocol": protocol,
            "target": f"{host}:{port}",
            "results": results,
        }

        return summary

    def _parse_target(self, target: str) -> tuple[str, int]:
        """解析目标地址"""
        if ":" in target:
            host, port_str = target.rsplit(":", 1)
            port = int(port_str)
        else:
            host = target
            port = self.default_port

        return host, port

    def _get_poc_files(self, directory: Path) -> List[Path]:
        """获取POC文件列表"""
        files = []

        # 支持的文件扩展名
        extensions = [".bin", ".txt", ".dat", ".raw", ".poc"]

        for ext in extensions:
            files.extend(directory.glob(f"*{ext}"))

        # 如果没有特定扩展名的文件，取所有文件
        if not files:
            files.extend(directory.glob("*"))

        # 过滤目录
        files = [f for f in files if f.is_file()]

        # 按名称排序
        files.sort()

        return files

    async def _send_data(
        self,
        data: bytes,
        host: str,
        port: int,
        protocol: str,
        retries: int,
        timeout: float,
        delay: float,
        batch_size: int,
    ) -> List[Dict[str, Any]]:
        """发送数据"""
        results = []

        # 分批处理
        batches = [data[i:i + batch_size] for i in range(0, len(data), batch_size)]

        for batch in batches:
            for attempt in range(retries):
                try:
                    # 创建连接
                    sock = await self._create_connection(host, port, protocol, timeout)

                    # 发送数据
                    if protocol == "udp":
                        await self._send_udp(sock, batch, timeout)
                    elif protocol == "tcp":
                        await self._send_tcp(sock, batch, timeout)
                    elif protocol == "http":
                        await self._send_http(batch, host, port, timeout)

                    # 记录成功
                    results.append({
                        "status": "success",
                        "attempt": attempt + 1,
                        "bytes_sent": len(batch),
                    })

                    break

                except Exception as e:
                    results.append({
                        "status": "failed",
                        "attempt": attempt + 1,
                        "error": str(e),
                    })

                    if attempt == retries - 1:
                        # 最后一次尝试失败
                        break
                    else:
                        # 等待后重试
                        await asyncio.sleep(delay * (attempt + 1))

                finally:
                    # 清理连接
                    if 'sock' in locals() and sock:
                        sock.close()

            # 批次间延迟
            if delay > 0 and len(batches) > 1:
                await asyncio.sleep(delay)

        return results

    async def _create_connection(
        self, host: str, port: int, protocol: str, timeout: float
    ) -> socket.socket:
        """创建网络连接"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)

        if protocol == "udp":
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
        elif protocol == "tcp":
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((host, port))
        elif protocol == "http":
            # HTTP使用httpx客户端
            pass

        return sock

    async def _send_udp(
        self, sock: socket.socket, data: bytes, timeout: float
    ) -> None:
        """发送UDP数据"""
        sock.sendto(data, (sock.getpeername()[0], sock.getpeername()[1]))

    async def _send_tcp(
        self, sock: socket.socket, data: bytes, timeout: float
    ) -> None:
        """发送TCP数据"""
        sock.sendall(data)

    async def _send_http(self, data: bytes, host: str, port: int, timeout: float) -> None:
        """发送HTTP数据"""
        import httpx

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"http://{host}:{port}",
                content=data,
                headers={"Content-Type": "application/octet-stream"},
            )
            response.raise_for_status()

    def _setup_tcp(self, sock: socket.socket) -> None:
        """TCP设置"""
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    def _setup_udp(self, sock: socket.socket) -> None:
        """UDP设置"""
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def _setup_http(self) -> None:
        """HTTP设置"""
        pass