"""
Disassembler Tool - 反汇编工具
"""

import re
from typing import Any, Dict, List, Optional

from .base import Tool
from ..core.exceptions import ToolError


class DisassemblerTool(Tool):
    """
    反汇编工具
    """

    tool_name = "disassembler"
    category = "debugger"
    description = "反汇编代码并分析"
    version = "1.0.0"

    # 参数定义
    parameters = {
        "type": "object",
        "properties": {
            "address": {
                "type": "string",
                "description": "起始地址",
            },
            "size": {
                "type": "integer",
                "default": 32,
                "description": "反汇编的字节数",
            },
            "format": {
                "type": "string",
                "enum": ["intel", "att", "native"],
                "default": "intel",
                "description": "汇编语法格式",
            },
            "debugger": {
                "type": "string",
                "description": "调试器实例名称",
            },
            "analyze": {
                "type": "boolean",
                "default": True,
                "description": "是否分析反汇编结果",
            },
        },
        "required": ["address"],
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)

        # 指令模式
        self.instruction_patterns = {
            "mov": r"mov\s+([^,]+),\s*(.+)",
            "lea": r"lea\s+([^,]+),\s*\[(.+)\]",
            "call": r"call\s+([^;]+)",
            "jmp": r"jmp\s+([^;]+)",
            "ret": r"ret",
            "push": r"push\s+(.+)",
            "pop": r"pop\s+(.+)",
            "add": r"add\s+([^,]+),\s*(.+)",
            "sub": r"sub\s+([^,]+),\s*(.+)",
            "mul": r"mul\s+(.+)",
            "div": r"div\s+(.+)",
            "xor": r"xor\s+([^,]+),\s*(.+)",
            "and": r"and\s+([^,]+),\s*(.+)",
            "or": r"or\s+([^,]+),\s*(.+)",
            "not": r"not\s+(.+)",
            "test": r"test\s+([^,]+),\s*(.+)",
            "cmp": r"cmp\s+([^,]+),\s*(.+)",
            "int": r"int\s+(.+)",
            "in": r"in\s+(.+),\s*(.+)",
            "out": r"out\s+(.+),\s*(.+)",
        }

        # 危险指令
        self.dangerous_instructions = [
            "int 3",    # 断点
            "int 0x80", # 系统调用
            "sysenter", # 快速系统调用
            "sysexit",  # 系统调用退出
        ]

    async def execute(self, **kwargs) -> Any:
        """
        反汇编代码

        Args:
            **kwargs: 参数

        Returns:
            反汇编结果
        """
        address = kwargs.get("address")
        size = kwargs.get("size", 32)
        format_type = kwargs.get("format", "intel")
        debugger = kwargs.get("debugger")
        analyze = kwargs.get("analyze", True)

        # 解析地址
        try:
            addr = int(address, 16) if address.startswith("0x") else int(address)
        except ValueError:
            raise ToolError(f"无效的地址: {address}")

        # 读取代码
        code = await self._read_code(debugger, addr, size)

        # 反汇编
        instructions = await self._disassemble(code, addr, format_type)

        # 分析代码
        if analyze:
            analysis = await self._analyze_instructions(instructions)
        else:
            analysis = None

        return {
            "address": f"0x{addr:x}",
            "size": size,
            "format": format_type,
            "instructions": instructions,
            "analysis": analysis,
            "summary": {
                "total_instructions": len(instructions),
                "dangerous_count": sum(1 for inst in instructions if self._is_dangerous(inst)),
                "function_calls": sum(1 for inst in instructions if self._is_call(inst)),
                "branches": sum(1 for inst in instructions if self._is_branch(inst)),
            },
        }

    async def _read_code(self, debugger: str, address: int, size: int) -> bytes:
        """读取代码"""
        # 这里应该从调试器读取代码
        # 简化实现，返回模拟数据
        return b"\x90\x90\x90\x90"  # NOP指令

    async def _disassemble(
        self, code: bytes, start_addr: int, format_type: str
    ) -> List[Dict[str, Any]]:
        """反汇编代码"""
        instructions = []

        # 这里应该使用真正的反汇编器
        # 简化实现，生成模拟指令
        current_addr = start_addr

        # 模拟一些指令
        mock_instructions = [
            {"addr": start_addr, "bytes": b"\x90", "op": "nop", "operands": ""},
            {"addr": start_addr + 1, "bytes": b"\xb8\x2a\x00\x00\x00", "op": "mov", "operands": "eax, 42"},
            {"addr": start_addr + 6, "bytes": b"\xff\xd0", "op": "call", "operands": "eax"},
            {"addr": start_addr + 8, "bytes": b"\xc3", "op": "ret", "operands": ""},
        ]

        for inst in mock_instructions:
            # 格式化指令
            formatted = self._format_instruction(inst, format_type)
            inst["formatted"] = formatted
            instructions.append(inst)

            current_addr = inst["addr"] + len(inst["bytes"])

        return instructions

    def _format_instruction(self, instruction: Dict[str, Any], format_type: str) -> str:
        """格式化指令"""
        addr = instruction["addr"]
        op = instruction["op"]
        operands = instruction["operands"]
        bytes_hex = instruction["bytes"].hex().upper()

        if format_type == "intel":
            return f"{addr:08x}: {bytes_hex:<10} {op} {operands}"
        elif format_type == "att":
            return f"{addr:08x}: {bytes_hex:<10} {operands} {op}"
        else:  # native
            return f"{addr:08x}: {op} {operands}"

    async def _analyze_instructions(self, instructions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析指令"""
        analysis = {
            "patterns": [],
            "functions": [],
            "dangers": [],
            "control_flow": self._analyze_control_flow(instructions),
            "memory_access": self._analyze_memory_access(instructions),
        }

        # 检查模式
        analysis["patterns"] = self._find_patterns(instructions)

        # 识别函数
        analysis["functions"] = self._identify_functions(instructions)

        # 检查危险指令
        analysis["dangers"] = [
            inst for inst in instructions
            if self._is_dangerous(inst)
        ]

        return analysis

    def _find_patterns(self, instructions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """查找代码模式"""
        patterns = []

        # 查查空操作序列
        nop_sequences = []
        current_nop = 0

        for inst in instructions:
            if inst["op"] == "nop":
                current_nop += 1
            else:
                if current_nop >= 3:
                    nop_sequences.append({
                        "type": "nop_sequence",
                        "length": current_nop,
                        "start": inst["addr"] - current_nop,
                    })
                current_nop = 0

        if current_nop >= 3:
            nop_sequences.append({
                "type": "nop_sequence",
                "length": current_nop,
                "start": instructions[-1]["addr"] - current_nop + 1,
            })

        patterns.extend(nop_sequences)

        # 查查函数序言
        for i in range(len(instructions) - 2):
            # 典型的函数序言
            if (instructions[i]["op"] == "push" and
                instructions[i+1]["op"] == "mov" and
                "ebp" in instructions[i+1]["operands"]):
                patterns.append({
                    "type": "function_prologue",
                    "address": instructions[i]["addr"],
                    "instructions": [
                        instructions[i]["op"],
                        instructions[i+1]["op"],
                    ],
                })

        return patterns

    def _identify_functions(self, instructions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """识别函数"""
        functions = []

        # 通过ret指令识别函数
        for i, inst in enumerate(instructions):
            if inst["op"] == "ret":
                # 向查找函数开始
                func_start = None
                for j in range(i, max(0, i-20), -1):
                    if instructions[j]["op"] in ["call", "jmp"]:
                        func_start = j
                        break

                if func_start is not None:
                    functions.append({
                        "start": instructions[func_start]["addr"],
                        "end": inst["addr"],
                        "size": inst["addr"] - instructions[func_start]["addr"],
                        "calls": [],
                    })

        return functions

    def _analyze_control_flow(self, instructions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析控制流"""
        return {
            "branches": [
                inst for inst in instructions
                if self._is_branch(inst)
            ],
            "calls": [
                inst for inst in instructions
                if self._is_call(inst)
            ],
            "returns": [
                inst for inst in instructions
                if inst["op"] == "ret"
            ],
        }

    def _analyze_memory_access(self, instructions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析内存访问"""
        memory_access = []

        for inst in instructions:
            operands = inst["operands"]
            if "[" in operands and "]" in operands:
                memory_access.append({
                    "instruction": inst["op"],
                    "address": operands,
                    "type": "dereference",
                })

        return {
            "accesses": memory_access,
            "total": len(memory_access),
        }

    def _is_dangerous(self, instruction: Dict[str, Any]) -> bool:
        """检查是否是危险指令"""
        full_inst = f"{instruction['op']} {instruction['operands']}"
        return any(danger in full_inst for danger in self.dangerous_instructions)

    def _is_call(self, instruction: Dict[str, Any]) -> bool:
        """检查是否是调用指令"""
        return instruction["op"] in ["call", "bl", "blx", "blx", "blrl"]

    def _is_branch(self, instruction: Dict[str, Any]) -> bool:
        """检查是否是分支指令"""
        return instruction["op"] in ["jmp", "jz", "jnz", "je", "jne", "b", "beq", "bne"]