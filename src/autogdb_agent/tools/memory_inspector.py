"""
Memory Inspector Tool - 内存检查工具
"""

import math
import struct
from typing import Any, Dict, List, Optional

from .base import Tool
from ..core.exceptions import ToolError


class MemoryInspectorTool(Tool):
    """
    内存检查工具
    分析程序内存状态
    """

    tool_name = "memory_inspector"
    category = "debugger"
    description = "检查和分析程序内存"
    version = "1.0.0"

    # 参数定义
    parameters = {
        "type": "object",
        "properties": {
            "address": {
                "type": "string",
                "description": "内存地址",
            },
            "size": {
                "type": "integer",
                "default": 64,
                "description": "读取的字节数",
            },
            "format": {
                "type": "string",
                "enum": ["hex", "ascii", "int", "float", "bytes"],
                "default": "hex",
                "description": "输出格式",
            },
            "debugger": {
                "type": "string",
                "description": "调试器实例名称",
            },
        },
        "required": ["address"],
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)

        # 内存格式
        self.formats = {
            "hex": self._format_hex,
            "ascii": self._format_ascii,
            "int": self._format_int,
            "float": self._format_float,
            "bytes": self._format_bytes,
        }

        # 数据类型大小
        self.type_sizes = {
            "char": 1,
            "short": 2,
            "int": 4,
            "long": 8,
            "long long": 8,
            "float": 4,
            "double": 8,
        }

    async def execute(self, **kwargs) -> Any:
        """
        检查内存

        Args:
            **kwargs: 参数

        Returns:
            内存检查结果
        """
        address = kwargs.get("address")
        size = kwargs.get("size", 64)
        format_type = kwargs.get("format", "hex")
        debugger = kwargs.get("debugger")

        # 解析地址
        try:
            addr = int(address, 16) if address.startswith("0x") else int(address)
        except ValueError:
            raise ToolError(f"无效的地址: {address}")

        # 读取内存
        memory_data = await self._read_memory(debugger, addr, size)

        # 格式化输出
        formatter = self.formats.get(format_type)
        if not formatter:
            raise ToolError(f"不支持的格式: {format_type}")

        formatted_data = formatter(memory_data)

        # 分析内存
        analysis = await self._analyze_memory(memory_data, addr)

        return {
            "address": f"0x{addr:x}",
            "size": size,
            "format": format_type,
            "data": formatted_data,
            "analysis": analysis,
        }

    async def _read_memory(
        self, debugger: str, address: int, size: int
    ) -> bytes:
        """读取内存"""
        # 这里应该使用调试器API读取内存
        # 简化实现，返回模拟数据
        return b"\x00" * size  # 实际实现需要从调试器读取

    def _format_hex(self, data: bytes) -> str:
        """格式化为十六进制"""
        return data.hex().upper()

    def _format_ascii(self, data: bytes) -> str:
        """格式化为ASCII"""
        try:
            return data.decode("ascii", errors="replace")
        except:
            return "[非ASCII数据]"

    def _format_int(self, data: bytes) -> List[int]:
        """格式化为整数"""
        if len(data) < 4:
            return []
        return list(struct.unpack("I" * (len(data) // 4), data))

    def _format_float(self, data: bytes) -> List[float]:
        """格式化为浮点数"""
        if len(data) < 4:
            return []
        return list(struct.unpack("f" * (len(data) // 4), data))

    def _format_bytes(self, data: bytes) -> str:
        """格式化为字节字符串"""
        return str(data)

    async def _analyze_memory(self, data: bytes, address: int) -> Dict[str, Any]:
        """分析内存"""
        analysis = {
            "null_bytes": data.count(b"\x00"),
            "non_zero": len([b for b in data if b != 0]),
            "entropy": self._calculate_entropy(data),
            "strings": self._find_strings(data),
            "pointers": self._find_pointers(data),
            "patterns": self._detect_patterns(data),
        }

        # 分析堆栈特征
        if address > 0x7fffffffffff:  # 用户空间
            analysis["stack_analysis"] = self._analyze_stack(data)
        else:
            analysis["heap_analysis"] = self._analyze_heap(data)

        return analysis

    def _calculate_entropy(self, data: bytes) -> float:
        """计算信息熵"""
        if not data:
            return 0.0

        # 计算字节频率
        freq = {}
        for byte in data:
            freq[byte] = freq.get(byte, 0) + 1

        # 计算熵
        entropy = 0.0
        for count in freq.values():
            p = count / len(data)
            entropy -= p * (p and math.log2(p))

        return entropy

    def _find_strings(self, data: bytes) -> List[str]:
        """查找字符串"""
        strings = []
        current_string = []
        min_length = 4  # 最小字符串长度

        for byte in data:
            if 32 <= byte <= 126:  # 可打印ASCII
                current_string.append(chr(byte))
            else:
                if len(current_string) >= min_length:
                    strings.append("".join(current_string))
                current_string = []

        # 添加最后一个字符串
        if len(current_string) >= min_length:
            strings.append("".join(current_string))

        return strings[:5]  # 限制数量

    def _find_pointers(self, data: bytes) -> List[int]:
        """查找可能的指针"""
        pointers = []

        # 检查4字节对齐的地址
        for i in range(0, len(data) - 3, 4):
            word = struct.unpack("<I", data[i:i+4])[0]

            # 检查是否是合理的指针值
            if 0x1000 < word < 0x7fffffffffff:
                pointers.append(word)

        return pointers[:10]  # 限制数量

    def _detect_patterns(self, data: bytes) -> Dict[str, int]:
        """检测模式"""
        patterns = {
            "repeating_bytes": 0,
            "zero_blocks": 0,
            "ff_blocks": 0,
        }

        # 检测重复字节
        for i in range(len(data) - 1):
            if data[i] == data[i + 1]:
                patterns["repeating_bytes"] += 1

        # 检测零块
        zero_count = 0
        for byte in data:
            if byte == 0:
                zero_count += 1
            else:
                if zero_count >= 4:
                    patterns["zero_blocks"] += 1
                zero_count = 0

        # 检测0xFF块
        ff_count = 0
        for byte in data:
            if byte == 0xFF:
                ff_count += 1
            else:
                if ff_count >= 4:
                    patterns["ff_blocks"] += 1
                ff_count = 0

        return patterns

    def _analyze_stack(self, data: bytes) -> Dict[str, Any]:
        """分析栈"""
        return {
            "canary": self._find_canary(data),
            "base_pointer": self._find_base_pointer(data),
            "return_address": self._find_return_address(data),
        }

    def _analyze_heap(self, data: bytes) -> Dict[str, Any]:
        """分析堆"""
        return {
            "chunk_headers": self._find_chunk_headers(data),
            "free_list": self._find_free_list(data),
        }

    def _find_canary(self, data: bytes) -> Optional[int]:
        """查找栈保护cookie"""
        canary_patterns = [
            b"\x00\x00\x00\x00",  # 简单的canary
        ]

        for pattern in canary_patterns:
            if pattern in data:
                return data.index(pattern)

        return None

    def _find_base_pointer(self, data: bytes) -> Optional[int]:
        """查找基址指针"""
        # 查找可能的帧指针
        for i in range(len(data) - 4):
            word = struct.unpack("<I", data[i:i+4])[0]
            if 0x7fff0000 < word < 0x80000000:
                return i
        return None

    def _find_return_address(self, data: bytes) -> Optional[int]:
        """查找返回地址"""
        # 查找可能的返回地址
        for i in range(len(data) - 4):
            word = struct.unpack("<I", data[i:i+4])[0]
            if 0x400000 < word < 0x500000:  # 常见的代码段地址
                return i
        return None

    def _find_chunk_headers(self, data: bytes) -> List[int]:
        """查找堆块头"""
        chunks = []

        # 检查glibc堆块头模式
        for i in range(len(data) - 8):
            # 简单的堆块头检测
            prev_size = struct.unpack("<I", data[i:i+4])[0]
            size = struct.unpack("<I", data[i+4:i+8])[0]

            if size & 1:  # 已分配位
                chunks.append(i)

        return chunks

    def _find_free_list(self, data: bytes) -> List[int]:
        """查找空闲链表"""
        free_list = []

        # 查找空闲链表指针
        for i in range(len(data) - 4):
            word = struct.unpack("<I", data[i:i+4])[0]
            if 0x7fff0000 < word < 0x80000000:  # 可能的链表指针
                free_list.append(word)

        return free_list