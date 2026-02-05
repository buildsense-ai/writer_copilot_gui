"""Infrastructure setup: local SQLite and ChromaDB."""
import os
import hashlib
import sqlite3
from pathlib import Path
import chromadb
from chromadb.config import Settings as ChromaSettings
from rich.console import Console

console = Console()

ENV_BASE_DIR = "PAPERMEM_BASE_DIR"


def get_project_id(cwd: str) -> str:
    """Calculate project_id as SHA256 of the current working directory."""
    return hashlib.sha256(cwd.encode()).hexdigest()


def get_base_dir() -> Path:
    base = Path(os.getenv(ENV_BASE_DIR, Path.home() / "PaperMem"))
    return base.expanduser() / "cli"


def get_sqlite_path() -> str:
    path = get_base_dir() / "papermem_cli.sqlite"
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


def get_chroma_path() -> str:
    path = get_base_dir() / "chromadb"
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def get_db_connection() -> sqlite3.Connection:
    return sqlite3.connect(get_sqlite_path())


def init_sqlite() -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            text TEXT NOT NULL,
            metadata TEXT,
            created_at TEXT NOT NULL
        );
        """
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS memories_project_id_idx ON memories (project_id);"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS memories_created_at_idx ON memories (created_at);"
    )
    conn.commit()
    cursor.close()
    conn.close()


def get_chroma_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(
        path=get_chroma_path(),
        settings=ChromaSettings(anonymized_telemetry=False)
    )


def setup_infrastructure() -> str:
    """
    Setup local storage (SQLite + ChromaDB) and return project_id.
    """
    cwd = os.getcwd()
    project_id = get_project_id(cwd)

    console.print(f"[cyan]Project Directory:[/cyan] {cwd}")
    console.print(f"[cyan]Project ID:[/cyan] {project_id[:16]}...")

    init_sqlite()
    get_chroma_path()

    console.print("[green]Local storage ready (SQLite + ChromaDB).[/green]")
    return project_id
