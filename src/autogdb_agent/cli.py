"""
CLI - 命令行接口
"""

import asyncio
import json
import time
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from .core.agent import Agent
from .core.config import Config
from .utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


@click.group()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="配置文件路径",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="详细输出",
)
@click.pass_context
def cli(ctx, config, verbose):
    """AutoGDB Agent - 智能调试助手"""
    ctx.ensure_object(dict)

    # 加载配置
    config_path = Path(config) if config else None
    ctx.obj["config"] = Config(config_path)
    ctx.obj["verbose"] = verbose


@cli.command()
@click.pass_context
def init(ctx):
    """初始化AutoGDB Agent"""
    config = ctx.obj["config"]

    console.print("🚀 初始化 AutoGDB Agent...")

    # 创建配置文件
    if not config.config_path.exists():
        config.save()
        console.print(f"✅ 配置文件已创建: {config.config_path}")
    else:
        console.print(f"ℹ️  配置文件已存在: {config.config_path}")

    # 创建必要的目录
    directories = [
        Path.home() / ".autogdb-agent" / "plugins",
        Path.home() / ".autogdb-agent" / "logs",
        Path.home() / ".autogdb-agent" / "sessions",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        console.print(f"✅ 创建目录: {directory}")

    console.print("🎉 初始化完成！")


@cli.command()
@click.option(
    "--session-id",
    "-s",
    help="会话ID",
)
@click.option(
    "--debug-target",
    "-t",
    required=True,
    help="调试目标",
)
@click.option(
    "--debug-type",
    help="调试类型 (gdb, lldb)",
    default="gdb",
)
@click.pass_context
async def debug(ctx, session_id, debug_target, debug_type):
    """启动调试会话"""
    config = ctx.obj["config"]
    verbose = ctx.obj["verbose"]

    # 生成会话ID
    if not session_id:
        session_id = f"debug_{int(time.time())}"

    console.print(f"🔍 启动调试会话: {session_id}")

    # 创建代理
    agent = Agent(config)
    await agent.start()

    try:
        # 创建会话
        session = await agent.create_session(
            session_id,
            debug_target=debug_target,
            debug_type=debug_type,
        )

        # 启动调试
        await session.process_message(
            create_message("user", f"开始调试: {debug_target}")
        )

        # 简单的交互循环
        while session.status not in ["completed", "failed"]:
            user_input = console.input("\n>>> ")

            if user_input.lower() in ["quit", "exit", "q"]:
                break

            if user_input.startswith("/"):
                # 处理命令
                response = await session.process_message(
                    create_message("user", user_input)
                )
            else:
                # 发送调试命令
                response = await session.process_message(
                    create_message("user", user_input)
                )

            console.print(f"[bold green]{response.content}[/bold green]")

    finally:
        await agent.stop()


@cli.command()
@click.option(
    "--interactive",
    "-i",
    is_flag=True,
    help="交互模式",
)
@click.pass_context
async def interactive(ctx, interactive):
    """交互式调试"""
    config = ctx.obj["config"]

    console.print("🎮 进入交互模式")

    # 创建代理
    agent = Agent(config)
    await agent.start()

    try:
        # 创建会话
        session = await agent.create_session("interactive")

        if interactive:
            # 交互式界面
            while True:
                user_input = console.input("\n[bold blue]User:[/bold blue] ")

                if user_input.lower() in ["quit", "exit", "q"]:
                    break

                response = await session.process_message(
                    create_message("user", user_input)
                )

                console.print(f"\n[bold green]Assistant:[/bold green] {response.content}")

    finally:
        await agent.stop()


@cli.command()
@click.pass_context
def plugins(ctx):
    """列出所有插件"""
    config = ctx.obj["config"]

    # 创建代理
    agent = Agent(config)
    loop = asyncio.get_event_loop()

    try:
        plugins_info = loop.run_until_complete(agent.list_plugins())

        table = Table(title="插件列表")
        table.add_column("名称", style="cyan", no_wrap=True)
        table.add_column("类型", style="magenta")
        table.add_column("描述", style="green")
        table.add_column("版本", style="yellow")
        table.add_column("已加载", justify="center", style="blue")

        for plugin in plugins_info:
            table.add_row(
                plugin["name"],
                plugin.get("type", "general"),
                plugin.get("description", "-"),
                plugin.get("version", "1.0.0"),
                "✅" if plugin["instance_loaded"] else "❌",
            )

        console.print(table)

    finally:
        loop.run_until_complete(agent.stop())


@cli.command()
@click.pass_context
def tools(ctx):
    """列出所有工具"""
    config = ctx.obj["config"]

    # 创建代理
    agent = Agent(config)
    loop = asyncio.get_event_loop()

    try:
        tools_info = loop.run_until_complete(agent.list_tools())

        table = Table(title="工具列表")
        table.add_column("名称", style="cyan", no_wrap=True)
        table.add_column("类别", style="magenta")
        table.add_column("描述", style="green")
        table.add_column("版本", style="yellow")
        table.add_column("已加载", justify="center", style="blue")

        for tool in tools_info:
            table.add_row(
                tool["name"],
                tool.get("category", "general"),
                tool.get("description", "-"),
                tool.get("version", "1.0.0"),
                "✅" if tool["instance_loaded"] else "❌",
            )

        console.print(table)

    finally:
        loop.run_until_complete(agent.stop())


@cli.command()
@click.pass_context
async def status(ctx):
    """查看状态"""
    config = ctx.obj["config"]

    # 创建代理
    agent = Agent(config)
    await agent.start()

    try:
        status_info = await agent.get_status()

        console.print("📊 AutoGDB Agent 状态")
        console.print(f"运行状态: {'运行中' if status_info['running'] else '已停止'}")
        console.print(f"启动时间: {status_info.get('start_time', 'N/A')}")
        console.print(f"运行时长: {status_info.get('uptime', 0):.2f} 秒")
        console.print(f"活跃会话: {status_info['sessions']}")
        console.print(f"已加载插件: {status_info['plugins']}")
        console.print(f"已加载工具: {status_info['tools']}")
        console.print(f"会话ID: {', '.join(status_info['session_ids'])}")

    finally:
        await agent.stop()


@cli.command()
@click.argument("command")
@click.option(
    "--session-id",
    "-s",
    help="会话ID",
)
@click.pass_context
async def exec(ctx, command, session_id):
    """执行命令"""
    config = ctx.obj["config"]

    # 创建代理
    agent = Agent(config)
    await agent.start()

    try:
        if not session_id:
            # 创建新会话
            session_id = "temp"
            session = await agent.create_session(session_id)
        else:
            session = await agent.get_session(session_id)
            if not session:
                console.print(f"❌ 会话不存在: {session_id}")
                return

        # 执行命令
        result = await agent.execute_command(session_id, command)

        console.print("🎯 执行结果:")
        console.print(json.dumps(result, indent=2, ensure_ascii=False))

    finally:
        await agent.stop()


def create_message(role, content):
    """创建消息"""
    from .core.message import Message, MessageRole
    return Message(MessageRole(role), content)


def main():
    """CLI entry point"""
    cli()


if __name__ == "__main__":
    main()