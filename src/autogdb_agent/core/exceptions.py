"""
Exceptions - 自定义异常类
"""


class AutoGDBError(Exception):
    """AutoGDB Agent 基础异常"""
    pass


class PluginError(AutoGDBError):
    """插件相关异常"""
    pass


class ToolError(AutoGDBError):
    """工具相关异常"""
    pass


class SessionError(AutoGDBError):
    """会话相关异常"""
    pass


class ConfigError(AutoGDBError):
    """配置相关异常"""
    pass


class CommunicationError(AutoGDBError):
    """通信相关异常"""
    pass


class ValidationError(AutoGDBError):
    """验证相关异常"""
    pass


class TimeoutError(AutoGDBError):
    """超时异常"""
    pass


class AuthenticationError(AutoGDBError):
    """认证异常"""
    pass