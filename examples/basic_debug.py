"""
基本调试示例
"""

import asyncio
from autogdb_agent import Agent
from autogdb_agent.core.message import Message, MessageRole


async def main():
    """基本调试示例"""
    # 创建代理
    agent = Agent()
    await agent.start()

    try:
        # 创建调试会话
        session = await agent.create_session(
            "basic_debug",
            debug_target="/path/to/target",
            debug_type="gdb"
        )

        # 发送调试命令
        response = await session.process_message(
            Message(MessageRole.USER, "启动调试器并加载目标")
        )
        print("响应:", response.content)

        # 执行一些调试命令
        commands = [
            "info registers",
            "bt",
            "x/10i $pc"
        ]

        for cmd in commands:
            response = await agent.execute_command("basic_debug", cmd)
            print(f"命令 '{cmd}' 的结果:", response)

    finally:
        await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())