# AutoGDB Agent - 通用智能调试平台

一个基于大语言模型的通用智能调试平台，支持多种调试器、协议和目标类型。灵感源自Claude Code，提供插件化架构和丰富的扩展能力。

## 🌟 核心特性

- **通用调试器支持**: GDB, LLDB, WinDbg及自定义调试器
- **多协议支持**: TCP, UDP, HTTP, WebSocket, BACnet
- **智能崩溃分析**: 基于LLM的自动分析和建议
- **工作流引擎**: 预定义和自定义调试工作流
- **丰富的工具集**: 内存分析、反汇编、栈回溯等
- **插件化架构**: 灵活扩展新的调试器和协议
- **可视化输出**: HTML/JSON格式的调试报告

## 🏗️ 架构设计

### 核心组件

1. **Agent Core**: 智能代理核心，协调各组件工作
2. **Plugin System**: 插件系统，支持自定义调试器和分析器
3. **Tool Registry**: 工具注册中心，管理调试工具
4. **Session Manager**: 会话管理器，管理调试会话
5. **Communication Hub**: 通信中心，处理数据交换
6. **Configuration Manager**: 配置管理器，支持多环境配置
7. **Tool Runner**: 工具执行器，协调各种工具

### 工具生态系统

#### 调试器工具
- **Debugger Tool**: 通用GDB/LLDB接口
- 支持ELF, PE, MachO等多种目标格式
- 自动初始化和命令执行

#### 协议工具
- **Protocol Sender Tool**: 支持TCP/UDP/HTTP协议
- 可扩展的协议插件系统
- 支持自定义协议

#### 分析工具
- **Crash Analyzer**: 智能崩溃分析
- **Memory Inspector**: 内存状态检查
- **Stack Trace**: 栈回溯分析
- **Disassembler**: 代码反汇编

## 📦 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/luchng31/autogdb-agent.git
cd autogdb-agent

# 安装依赖
pip install -e .

# 初始化配置
autogdb-agent init
```

### 基本使用

```bash
# 启动调试会话
autogdb-agent debug -t /path/to/binary -p ./pocs/

# 使用自定义协议发送
autogdb-agent send --protocol tcp --target localhost --port 8080 --data "test"

# 查看可用工具
autogdb-agent tools list

# 查看工作流
autogdb-agent workflows list

# 查看状态
autogdb-agent status
```

## 🔧 配置

配置文件位于 `~/.autogdb-agent/config.yaml` 或项目根目录：

### 基本配置示例

```yaml
# 调试器配置
debuggers:
  gdb:
    path: "/usr/bin/gdb"
    prompt_pattern: r"\(gdb\)"
    init_commands:
      - "set pagination off"

# 协议配置
protocols:
  tcp:
    enabled: true
    default_port: 80
    timeout: 5

  udp:
    enabled: true
    default_port: 53
    timeout: 3

  http:
    enabled: true
    method: "POST"
    timeout: 30

# LLM配置
llm:
  provider: "anthropic"
  api_key: "your-api-key"
  model: "claude-3-opus"
```

## 📚 工具使用

### 1. 调试器工具

```python
from autogdb_agent import Agent

agent = Agent()
session = await agent.create_session("debug_session")

# 执行调试器命令
result = await agent.execute_command("debug_session", "info registers")
print(result)
```

### 2. 协议发送工具

```python
# TCP协议
result = await agent.execute_tool(
    "protocol_sender",
    protocol="tcp",
    target="localhost",
    port=8080,
    data="hello"
)

# HTTP协议
result = await agent.execute_tool(
    "protocol_sender",
    protocol="http",
    target="http://localhost/api",
    data='{"key": "value"}'
)
```

### 3. 崩溃分析

```python
analyzer = CrashAnalyzerTool()
analysis = await analyzer.execute(
    crash_output=crash_data,
    analysis_type="detailed"
)

print(f"崩溃类型: {analysis['crash_type']}")
print(f"位置: {analysis['location']}")
```

## 🎯 支持的目标类型

- **ELF**: Linux/Unix可执行文件
- **PE**: Windows可执行文件
- **MachO**: macOS可执行文件
- **Core**: Core dump文件
- **Runtime**: 运行时程序

## 📚 支持的协议

- **TCP**: 传输控制协议
- **UDP**: 用户数据报协议
- **HTTP**: 超文本传输协议
- **WebSocket**: 实时双向通信
- **BACnet**: 保留支持

## 🚀 高级功能

### 工作流系统

```yaml
workflows:
  fuzzing:
    name: "模糊测试"
    steps:
      - action: "fuzz"
        plugin: "poc_sender"
      - action: "collect_crashes"
        plugin: "crash_collector"
      - action: "debug"
        plugin: "debugger"
```

### 插件开发

创建自定义调试器插件：

```python
from autogdb_agent.core.plugin import Plugin
from autogdb_agent.tools.debugger import DebuggerTool

class MyDebuggerPlugin(Plugin):
    name = "my_debugger"
    type = "debugger"
    description = "我的自定义调试器"

    async def initialize(self):
        # 初始化调试器
        pass

    async def execute(self, **kwargs):
        debugger = DebuggerTool(self.config)
        await debugger.initialize()
        return await debugger.execute(**kwargs)

    async def cleanup(self):
        # 清理资源
        pass
```

### 自定义协议

```python
from autogdb_agent.plugins.protocols.base import ProtocolPlugin

class MyProtocol(ProtocolPlugin):
    name = "my_protocol"
    description = "我的自定义协议"

    async def connect(self, target, **kwargs):
        # 实现连接逻辑
        pass

    async def send(self, data, **kwargs):
        # 实现发送逻辑
        pass
```

## 📊 可视化

调试结果支持多种输出格式：

- **HTML**: 完整的调试报告，包含图表和可视化
- **JSON**: 结构化的调试数据
- **JSON Lines**: 流式调试数据

## 🔒 安全性

- 不在代码中硬编码API密钥
- 支持环境变量配置
- 配置文件加密存储（可选）
- 敏感信息过滤

## 🤝 贡献

欢迎贡献代码！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 📄 许可证

MIT License - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📖 文档

- [项目结构](PROJECT_STRUCTURE.md)
- [配置说明](config/)