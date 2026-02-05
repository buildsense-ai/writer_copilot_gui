"""Base repository class."""
from typing import Optional, List, Dict, Any
from src.infrastructure.database.connection import get_db_connection


class BaseRepository:
    """Base repository with common database operations."""
    
    def __init__(self):
        pass
    
    def get_connection(self):
        """Get a database connection."""
        return get_db_connection()
    
    def execute(self, query: str, params: tuple = ()) -> Any:
        """Execute a query and return results."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        result = cursor.lastrowid
        cursor.close()
        conn.close()
        return result
    
    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict]:
        """Fetch one row."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict]:
        """Fetch all rows."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return [dict(row) for row in rows]
