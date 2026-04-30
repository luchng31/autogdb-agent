"""
崩溃分析示例
"""

import asyncio
from autogdb_agent import Agent
from autogdb_agent.core.message import Message, MessageRole


async def main():
    """崩溃分析示例"""
    # 创建代理
    agent = Agent()
    await agent.start()

    try:
        # 创建会话
        session = await agent.create_session("crash_analysis")

        # 模拟崩溃输出
        crash_output = """
Program received signal SIGSEGV, Segmentation fault.
0x0000000000401000 in main () at test.c:10
10          int *ptr = NULL;
11          *ptr = 42;
(gdb)
"""

        # 发送到分析器
        from autogdb_agent.tools.analyzer import CrashAnalyzerTool

        analyzer = CrashAnalyzerTool()
        result = await analyzer.execute(
            crash_output=crash_output,
            analysis_type="detailed"
        )

        print("崩溃分析结果:")
        print(f"崩溃类型: {result['crash_type']}")
        print(f"位置: {result['location']}")
        print(f"信号: {result['signal']}")
        print(f"潜在原因: {', '.join(result['potential_causes'])}")
        print(f"建议命令: {result['suggested_commands']}")

    finally:
        await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())