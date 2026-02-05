"""Session state management."""
import uuid
from typing import Dict, Any, Optional
from datetime import datetime


class SessionManager:
    """管理会话状态"""

    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self) -> str:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "created_at": datetime.now(),
            "turn": 0,
            "history": []
        }
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话"""
        return self.sessions.get(session_id)

    def increment_turn(self, session_id: str):
        """增加对话轮次"""
        if session_id in self.sessions:
            self.sessions[session_id]["turn"] += 1

    def add_message(self, session_id: str, role: str, content: str):
        """添加消息到历史"""
        if session_id in self.sessions:
            self.sessions[session_id]["history"].append({
                "role": role,
                "content": content
            })


# Global session manager
_session_manager = None


def get_session_manager() -> SessionManager:
    """获取全局会话管理器"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
