# AutoGDB Agent 使用指南

## 目录

1. [基础使用](#基础使用)
2. [协议使用](#协议使用)
3. [工作流使用](#工作流使用)
4. [插件开发](#插件开发)
5. [调试场景](#调试场景)

---

## 基础使用

### 启动调试会话

```bash
# 调试任意程序
autogdb-agent debug -t /usr/bin/nginx -p ./requests/

# 使用特定调试器
autogdb-agent debug -t ./my_program -d gdb --debug-gdb

# 指定配置文件
autogdb-agent --config custom_config.yaml debug -t /path/to/binary
```

### Python API 使用

```python
import asyncio
from autogdb_agent import Agent
from autogdb_agent.core.message import Message, MessageRole

async def debug_program():
    # 创建代理
    agent = Agent()
    await agent.start()

    try:
        # 创建调试会话
        session = await agent.create_session(
            "debug_session",
            debug_target="./my_program",
            debug_type="gdb"
        )

        # 发送调试命令
        response = await session.process_message(
            Message(MessageRole.USER, "开始调试")
        )
        print(response.content)

        # 执行GDB命令
        commands = ["info registers", "bt", "x/10i $pc"]
        for cmd in commands:
            result = await agent.execute_command("debug_session", cmd)
            print(f"命令 '{cmd}':")
            print(result)
            print()

    finally:
        await agent.stop()

asyncio.run(debug_program())
```

## 协议使用

### TCP 协议

```python
# 通过协议发送工具发送TCP数据
result = await agent.execute_tool(
    "protocol_sender",
    protocol="tcp",
    target="localhost",
    port=8080,
    data="hello world"
)

print(f"发送成功: {result}")
```

### UDP 协议

```python
result = await agent.execute_tool(
    "protocol_sender",
    protocol="udp",
    target="localhost",
    port=53,
    data="dns query"
)
```

### HTTP 协议

```python
# 发送HTTP请求
result = await agent.execute_tool(
    "protocol_sender",
    protocol="http",
    target="http://localhost:8080/api/test",
    data='{"key": "value"}',
    method="POST"
)

# 带JSON数据的HTTP请求
result = await agent.execute_tool(
    "protocol_sender",
    protocol="http",
    target="http://localhost/api",
    json={"command": "test", "params": {"value": 123}}
)
```

### WebSocket 协议

```python
# WebSocket发送（需要实现WebSocket协议插件）
result = await agent.execute_tool(
    "protocol_sender",
    protocol="websocket",
    target="ws://localhost:8080/ws",
    data="connected"
)
```

## 工作流使用

### 使用预定义工作流

```yaml
# 在配置文件中定义工作流
workflows:
  auto_debug:
    name: "自动调试"
    description: "自动调试工作流"
    steps:
      - action: "analyze"
        plugin: "crash_analyzer"
      - action: "debug"
        plugin: "debugger"
```

```python
# 执行工作流
runner = ToolRunner()
results = await runner.run_workflow("auto_debug", binary_path="./target")

print(f"工作流执行结果: {results['success']}")
for step in results["steps"]:
    print(f"步骤 {step['action']}: {'成功' if step['success'] else '失败'}")
```

### 自定义工作流

```python
# 创建自定义工作流
custom_workflow = {
    "name": "我的调试工作流",
    "description": "我的自定义调试流程",
    "steps": [
        {
            "action": "initialize",
            "plugin": "debugger",
            "params": {"target": "./my_program"}
        },
        {
            "action": "analyze",
            "plugin": "crash_analyzer",
            "params": {"analysis_level": "deep"}
        },
        {
            "action": "execute",
            "plugin": "debugger",
            "params": {"command": "run"}
        },
        {
            "action": "send_poc",
            "plugin": "poc_sender",
            "params": {"target": "udp://localhost:47808"}
        }
    ]
}
```

## 插件开发

### 创建自定义调试器插件

```python
# plugins/custom_debugger.py
import asyncio
from autogdb_agent.core.plugin import Plugin
from autogdb_agent.tools.debugger import DebuggerTool

class CustomDebuggerPlugin(Plugin):
    """自定义调试器插件"""

    name = "custom_debugger"
    type = "debugger"
    description = "我的自定义调试器"
    version = "1.0.0"

    def __init__(self, config=None):
        super().__init__(config)
        self.debugger = None

    async def initialize(self):
        """初始化调试器"""
        self.logger.info("初始化自定义调试器")

        # 创建调试器实例
        self.debugger = DebuggerTool(self.config)
        await self.debugger.initialize()

    async def execute(self, **kwargs):
        """执行调试操作"""
        action = kwargs.get("action")

        if action == "start":
            target = kwargs.get("target")
            return await self.debugger.start(target)

        elif action == "stop":
            return await self.debugger.stop()

        elif action == "execute":
            command = kwargs.get("command")
            return await self.debugger.execute_command(command)

        elif action == "status":
            return await self.debugger.get_status()

        return {"status": "unknown action"}

    async def cleanup(self):
        """清理资源"""
        if self.debugger:
            await self.debugger.close()
```

### 创建自定义协议插件

```python
# plugins/protocols/my_protocol.py
import asyncio
from autogdb_agent.plugins.protocols.base import ProtocolPlugin

class MyCustomProtocol(ProtocolPlugin):
    """自定义协议插件"""

    name = "my_custom_protocol"
    type = "protocol"
    description = "我的自定义协议"
    version = "1.0.0"

    async def initialize(self):
        """初始化协议"""
        self.logger.info("初始化自定义协议")

    async def connect(self, target, **kwargs):
        """连接到目标"""
        self.target = target
        self.connected = True
        return True

    async def send(self, data, **kwargs):
        """发送数据"""
        # 实现发送逻辑
        response = b"response"
        return response

    async def disconnect(self):
        """断开连接"""
        self.connected = False

    async def close(self):
        """关闭协议"""
        await self.disconnect()
```

## 调试场景

### 场景1: 调试Web服务器

```python
async def debug_web_server():
    agent = Agent()
    await agent.start()

    try:
        # 1. 启动调试器
        session = await agent.create_session(
            "web_debug",
            debug_target="/usr/sbin/nginx",
            debug_type="gdb"
        )

        # 2. 执行GDB命令
        await agent.execute_command("web_debug", "file /usr/sbin/nginx")
        await agent.execute_command("web_debug", "run")

        # 3. 发送HTTP请求
        result = await agent.execute_tool(
            "protocol_sender",
            protocol="http",
            target="http://localhost",
            data="GET / HTTP/1.1\r\n\r\n"
        )

        print(f"HTTP响应: {result}")

        # 4. 分析崩溃
        analyzer = CrashAnalyzerTool()
        crash_analysis = await analyzer.execute(
            crash_output=result,
            analysis_type="detailed"
        )

        print(f"分析结果: {crash_analysis}")

    finally:
        await agent.stop()
```

### 场景2: 自动化模糊测试

```python
async def fuzzing_workflow():
    agent = Agent()
    await agent.start()

    try:
        # 1. 准备POC数据
        pocs = ["poc1.bin", "poc2.bin", "poc3.bin"]

        # 2. 模糊测试
        for poc in pocs:
            print(f"测试POC: {poc}")

            # 发送POC
            result = await agent.execute_tool(
                "protocol_sender",
                protocol="tcp",
                target="localhost",
                port=8080,
                data=open(poc, "rb").read()
            )

            # 检查结果
            if result.get("success"):
                print(f"✓ POC {poc} 发送成功")
            else:
                print(f"✗ POC {poc} 发送失败")

    finally:
        await agent.stop()
```

### 场景3: 内存分析

```python
async def memory_analysis():
    agent = Agent()
    await agent.start()

    try:
        # 创建调试会话
        session = await agent.create_session("mem_analysis")

        # 读取内存
        result = await agent.execute_command(
            "mem_analysis",
            "x/10i $pc"
        )

        print(f"内存转储: {result}")

        # 分析内存
        inspector = MemoryInspectorTool()
        memory_analysis = await inspector.execute(
            address="0x4001000",
            size=64,
            format="hex"
        )

        print(f"内存分析: {memory_analysis}")

    finally:
        await agent.stop()
```

### 场景4: 多协议攻击测试

```python
async def multi_protocol_test():
    agent = Agent()
    await agent.start()

    try:
        # TCP测试
        tcp_result = await agent.execute_tool(
            "protocol_sender",
            protocol="tcp",
            target="target",
            port=80,
            data="test"
        )

        # UDP测试
        udp_result = await agent.execute_tool(
            "protocol_sender",
            protocol="udp",
            target="target",
            port=53,
            data="test"
        )

        # HTTP测试
        http_result = await agent.execute_tool(
            "protocol_sender",
            protocol="http",
            target="http://target",
            data="test"
        )

        print("多协议测试结果:")
        print(f"TCP: {tcp_result.get('success')}")
        print(f"UDP: {udp_result.get('success')}")
        print(f"HTTP: {http_result.get('success')}")

    finally:
        await agent.stop()
```

## 故障排除

### 常见问题

1. **调试器连接失败**
   - 检查调试器路径是否正确
   - 确保目标文件存在
   - 查看详细日志

2. **协议发送失败**
   - 验证目标地址和端口
   - 检查网络连接
   - 确认协议配置

3. **LLM API调用失败**
   - 检查API密钥配置
   - 验证网络连接
   - 确认API配额

### 调试模式

```bash
# 启用详细日志
export AUTOAGENT_DEBUG=1
autogdb-agent debug -t ./binary

# 使用配置文件调试
autogdb-agent --config debug_config.yaml debug -t ./binary
```