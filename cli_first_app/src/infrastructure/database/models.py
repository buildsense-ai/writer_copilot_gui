"""Data models for SQLite database."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class Skill:
    """Skill model."""
    id: str
    name: str
    prompt_template: str
    tool_set: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class MemSource:
    """Conversation history model."""
    source_id: Optional[int] = None
    session_id: Optional[str] = None
    turn: Optional[int] = None
    speaker: Optional[str] = None
    content: Optional[str] = None
    tool_calls: Optional[List[dict]] = None
    tool_results: Optional[List[dict]] = None
    created_at: Optional[datetime] = None


@dataclass
class Task:
    """Task model for Todo Skill."""
    id: str
    title: str
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    energy_level: Optional[str] = None
    estimated_duration: Optional[int] = None
    metadata: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


@dataclass
class Tag:
    """Tag model."""
    id: str
    name: str
    created_at: Optional[datetime] = None
