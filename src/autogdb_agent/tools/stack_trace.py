"""
Stack Trace Tool - 栈回溯工具
"""

import re
from typing import Any, Dict, List, Optional

from .base import Tool
from ..core.exceptions import ToolError


class StackTraceTool(Tool):
    """
    栈回溯分析工具
    """

    tool_name = "stack_trace"
    category = "debugger"
    description = "分析和美化栈回溯"
    version = "1.0.0"

    # 参数定义
    parameters = {
        "type": "object",
        "properties": {
            "bt_output": {
                "type": "string",
                "description": "bt命令的输出",
            },
            "dwarf_info": {
                "type": "string",
                "description": "DWARF调试信息",
            },
            "symbols": {
                "type": "string",
                "description": "符号文件路径",
            },
            "demangle": {
                "type": "boolean",
                "default": True,
                        "description": "是否解码C++名称",
            },
        },
        "required": ["bt_output"],
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)

        # 栈帧解析正则
        self.frame_patterns = [
            # GDB格式: #0 0x0000000000401000 in main () at test.c:10
            r"#(\d+)\s+(0x[0-9a-f]+)\s+in\s+([^\s(]+)(?:\s*\(\s*(.*?)\s*\))?\s*(?:at\s+([^:]+):(\d+))?",

            # LLDB格式: frame #0: 0x0000000100000fa0 test`main at test.c:10:5
            r"frame\s+#(\d+):\s+(0x[0-9a-f]+)\s+([^\s`]+)`([^\s]+)\s+at\s+([^:]+):(\d+)(?::(\d+))?",

            # WinDbg格式: 00 00007ffb`1d2e4fa0 00007ffb`1d2e4e60 MyModule!MyFunction+0x50
            r"(\d{2})\s+(0x[0-9a-f]+)\s+(0x[0-9a-f]+)\s+([^\s!]+)!([^\s+]+)(?:\+0x([0-9a-f]+))?",
        ]

        # 函数名解码
        self.demangle_patterns = {
            "c++": [
                r"_Z(\w+)",  # Itanium ABI
                r"?(\w+)",   # MSVC
            ],
            "rust": [
                r"_([A-Z][a-zA-Z0-9_]*)",  # Rust
            ],
        }

    async def execute(self, **kwargs) -> Any:
        """
        分析栈回溯

        Args:
            **kwargs: 参数

        Returns:
            分析结果
        """
        bt_output = kwargs.get("bt_output", "")
        dwarf_info = kwargs.get("dwarf_info", "")
        symbols = kwargs.get("symbols", "")
        demangle = kwargs.get("demangle", True)

        # 解析栈帧
        frames = await self._parse_frames(bt_output)

        # 增强栈帧信息
        if demangle:
            frames = await self._demangle_frames(frames)

        # 添加DWARF信息
        if dwarf_info:
            frames = await self._add_dwarf_info(frames, dwarf_info)

        # 添加符号信息
        if symbols:
            frames = await self._add_symbols(frames, symbols)

        # 分析栈回溯
        analysis = await self._analyze_stack_trace(frames)

        return {
            "frames": frames,
            "analysis": analysis,
            "summary": {
                "total_frames": len(frames),
                "crash_frame": analysis.get("crash_frame"),
                "recursive_calls": analysis.get("recursive_calls", []),
                "tail_calls": analysis.get("tail_calls", []),
            },
        }

    async def _parse_frames(self, bt_output: str) -> List[Dict[str, Any]]:
        """解析栈帧"""
        frames = []
        lines = bt_output.split('\n')

        for line in lines:
            line = line.strip()
            if not line.startswith("#"):
                continue

            # 尝试各种格式
            for pattern in self.frame_patterns:
                match = re.search(pattern, line)
                if match:
                    frame = self._extract_frame_info(match, pattern)
                    if frame:
                        frames.append(frame)
                        break

        return frames

    def _extract_frame_info(self, match, pattern: str) -> Optional[Dict[str, Any]]:
        """提取栈帧信息"""
        frame = {
            "number": None,
            "address": None,
            "function": None,
            "arguments": None,
            "file": None,
            "line": None,
            "column": None,
            "module": None,
        }

        # 根据不同的模式提取信息
        if "#0" in pattern:  # GDB格式
            frame.update({
                "number": int(match.group(1)),
                "address": match.group(2),
                "function": match.group(3),
                "arguments": match.group(4),
                "file": match.group(5),
                "line": int(match.group(6)) if match.group(6) else None,
            })
        elif "frame #" in pattern:  # LLDB格式
            frame.update({
                "number": int(match.group(1)),
                "address": match.group(2),
                "module": match.group(3),
                "function": match.group(4),
                "file": match.group(5),
                "line": int(match.group(6)) if match.group(6) else None,
                "column": int(match.group(7)) if match.group(7) else None,
            })
        elif r"\d{2}\s+" in pattern:  # WinDbg格式
            frame.update({
                "number": int(match.group(1)),
                "address": match.group(2),
                "return_address": match.group(3),
                "module": match.group(4),
                "function": match.group(5),
                "offset": match.group(6),
            })

        return frame

    async def _demangle_frames(self, frames: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """解码函数名"""
        for frame in frames:
            function = frame.get("function")
            if function:
                # 尝试C++解码
                for pattern in self.demangle_patterns.get("c++", []):
                    match = re.search(pattern, function)
                    if match:
                        frame["demangled"] = self._demangle_cplus(function, match)
                        break

                # 尝试Rust解码
                if not frame.get("demangled"):
                    for pattern in self.demangle_patterns.get("rust", []):
                        match = re.search(pattern, function)
                        if match:
                            frame["demangled"] = self._demangle_rust(function, match)
                            break

        return frames

    def _demangle_cplus(self, name: str, match) -> str:
        """解码C++函数名"""
        # 简单的解码逻辑
        if name.startswith("_Z"):
            # Itanium ABI
            return name[2:]  # 简化处理
        elif name.startswith("?"):
            # MSVC
            return name[1:]  # 简化处理
        return name

    def _demangle_rust(self, name: str, match) -> str:
        """解码Rust函数名"""
        # 简单的Rust解码
        clean_name = match.group(1)
        if clean_name:
            return clean_name
        return name

    async def _add_dwarf_info(
        self, frames: List[Dict[str, Any]], dwarf_info: str
    ) -> List[Dict[str, Any]]:
        """添加DWARF信息"""
        # 这里应该解析DWARF信息并添加到对应的帧
        # 简化实现，标记已添加
        for frame in frames:
            frame["dwarf_info"] = True

        return frames

    async def _add_symbols(
        self, frames: List[Dict[str, Any]], symbols_path: str
    ) -> List[Dict[str, Any]]:
        """添加符号信息"""
        # 这里应该加载符号文件并解析
        # 简化实现，标记已添加
        for frame in frames:
            frame["symbols_loaded"] = True

        return frames

    async def _analyze_stack_trace(self, frames: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析栈回溯"""
        analysis = {
            "crash_frame": None,
            "recursive_calls": [],
            "tail_calls": [],
            "call_depth": len(frames),
            "functions": set(),
        }

        # 查找崩溃帧
        for frame in frames:
            # 通常崩溃帧包含特定的信号信息
            if "signal" in str(frame.get("function", "")).lower():
                analysis["crash_frame"] = frame["number"]
                break

        # 检查递归调用
        functions_seen = {}
        for frame in frames:
            func = frame.get("function")
            if func:
                if func in functions_seen:
                    # 重复调用
                    analysis["recursive_calls"].append({
                        "function": func,
                        "frames": [functions_seen[func], frame["number"]],
                    })
                functions_seen[func] = frame["number"]

        # 检查尾调用
        for i in range(len(frames) - 1):
            current = frames[i]
            next_frame = frames[i + 1]

            # 简单的尾调用检测
            current_func = current.get("function")
            next_func = next_frame.get("function")

            if (current_func and next_func and
                current_func != next_func and
                self._is_tail_call(current, next_frame)):
                analysis["tail_calls"].append({
                    "from": current_func,
                    "to": next_func,
                    "frame": current["number"],
                })

        return analysis

    def _is_tail_call(self, current_frame: Dict[str, Any], next_frame: Dict[str, Any]) -> bool:
        """检查是否是尾调用"""
        # 简化的尾调用检测
        # 在实际实现中，需要检查函数调用是否是最后一条指令
        return True

    def format_stack_trace(self, frames: List[Dict[str, Any]], format_type: str = "text") -> str:
        """格式化栈回溯"""
        if format_type == "text":
            return self._format_text(frames)
        elif format_type == "json":
            return json.dumps(frames, indent=2)
        elif format_type == "html":
            return self._format_html(frames)
        else:
            raise ValueError(f"不支持的格式: {format_type}")

    def _format_text(self, frames: List[Dict[str, Any]]) -> str:
        """格式化为文本"""
        output = []

        for frame in frames:
            output.append(f"#{frame.get('number', 0)} {frame.get('address', '???')} in {frame.get('function', '???')}")

            if frame.get("file"):
                output.append(f"  {frame['file']}:{frame.get('line', '?')}")

            if frame.get("demangled"):
                output.append(f"  [demangled] {frame['demangled']}")

            output.append("")

        return "\n".join(output)

    def _format_html(self, frames: List[Dict[str, Any]]) -> str:
        """格式化为HTML"""
        html = ["<html><body><pre>"]

        for frame in frames:
            html.append(f"<div class='frame'>")
            html.append(f"<span class='number'>#{frame.get('number', 0)}</span> ")
            html.append(f"<span class='address'>{frame.get('address', '???')}</span> ")
            html.append(f"<span class='function'>{frame.get('function', '???')}</span>")

            if frame.get("file"):
                html.append(f"<div class='location'>{frame['file']}:{frame.get('line', '?')}</div>")

            if frame.get("demangled"):
                html.append(f"<div class='demangled'>[demangled] {frame['demangled']}</div>")

            html.append("</div>")

        html.append("</pre></body></html>")
        return "\n".join(html)