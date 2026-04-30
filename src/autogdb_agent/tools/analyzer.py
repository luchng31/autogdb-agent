"""
Crash Analyzer Tool - 崩溃分析工具
"""

import re
from typing import Any, Dict, List, Optional

from .base import Tool
from ..core.exceptions import ToolError


class CrashAnalyzerTool(Tool):
    """
    崩溃分析工具
    分析崩溃转储和GDB输出
    """

    tool_name = "crash_analyzer"
    category = "analyzer"
    description = "分析程序崩溃信息"
    version = "1.0.0"

    # 参数定义
    parameters = {
        "type": "object",
        "properties": {
            "crash_output": {
                "type": "string",
                "description": "崩溃输出",
            },
            "stack_trace": {
                "type": "string",
                "description": "栈回溯",
            },
            "memory_dump": {
                "type": "string",
                "description": "内存转储",
            },
            "analysis_type": {
                "type": "string",
                "enum": ["basic", "detailed", "deep"],
                "default": "detailed",
                "description": "分析深度",
            },
        },
        "required": ["crash_output"],
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)

        # 崩溃模式
        self.crash_patterns = {
            "null_deref": {
                "patterns": [
                    r"0x0",
                    r"NULL",
                    r"null pointer",
                    r"access violation",
                ],
                "description": "空指针解引用",
            },
            "buffer_overflow": {
                "patterns": [
                    r"out of bounds",
                    r"buffer overflow",
                    r"index out of range",
                    r"subscript out of range",
                ],
                "description": "缓冲区溢出",
            },
            "use_after_free": {
                "patterns": [
                    r"use after free",
                    r"dangling pointer",
                    r"double free",
                ],
                "description": "释放后使用",
            },
            "stack_overflow": {
                "patterns": [
                    r"stack overflow",
                    r"segmentation fault",
                    r"stack smashing",
                ],
                "description": "栈溢出",
            },
            "heap_corruption": {
                "patterns": [
                    r"heap corruption",
                    r"corrupted double-linked list",
                    r"malloc",
                    r"free",
                ],
                "description": "堆损坏",
            },
        }

        # 分析规则
        self.analysis_rules = {
            "check_rip": self._check_rip_address,
            "check_signal": self._check_signal,
            "check_stack": self._check_stack_trace,
            "check_registers": self._check_registers,
            "suggest_commands": self._suggest_commands,
        }

    async def execute(self, **kwargs) -> Any:
        """
        执行崩溃分析

        Args:
            **kwargs: 参数

        Returns:
            分析结果
        """
        crash_output = kwargs.get("crash_output", "")
        stack_trace = kwargs.get("stack_trace", "")
        memory_dump = kwargs.get("memory_dump", "")
        analysis_type = kwargs.get("analysis_type", "detailed")

        # 基本分析
        analysis = {
            "timestamp": self._get_timestamp(),
            "crash_type": self._detect_crash_type(crash_output),
            "location": self._extract_crash_location(crash_output),
            "signal": self._extract_signal(crash_output),
            "registers": self._extract_registers(crash_output),
            "stack_trace": self._parse_stack_trace(stack_trace) if stack_trace else [],
        }

        # 详细分析
        if analysis_type in ["detailed", "deep"]:
            analysis.update({
                "memory_analysis": self._analyze_memory(memory_dump),
                "call_stack": self._analyze_call_stack(crash_output),
                "potential_causes": self._identify_causes(crash_output, analysis),
                "suggested_commands": self._suggest_debug_commands(analysis),
            })

        # 深度分析
        if analysis_type == "deep":
            analysis.update({
                "exploitability": self._assess_exploitability(analysis),
                "mitigation_suggestions": self._suggest_mitigations(analysis),
                "similar_patterns": self._find_similar_patterns(analysis),
            })

        # 添加元数据
        analysis["analysis_type"] = analysis_type
        analysis["input_length"] = len(crash_output)
        analysis["processing_time"] = self._get_processing_time()

        return analysis

    def _detect_crash_type(self, crash_output: str) -> str:
        """检测崩溃类型"""
        crash_output_lower = crash_output.lower()

        for crash_type, info in self.crash_patterns.items():
            for pattern in info["patterns"]:
                if re.search(pattern, crash_output_lower):
                    return crash_type

        return "unknown"

    def _extract_crash_location(self, crash_output: str) -> Dict[str, Any]:
        """提取崩溃位置"""
        location = {
            "function": None,
            "file": None,
            "line": None,
            "address": None,
        }

        # 提取函数名
        func_match = re.search(r"in\s+([^\s(]+)", crash_output)
        if func_match:
            location["function"] = func_match.group(1)

        # 提取地址
        addr_match = re.search(r"rip\s+0x([0-9a-f]+)", crash_output, re.IGNORECASE)
        if addr_match:
            location["address"] = addr_match.group(1)

        # 提取文件和行号
        file_match = re.search(r"at\s+([^:]+):(\d+)", crash_output)
        if file_match:
            location["file"] = file_match.group(1)
            location["line"] = int(file_match.group(2))

        return location

    def _extract_signal(self, crash_output: str) -> str:
        """提取信号"""
        signal_match = re.search(r"Program received signal (\S+)", crash_output)
        if signal_match:
            return signal_match.group(1)
        return "unknown"

    def _extract_registers(self, crash_output: str) -> Dict[str, str]:
        """提取寄存器值"""
        registers = {}

        # 提取通用寄存器
        reg_patterns = [
            (r"rax\s+0x([0-9a-f]+)", "rax"),
            (rb"rbx\s+0x([0-9a-f]+)", "rbx"),
            (rc"rcx\s+0x([0-9a-f]+)", "rcx"),
            (rd"rdx\s+0x([0-9a-f]+)", "rdx"),
            (r"rsp\s+0x([0-9a-f]+)", "rsp"),
            (r"rbp\s+0x([0-9a-f]+)", "rbp"),
            (r"rsi\s+0x([0-9a-f]+)", "rsi"),
            (r"rdi\s+0x([0-9a-f]+)", "rdi"),
        ]

        for pattern, reg_name in reg_patterns:
            match = re.search(pattern, crash_output, re.IGNORECASE)
            if match:
                registers[reg_name] = match.group(1)

        return registers

    def _parse_stack_trace(self, stack_trace: str) -> List[Dict[str, Any]]:
        """解析栈回溯"""
        frames = []

        # 分割帧
        frame_matches = re.finditer(r"#(\d+)\s+0x([0-9a-f]+) in\s+([^\s(]+)", stack_trace)

        for match in frame_matches:
            frame_num = match.group(1)
            address = match.group(2)
            function = match.group(3)

            frame = {
                "frame": int(frame_num),
                "address": address,
                "function": function,
                "source": None,
            }

            # 尝试提取源文件信息
            src_match = re.search(r"(.+):(\d+)", function)
            if src_match:
                frame["source"] = {
                    "file": src_match.group(1),
                    "line": int(src_match.group(2)),
                }

            frames.append(frame)

        return frames

    def _analyze_memory(self, memory_dump: str) -> Dict[str, Any]:
        """分析内存"""
        analysis = {
            "corrupted_pointers": 0,
            "null_pointers": 0,
            "suspicious_values": [],
        }

        if memory_dump:
            # 检查损坏的指针
            null_ptr = re.findall(r"0x0", memory_dump)
            analysis["null_pointers"] = len(null_ptr)

            # 检查可疑值
            suspicious = re.findall(r"0x[0-9a-f]{8,}", memory_dump)
            analysis["suspicious_values"] = suspicious[:10]  # 限制数量

        return analysis

    def _analyze_call_stack(self, crash_output: str) -> Dict[str, Any]:
        """分析调用栈"""
        return {
            "depth": self._count_stack_depth(crash_output),
            "recursive_calls": self._check_recursive_calls(crash_output),
            "tail_calls": self._check_tail_calls(crash_output),
        }

    def _identify_causes(self, crash_output: str, analysis: Dict) -> List[str]:
        """识别可能的原因"""
        causes = []

        # 基于崩溃类型
        crash_type = analysis.get("crash_type")
        if crash_type == "null_deref":
            causes.append("空指针解引用")
            causes.append("未初始化的指针")
        elif crash_type == "buffer_overflow":
            causes.append("缓冲区溢出")
            causes.append("数组越界访问")
        elif crash_type == "use_after_free":
            causes.append("释放后使用")
            causes.append("双重释放")

        # 基于信号
        signal = analysis.get("signal")
        if signal == "SIGSEGV":
            causes.append("段错误")
            causes.append("内存访问违规")
        elif signal == "SIGABRT":
            causes.append("程序异常终止")
            causes.append("断言失败")

        return causes

    def _suggest_debug_commands(self, analysis: Dict) -> List[str]:
        """建议调试命令"""
        commands = []

        # 基本命令
        commands.append("bt full")
        commands.append("info registers")

        # 崩溃类型特定命令
        crash_type = analysis.get("crash_type")
        if crash_type == "null_deref":
            commands.append("frame 0")
            commands.append("info locals")
        elif crash_type == "buffer_overflow":
            commands.append("x/20x $rsp")
            commands.append("info frame")

        return commands

    def _assess_exploitability(self, analysis: Dict) -> Dict[str, Any]:
        """评估可利用性"""
        score = 0
        factors = []

        # 检查是否可写内存
        if analysis.get("crash_type") == "buffer_overflow":
            score += 30
            factors.append("缓冲区溢出可能允许代码执行")

        # 检查控制流劫持
        stack_trace = analysis.get("stack_trace", [])
        if len(stack_trace) > 0:
            score += 20
            factors.append("栈回溯显示控制流可能被劫持")

        # 检查内存损坏
        mem_analysis = analysis.get("memory_analysis", {})
        if mem_analysis.get("suspicious_values"):
            score += 25
            factors.append("检测到可疑的内存值")

        return {
            "score": min(score, 100),
            "risk_level": self._get_risk_level(score),
            "factors": factors,
        }

    def _get_risk_level(self, score: int) -> str:
        """获取风险等级"""
        if score >= 70:
            return "high"
        elif score >= 40:
            return "medium"
        else:
            return "low"

    def _suggest_mitigations(self, analysis: Dict) -> List[str]:
        """建议缓解措施"""
        mitigations = []

        crash_type = analysis.get("crash_type")
        if crash_type == "null_deref":
            mitigations.append("添加空指针检查")
            mitigations.append("使用智能指针")
        elif crash_type == "buffer_overflow":
            mitigations.append("使用边界检查")
            mitigations.append("启用栈保护")
        elif crash_type == "use_after_free":
            mitigations.append("使用弱引用")
            mitigations.append("实现引用计数")

        return mitigations

    def _find_similar_patterns(self, analysis: Dict) -> List[str]:
        """查找相似模式"""
        # 这里可以集成数据库或CVE搜索
        return [
            "检查是否有已知的CVE与此崩溃模式匹配",
            "查看类似的开源项目是否有类似问题",
        ]

    def _count_stack_depth(self, crash_output: str) -> int:
        """计算栈深度"""
        frame_matches = re.findall(r"#(\d+)\s+", crash_output)
        return len(frame_matches) if frame_matches else 0

    def _check_recursive_calls(self, crash_output: str) -> bool:
        """检查递归调用"""
        # 简单检查是否有函数重复调用
        functions = re.findall(r"in\s+([^\s(]+)", crash_output)
        return len(functions) != len(set(functions))

    def _check_tail_calls(self, crash_output: str) -> bool:
        """检查尾调用"""
        # 这里可以实现更复杂的检测逻辑
        return False

    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()

    def _get_processing_time(self) -> float:
        """获取处理时间"""
        import time
        return time.time()