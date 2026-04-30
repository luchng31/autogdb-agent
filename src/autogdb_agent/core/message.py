"""
Message - 消息类
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class MessageRole(Enum):
    """消息角色枚举"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Message:
    """
    消息类
    用于表示对话中的消息
    """

    def __init__(
        self,
        role: MessageRole | str,
        content: str,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化消息

        Args:
            role: 消息角色
            content: 消息内容
            timestamp: 时间戳
            metadata: 元数据
        """
        self.role = MessageRole(role) if isinstance(role, str) else role
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """从字典创建消息"""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )

    def __str__(self) -> str:
        """字符串表示"""
        return f"[{self.timestamp}] {self.role.value}: {self.content}"

    def __repr__(self) -> str:
        """调试表示"""
        return f"Message(role={self.role.value}, content={self.content[:50]}..., timestamp={self.timestamp})"

    def __eq__(self, other) -> bool:
        """相等比较"""
        if not isinstance(other, Message):
            return False
        return (
            self.role == other.role
            and self.content == other.content
            and self.timestamp == other.timestamp
            and self.metadata == other.metadata
        )