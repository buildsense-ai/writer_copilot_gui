"""Database connection management for SQLite."""
import sqlite3
from pathlib import Path
from src.infra import get_base_dir


def get_sqlite_path() -> str:
    """Get the path to the SQLite database file."""
    path = get_base_dir() / "agent.sqlite"
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


def get_db_connection() -> sqlite3.Connection:
    """
    Get a connection to the SQLite database.
    
    Returns:
        sqlite3.Connection: Database connection
    """
    conn = sqlite3.connect(get_sqlite_path())
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn


def init_database():
    """Initialize database tables if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create skills table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            prompt_template TEXT NOT NULL,
            tool_set TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    
    # Create mem_source table (conversation history)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mem_source (
            source_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            turn INTEGER NOT NULL,
            speaker TEXT NOT NULL,
            content TEXT NOT NULL,
            tool_calls TEXT,
            tool_results TEXT,
            created_at TEXT NOT NULL
        )
    """)
    
    # Create index for efficient session queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_mem_source_session 
        ON mem_source(session_id, turn)
    """)
    
    # Create tasks table (Todo Skill)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT,
            priority TEXT,
            energy_level TEXT,
            estimated_duration INTEGER,
            metadata TEXT,
            created_at TEXT,
            updated_at TEXT,
            deleted_at TEXT
        )
    """)
    
    # Create tags table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id TEXT PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            created_at TEXT
        )
    """)
    
    # Create task_tags junction table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_tags (
            task_id TEXT NOT NULL,
            tag_id TEXT NOT NULL,
            PRIMARY KEY (task_id, tag_id),
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
