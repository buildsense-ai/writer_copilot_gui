"""Task repository for Todo Skill."""
import json
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime

from src.repositories.base import BaseRepository
from src.infrastructure.database.models import Task


class TaskRepository(BaseRepository):
    """Repository for task operations."""
    
    def create(
        self,
        title: str,
        description: Optional[str] = None,
        status: str = "inbox",
        priority: Optional[str] = None,
        energy_level: Optional[str] = None,
        estimated_duration: Optional[int] = None,
        embedding: Optional[List[float]] = None
    ) -> Task:
        """Create a new task."""
        task_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        self.execute("""
            INSERT INTO tasks 
            (id, title, description, status, priority, energy_level, 
             estimated_duration, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task_id, title, description, status, priority,
            energy_level, estimated_duration, created_at, created_at
        ))
        
        return Task(
            id=task_id,
            title=title,
            description=description,
            status=status,
            priority=priority,
            energy_level=energy_level,
            estimated_duration=estimated_duration,
            created_at=datetime.fromisoformat(created_at)
        )
    
    def get_by_id(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        row = self.fetch_one("""
            SELECT * FROM tasks WHERE id = ? AND deleted_at IS NULL
        """, (task_id,))
        
        if row:
            return Task(
                id=row["id"],
                title=row["title"],
                description=row["description"],
                status=row["status"],
                priority=row["priority"],
                energy_level=row["energy_level"],
                estimated_duration=row["estimated_duration"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else None,
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
                updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
            )
        return None
    
    def update(self, task_id: str, **kwargs) -> Optional[Task]:
        """Update task fields."""
        if not kwargs:
            return self.get_by_id(task_id)
        
        # Build SET clause
        set_parts = []
        params = []
        
        for key, value in kwargs.items():
            if key in ["title", "description", "status", "priority", 
                      "energy_level", "estimated_duration", "metadata"]:
                set_parts.append(f"{key} = ?")
                if key == "metadata" and isinstance(value, dict):
                    params.append(json.dumps(value))
                else:
                    params.append(value)
        
        if not set_parts:
            return self.get_by_id(task_id)
        
        # Always update updated_at
        set_parts.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        
        # Add task_id to params
        params.append(task_id)
        
        query = f"UPDATE tasks SET {', '.join(set_parts)} WHERE id = ?"
        self.execute(query, tuple(params))
        
        return self.get_by_id(task_id)
    
    def soft_delete(self, task_id: str):
        """Soft delete a task."""
        self.execute("""
            UPDATE tasks SET deleted_at = ? WHERE id = ?
        """, (datetime.now().isoformat(), task_id))
    
    def list_all(
        self,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Task]:
        """List all tasks."""
        query = "SELECT * FROM tasks WHERE deleted_at IS NULL"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        rows = self.fetch_all(query, tuple(params))
        
        tasks = []
        for row in rows:
            tasks.append(Task(
                id=row["id"],
                title=row["title"],
                description=row["description"],
                status=row["status"],
                priority=row["priority"],
                energy_level=row["energy_level"],
                estimated_duration=row["estimated_duration"],
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
                updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
            ))
        
        return tasks
    
    def add_tag(self, task_id: str, tag_id: str):
        """Add a tag to a task."""
        try:
            self.execute("""
                INSERT INTO task_tags (task_id, tag_id)
                VALUES (?, ?)
            """, (task_id, tag_id))
        except:
            pass  # Ignore if already exists
    
    def remove_all_tags(self, task_id: str):
        """Remove all tags from a task."""
        self.execute("""
            DELETE FROM task_tags WHERE task_id = ?
        """, (task_id,))
    
    def get_task_tags(self, task_id: str) -> List[str]:
        """Get all tags for a task."""
        rows = self.fetch_all("""
            SELECT t.name FROM tags t
            JOIN task_tags tt ON t.id = tt.tag_id
            WHERE tt.task_id = ?
        """, (task_id,))
        
        return [row["name"] for row in rows]
