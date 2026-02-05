import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app.database import Base


def beijing_now() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=8)


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    type = Column(String(100), index=True)
    description = Column(Text)

    message_count = Column(Integer, default=0)
    file_count = Column(Integer, default=0)
    last_message_preview = Column(String(200))

    created_at = Column(DateTime, default=beijing_now, index=True)
    updated_at = Column(DateTime, default=beijing_now, onupdate=beijing_now)
    last_active_at = Column(DateTime, default=beijing_now, index=True)

    status = Column(String(20), default="active", index=True)


class File(Base):
    """上传的文件记录"""
    __tablename__ = "files"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)

    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500))  # 原始文件路径
    file_url = Column(String(500))  # 文件URL (MinIO/HTTP)
    file_type = Column(String(50))  # pdf, md, txt
    file_size = Column(Integer)  # 字节

    # MinerU 解析相关
    mineru_task_id = Column(String(100))
    parse_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    markdown_path = Column(String(500))  # 解析后的 Markdown 路径
    chunks_count = Column(Integer, default=0)  # 向量化的块数量

    created_at = Column(DateTime, default=beijing_now, index=True)
    parsed_at = Column(DateTime)


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)

    title = Column(String(255))
    message_count = Column(Integer, default=0)
    is_current = Column(Boolean, default=True, index=True)

    created_at = Column(DateTime, default=beijing_now, index=True)
    last_message_at = Column(DateTime, default=beijing_now, index=True)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("chat_sessions.id"), nullable=False, index=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)

    role = Column(String(50), nullable=False, index=True)
    content = Column(Text, nullable=False)
    reasoning_trace = Column(Text)
    search_results = Column(Text)
    has_thinking = Column(Boolean, default=False)
    message_index = Column(Integer, default=0)

    created_at = Column(DateTime, default=beijing_now, index=True)
