from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ProjectCreate(BaseModel):
    name: str
    type: Optional[str] = None
    description: Optional[str] = None


class ProjectRead(BaseModel):
    id: str
    name: str
    type: Optional[str] = None
    description: Optional[str] = None
    message_count: int = 0
    file_count: int = 0
    last_message_preview: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_active_at: datetime
    status: str = "active"

    model_config = ConfigDict(from_attributes=True)


class FileResponse(BaseModel):
    id: str
    project_id: str
    file_name: str
    file_path: Optional[str] = None
    file_url: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    mineru_task_id: Optional[str] = None
    parse_status: str = "pending"
    markdown_path: Optional[str] = None
    chunks_count: int = 0
    created_at: datetime
    parsed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ChatSessionCreate(BaseModel):
    project_id: str
    title: Optional[str] = None


class ChatSessionRead(BaseModel):
    id: str
    project_id: str
    title: Optional[str] = None
    message_count: int
    is_current: bool = True
    created_at: datetime
    last_message_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatMessageRead(BaseModel):
    id: str
    session_id: str
    project_id: str
    role: str
    content: str
    reasoning_trace: Optional[str] = None
    search_results: Optional[str] = None
    has_thinking: bool
    message_index: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
