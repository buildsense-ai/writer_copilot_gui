"""Tag repository for Todo Skill."""
import uuid
from typing import Optional
from datetime import datetime

from src.repositories.base import BaseRepository
from src.infrastructure.database.models import Tag


class TagRepository(BaseRepository):
    """Repository for tag operations."""
    
    def get_or_create(self, name: str) -> Tag:
        """Get existing tag or create new one."""
        # Try to get existing tag
        row = self.fetch_one("""
            SELECT * FROM tags WHERE name = ?
        """, (name,))
        
        if row:
            return Tag(
                id=row["id"],
                name=row["name"],
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
            )
        
        # Create new tag
        tag_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        self.execute("""
            INSERT INTO tags (id, name, created_at)
            VALUES (?, ?, ?)
        """, (tag_id, name, created_at))
        
        return Tag(
            id=tag_id,
            name=name,
            created_at=datetime.fromisoformat(created_at)
        )
    
    def get_by_name(self, name: str) -> Optional[Tag]:
        """Get tag by name."""
        row = self.fetch_one("""
            SELECT * FROM tags WHERE name = ?
        """, (name,))
        
        if row:
            return Tag(
                id=row["id"],
                name=row["name"],
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
            )
        return None
