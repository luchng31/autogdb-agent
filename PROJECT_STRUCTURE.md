# AutoGDB Agent 项目结构

```
autogdb-agent/
├── README.md                    # 项目说明文档
├── pyproject.toml              # 项目配置和依赖
├── config/
│   └── default.yaml           # 默认配置文件
├── development.yaml           # 开发环境配置
├── src/
│   └── autogdb_agent/
│       ├── __init__.py         # 包初始化
│       ├── cli.py             # 命令行接口
│       ├── core/              # 核心组件
│       │   ├── __init__.py
│       │   ├── agent.py       # 智能代理核心
│       │   ├── session.py     # 会话管理
│       │   ├── plugin_manager.py  # 插件管理器
│       │   ├── tool_registry.py   # 工具注册中心
│       │   ├── config.py      # 配置管理
│       │   ├── message.py     # 消息类
│       │   ├── plugin.py      # 插件基类
│       │   └── exceptions.py  # 异常定义
│       ├── tools/             # 工具集合
│       │   ├── __init__.py
│       │   ├── base.py        # 工具基类
│       │   ├── debugger.py    # 调试器工具
│       │   ├── analyzer.py    # 崩溃分析工具
│       │   ├── poc_sender.py  # POC发送工具
│       │   ├── memory_inspector.py  # 内存检查工具
│       │   ├── stack_trace.py       # 栈回溯工具
│       │   └── disassembler.py      # 反汇编工具
│       ├── plugins/           # 插件集合
│       │   ├── __init__.py
│       │   ├── debuggers/
│       │   │   └── gdb_plugin.py    # GDB插件
│       │   └── analyzers/
│       │       └── crash_analyzer_plugin.py  # 崩溃分析插件
│       └── utils/             # 工具函数
│           ├── __init__.py
│           ├── logger.py      # 日志工具
│           └── helpers.py     # 辅助函数
├── examples/                  # 示例代码
│   ├── basic_debug.py        # 基本调试示例
│   └── crash_analysis.py     # 崩溃分析示例
├── tests/                    # 测试目录
├── docs/                     # 文档目录
├── scripts/                  # 脚本目录
└── .gitignore               # Git忽略文件
```

## 核心组件说明

### 1. Agent (src/autogdb_agent/core/agent.py)
- 智能代理核心，协调所有组件
- 管理会话生命周期
- 处理用户请求和响应

### 2. Session (src/autogdb_agent/core/session.py)
- 单个调试会话的管理
- 维护会话上下文和历史
- 处理会话消息

### 3. Plugin Manager (src/autogdb_agent/core/plugin_manager.py)
- 插件加载和生命周期管理
- 插件依赖解析
- 插件实例管理

### 4. Tool Registry (src/autogdb_agent/core/tool_registry.py)
- 工具注册和管理
- 工具参数验证
- 工具执行协调

### 5. Config (src/autogdb_agent/core/config.py)
- 多环境配置管理
- 配置文件解析
- 环境变量展开

### 工具系统

#### Debugger Tool
- GDB调试器接口
- pexpect进程管理
- 命令执行和输出解析

#### Crash Analyzer
- 智能崩溃分析
- 模式识别
- 可利用性评估

#### POC Sender
- 网络数据包发送
- 多协议支持
- 重试机制

#### Memory Inspector
- 内存状态分析
- 模式检测
- 栈/堆分析

#### Stack Trace
- 栈回溯解析
- 函数名解码
- 控制流分析

#### Disassembler
- 代码反汇编
- 指令分析
- 危险指令检测

## 插件系统

### 插件类型
1. **Debugger Plugins**: GDB, LLDB, WinDbg等
2. **Analyzer Plugins**: 崩溃分析、漏洞检测
3. **Protocol Plugins**: UDP, TCP, HTTP, BACnet
4. **Tool Plugins**: 自定义工具集成
5. **UI Plugins**: 可视化和交互界面

### 插件开发
1. 继承Plugin基类
2. 实现必需方法（initialize, execute）
3. 添加插件元数据
4. 注册插件配置

## 使用方式

### 命令行接口
```bash
# 初始化
autogdb-agent init

# 启动调试会话
autogdb-agent debug -t /path/to/target

# 交互模式
autogdb-agent interactive

# 查看插件
autogdb-agent plugins

# 查看工具
autogdb-agent tools

# 查看状态
autogdb-agent status
```

### Python API
```python
from autogdb_agent import Agent

# 创建代理
agent = Agent()
await agent.start()

# 创建会话
session = await agent.create_session("debug_session")

# 执行命令
result = await agent.execute_command("debug_session", "info registers")
```

## 扩展点

### 1. 添加新工具
1. 继承Tool基类
2. 实现execute方法
3. 在tool_registry中注册

### 2. 添加新插件
1. 继承Plugin基类
2. 实现插件逻辑
3. 添加到插件目录

### 3. 添加新协议
1. 实现协议接口
2. 添加协议配置
3. 创建协议插件

### 4. 自定义分析器
1. 继承AnalyzerPlugin
2. 实现分析方法
3. 注册分析规则

## 架构特点

1. **模块化设计**: 每个组件职责明确，易于维护
2. **插件化架构**: 支持动态加载和扩展
3. **异步支持**: 基于asyncio实现高性能
4. **配置驱动**: 通过YAML配置灵活定制
5. **丰富的工具**: 内置多种调试和分析工具
6. **易于扩展**: 提供清晰的扩展API

这个架构设计参考了Claude Code的设计理念，提供了强大的调试能力和良好的扩展性。