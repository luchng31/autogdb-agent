"""
Configuration - 配置管理
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .exceptions import AutoGDBError
from ..utils.logger import get_logger


class Config:
    """
    配置管理器
    支持多环境配置和配置热更新
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.logger = get_logger(__name__)

        # 配置文件路径
        self.config_path = config_path or self._get_default_config_path()
        self.env = os.environ.get("AUTOAGENT_ENV", "development")

        # 配置数据
        self._config: Dict[str, Any] = {}
        self._env_config: Dict[str, Any] = {}

        # 加载配置
        self.load()

    def _get_default_config_path(self) -> Path:
        """获取默认配置文件路径"""
        # 优先级：当前目录 -> 用户目录 -> 安装目录
        possible_paths = [
            Path.cwd() / "autogdb-agent.yaml",
            Path.cwd() / "autogdb-agent.yml",
            Path.home() / ".autogdb-agent" / "config.yaml",
            Path.home() / ".autogdb-agent" / "config.yml",
            Path(__file__).parent.parent.parent / "config" / "default.yaml",
        ]

        for path in possible_paths:
            if path.exists():
                return path

        # 如果都不存在，使用默认路径
        return Path.home() / ".autogdb-agent" / "config.yaml"

    def load(self):
        """加载配置文件"""
        try:
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self._config = yaml.safe_load(f) or {}

                # 加载环境配置
                env_config_path = self.config_path.with_suffix(f".{self.env}.yaml")
                if env_config_path.exists():
                    with open(env_config_path, "r", encoding="utf-8") as f:
                        self._env_config = yaml.safe_load(f) or {}

                self.logger.info(f"加载配置文件: {self.config_path}")
            else:
                self._config = self._get_default_config()
                self.logger.info("使用默认配置")

        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            self._config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "agent": {
                "model": "claude-3-opus",
                "max_rounds": 100,
                "timeout": 3600,
                "temperature": 0.1,
                "debug_mode": False,
            },
            "debuggers": {
                "gdb": {
                    "path": "/usr/bin/gdb",
                    "prompt_pattern": r"\(gdb\)",
                    "init_commands": [
                        "set pagination off",
                        "set confirm off",
                        "set print pretty on",
                    ],
                    "timeout": 30,
                    "supported_targets": ["elf", "pe", "macho"],
                },
                "lldb": {
                    "path": "/usr/bin/lldb",
                    "prompt_pattern": r"lldb",
                    "init_commands": [
                        "settings set stop-disassembly-display source-and-assembly",
                        "settings set target.run-args",
                    ],
                    "timeout": 30,
                    "supported_targets": ["elf", "pe", "macho"],
                },
            },
            "protocols": {
                "bacnet": {
                    "enabled": True,
                    "default_port": 47808,
                    "protocol": "udp",
                    "retries": 3,
                    "timeout": 5,
                    "headers": {},
                },
                "tcp": {
                    "enabled": True,
                    "default_port": 80,
                    "protocol": "tcp",
                    "retries": 3,
                    "timeout": 10,
                },
                "udp": {
                    "enabled": True,
                    "default_port": 53,
                    "protocol": "udp",
                    "retries": 3,
                    "timeout": 5,
                },
                "http": {
                    "enabled": True,
                    "default_port": 80,
                    "method": "POST",
                    "timeout": 30,
                    "retry_policy": "exponential_backoff",
                },
            },
            "analyzers": {
                "crash_analyzer": {
                    "enabled": True,
                    "level": "detailed",
                    "patterns": {
                        "null_deref": {"enabled": True, "description": "空指针解引用"},
                        "buffer_overflow": {"enabled": True, "description": "缓冲区溢出"},
                        "use_after_free": {"enabled": True, "description": "释放后使用"},
                        "stack_overflow": {"enabled": True, "description": "栈溢出"},
                        "heap_corruption": {"enabled": True, "description": "堆损坏"},
                    },
                },
            },
            "debug": {
                "log_level": "INFO",
                "log_file": "~/.autogdb-agent/logs/agent.log",
                "max_log_size": "100MB",
                "backup_count": 5,
            },
            "plugins": {
                "paths": [
                    "~/.autogdb-agent/plugins",
                    "./plugins",
                ],
                "auto_load": True,
            },
            "tools": {
                "timeout": 300,
                "retry_count": 3,
                "cache_enabled": True,
                "cache_ttl": 3600,
            },
            "session": {
                "max_age": 86400,
                "cleanup_interval": 3600,
                "max_sessions": 100,
                "save_to_disk": True,
                "log_level": "INFO",
            },
            "api": {
                "host": "127.0.0.1",
                "port": 8000,
                "workers": 1,
                "reload": False,
                "cors_origins": ["*"],
            },
            "database": {
                "url": "sqlite:///~/.autogdb-agent/sessions.db",
                "echo": False,
                "pool_size": 10,
                "max_overflow": 20,
            },
            "logging": {
                "level": "INFO",
                "format": "text",
                "file": {
                    "enabled": True,
                    "path": "~/.autogdb-agent/logs/agent.log",
                    "max_size": "100MB",
                    "backup_count": 5,
                },
                "console": {
                    "enabled": True,
                    "format": "colored",
                },
            },
            "llm": {
                "provider": "anthropic",
                "api_key": os.environ.get("ANTHROPIC_API_KEY"),
                "base_url": os.environ.get("ANTHROPIC_BASE_URL"),
                "model": "claude-3-opus",
                "max_tokens": 4096,
                "timeout": 60,
                "temperature": 0.1,
                "system_prompt": """你是一个专业的调试分析专家。你的任务是通过分析GDB输出来定位程序崩溃的根因。
                1. 重点分析函数参数值，特别是空指针、无效地址等异常值
                2. 查找调用栈中的危险函数调用（如结构体成员访问前未检查指针）
                3. 确认具体的代码行和漏洞类型
                4. 当你确认找到根因时，输出以 ROOT_CAUSE_FOUND 开头的结论""",
            },
            "targets": {
                "supported": ["elf", "pe", "macho", "core", "runtime"],
            },
            "workflows": {
                "enabled": True,
                "default_workflow": "standard_debug",
                "workflows": {
                    "standard_debug": {
                        "name": "标准调试",
                        "description": "基本的调试流程",
                        "steps": [
                            {"action": "setup", "plugin": "environment_setup"},
                            {"action": "analyze", "plugin": "crash_analyzer"},
                            {"action": "debug", "plugin": "debugger"},
                        ],
                    },
                    "fuzzing": {
                        "name": "模糊测试",
                        "description": "自动化模糊测试流程",
                        "steps": [
                            {"action": "fuzz", "plugin": "fuzzer"},
                            {"action": "collect_crashes", "plugin": "crash_collector"},
                            {"action": "triage", "plugin": "crash_triage"},
                            {"action": "debug", "plugin": "debugger"},
                        ],
                    },
                    "regression": {
                        "name": "回归测试",
                        "description": "自动化回归测试流程",
                        "steps": [
                            {"action": "run_tests", "plugin": "test_runner"},
                            {"action": "collect_results", "plugin": "result_collector"},
                            {"action": "compare", "plugin": "diff_tool"},
                        ],
                    },
                },
            },
            "visualization": {
                "enabled": True,
                "format": "html",
                "include_charts": True,
                "include_stack_trace": True,
                "include_memory_graph": True,
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        支持嵌套路径，如 'agent.model'
        """
        # 首先从环境配置查找
        value = self._get_nested_value(self._env_config, key)
        if value is not None:
            return value

        # 然后从主配置查找
        value = self._get_nested_value(self._config, key)
        if value is not None:
            return value

        return default

    def _get_nested_value(self, config: Dict, key: str) -> Any:
        """获取嵌套配置值"""
        parts = key.split(".")
        value = config

        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None

        return value

    def set(self, key: str, value: Any, save: bool = False):
        """
        设置配置值
        """
        self._set_nested_value(self._config, key, value)

        if save:
            self.save()

    def _set_nested_value(self, config: Dict, key: str, value: Any):
        """设置嵌套配置值"""
        parts = key.split(".")
        current = config

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value

    def get_env_config(self, env: str = None) -> Dict[str, Any]:
        """获取环境特定配置"""
        if not env:
            env = self.env

        env_config_path = self.config_path.with_suffix(f".{env}.yaml")
        if env_config_path.exists():
            with open(env_config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}

        return {}

    def merge_config(self, other_config: Dict[str, Any]):
        """合并配置"""
        def merge_dict(base: Dict, update: Dict):
            for key, value in update.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    merge_dict(base[key], value)
                else:
                    base[key] = value

        merge_dict(self._config, other_config)

    def save(self):
        """保存配置到文件"""
        try:
            # 确保目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(self._config, f, default_flow_style=False, indent=2)

            self.logger.info(f"保存配置文件: {self.config_path}")

        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
            raise AutoGDBError(f"保存配置文件失败: {e}")

    def reload(self):
        """重新加载配置"""
        self.load()

    def expand_env_vars(self, value: Any) -> Any:
        """展开环境变量"""
        if isinstance(value, str):
            # 支持 ${VAR} 和 $VAR 格式
            def replace_var(match):
                var = match.group(1) or match.group(2)
                return os.environ.get(var, match.group(0))

            return re.sub(r'\$\{(\w+)\}|\$(\w+)', replace_var, value)
        elif isinstance(value, dict):
            return {k: self.expand_env_vars(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.expand_env_vars(v) for v in value]
        else:
            return value

    def validate_config(self) -> bool:
        """验证配置"""
        required_keys = [
            "agent.model",
            "agent.max_rounds",
            "agent.timeout",
        ]

        for key in required_keys:
            if self.get(key) is None:
                self.logger.error(f"缺少必需的配置项: {key}")
                return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "config": self._config,
            "env": self.env,
            "config_path": str(self.config_path),
        }

    @property
    def available_envs(self) -> List[str]:
        """可用的环境列表"""
        envs = ["development", "production", "testing"]

        # 检查配置文件目录中是否有环境配置文件
        config_dir = self.config_path.parent
        if config_dir.exists():
            for file in config_dir.glob("*.yaml"):
                env = file.stem
                if env not in envs and env != self.config_path.stem:
                    envs.append(env)

        return envs

    def __getitem__(self, key: str) -> Any:
        """支持字典式访问"""
        return self.get(key)

    def __setitem__(self, key: str, value: Any):
        """支持字典式设置"""
        self.set(key, value)