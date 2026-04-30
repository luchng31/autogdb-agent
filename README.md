# AutoGDB Agent - 智能调试助手

一个基于大语言模型的智能GDB调试助手，专为自动化漏洞分析和程序调试而设计。灵感源自Claude Code，提供插件化架构和丰富的扩展能力。

## 🌟 特性

- **智能调试分析**: 基于LLM的自动崩溃分析和调试建议
- **插件化架构**: 支持自定义调试器插件和分析器
- **多协议支持**: 支持多种网络协议的POC发送
- **可视化调试**: 提供调试过程可视化和交互界面
- **扩展能力**: 支持自定义工具和脚本集成
- **日志系统**: 完整的调试过程记录和导出

## 🏗️ 架构设计

### 核心组件

1. **Agent Core**: 智能代理核心，协调各组件工作
2. **Plugin System**: 插件系统，支持自定义调试器和分析器
3. **Tool Registry**: 工具注册中心，管理调试工具
4. **Session Manager**: 会话管理器，管理调试会话
5. **Communication Hub**: 通信中心，处理数据交换
6. **Configuration Manager**: 配置管理器，支持多环境配置

### 插件类型

- **Debugger Plugins**: GDB, LLDB, WinDbg等调试器支持
- **Analyzer Plugins**: 崩溃分析、模式识别、漏洞检测
- **Protocol Plugins**: UDP, TCP, HTTP, BACnet等协议支持
- **Tool Plugins**: 自定义工具和脚本集成
- **UI Plugins**: 可视化和交互界面扩展

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
autogdb-agent debug -v 1.3.2 -p ./pocs/

# 交互式调试模式
autogdb-agent interactive

# 查看可用插件
autogdb-agent plugins list

# 运行示例
autogdb-agent run examples/basic_crash.py
```

## 🔧 配置

配置文件位于 `~/.autogdb-agent/config.yaml`:

```yaml
agent:
  model: "claude-3-opus"
  max_rounds: 100
  timeout: 3600

debuggers:
  gdb:
    path: "/usr/bin/gdb"
    prompt_pattern: "\\(gdb\\)"
    init_commands:
      - "set pagination off"
      - "set confirm off"

analyzers:
  crash_analyzer:
    enabled: true
    pattern_types:
      - "null_deref"
      - "buffer_overflow"
      - "use_after_free"

protocols:
  bacnet:
    default_port: 47808
    protocol: "udp"
    retries: 3

tools:
  - name: "stack_trace"
    type: "builtin"
    command: "bt full"
  - name: "memory_dump"
    type: "custom"
    script: "scripts/memory_dump.py"
```

## 📚 插件开发

### 创建调试器插件

```python
# plugins/debuggers/my_debugger.py
from autogdb_agent.core.plugin import DebuggerPlugin

class MyDebugger(DebuggerPlugin):
    name = "my_debugger"
    
    def __init__(self, config):
        super().__init__(config)
        self.prompt_pattern = r">>>"
    
    def start(self):
        """启动调试器"""
        pass
    
    def execute(self, command):
        """执行命令"""
        pass
    
    def stop(self):
        """停止调试器"""
        pass
```

### 创建分析器插件

```python
# plugins/analyzers/crash_analyzer.py
from autogdb_agent.core.plugin import AnalyzerPlugin

class CrashAnalyzer(AnalyzerPlugin):
    name = "crash_analyzer"
    
    def analyze(self, crash_data):
        """分析崩溃数据"""
        analysis = {
            'type': self.detect_crash_type(crash_data),
            'location': self.extract_crash_location(crash_data),
            'suggestions': self.generate_suggestions(crash_data)
        }
        return analysis
```

## 🎯 高级功能

### 工作流管理

```python
# workflows/fuzzing_workflow.yaml
name: "fuzzing_workflow"
description: "自动模糊测试工作流"
steps:
  - name: "setup"
    plugin: "environment_setup"
    parameters:
      binary_path: "/target/bin"
  - name: "fuzz"
    plugin: "fuzzer"
    parameters:
      input_corpus: "./corpus/"
      iterations: 10000
  - name: "analyze"
    plugin: "crash_analyzer"
    parameters:
      auto_triage: true
```

### 自定义工具集成

```python
# tools/custom_analyzer.py
from autogdb_agent.core.tool import CustomTool

class CustomAnalyzer(CustomTool):
    def __init__(self):
        super().__init__("custom_analyzer", "自定义分析工具")
    
    def execute(self, context):
        # 实现自定义分析逻辑
        return {"result": "analysis_result"}
```

## 📊 监控和分析

- **调试会话统计**: 调试时长、成功率、分析深度
- **性能监控**: 响应时间、资源使用情况
- **质量分析**: 崩溃类型分布、漏洞类型统计

## 🤝 贡献

欢迎贡献代码！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 📄 许可证

MIT License - 查看 [LICENSE](LICENSE) 文件了解详情。