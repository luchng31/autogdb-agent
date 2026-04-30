# 调试器插件

支持多种调试器的通用插件系统：

## 已支持的调试器

- **GDB**: GNU Debugger
  - 文件: `gdb_plugin.py`
  - 支持的目标: ELF, PE, MachO
  - 特性: 完整的GDB命令支持

- **LLDB**: LLVM Debugger
  - 文件: `lldb_plugin.py`
  - 支持的目标: ELF, PE, MachO
  - 特性: 现代化的调试器接口

## 开发新的调试器插件

```python
from autogdb_agent.core.plugin import Plugin
from autogdb_agent.tools.debugger import DebuggerTool

class MyDebugger(Plugin):
    name = "my_debugger"
    type = "debugger"
    description = "我的调试器"
    version = "1.0.0"

    async def initialize(self):
        # 初始化调试器
        pass

    async def execute(self, **kwargs):
        # 执行调试操作
        debugger = DebuggerTool(self.config)
        await debugger.initialize()
        return await debugger.execute(**kwargs)

    async def cleanup(self):
        # 清理资源
        pass
```

## 配置示例

```yaml
debuggers:
  my_debugger:
    enabled: true
    path: "/path/to/debugger"
    prompt_pattern: r">>>"
    init_commands:
      - "set some-option value"
    timeout: 30
    supported_targets: ["elf", "pe"]
```