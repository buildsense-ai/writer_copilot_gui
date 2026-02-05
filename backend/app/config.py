import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application Settings
    app_name: str = "PaperMem"
    app_version: str = "1.0.0"
    environment: str = "development"
    log_level: str = "INFO"

    # API Settings
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    cors_allow_origins: str = "*"

    # OpenRouter API
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # AI Models
    llm_model: str = "deepseek/deepseek-r1"
    embedding_model: str = "qwen/qwen3-embedding-4b"

    # MinerU API
    mineru_api_token: str = ""
    mineru_api_url: str = "https://mineru.net/api/v4/extract/task"

    _default_base = Path.home() / "PaperMem"

    # Local Database Paths
    sqlite_db_path: str = str(_default_base / "papermem.db")
    chroma_persist_dir: str = str(_default_base / "chromadb")

    # File Storage Paths
    raw_files_dir: str = str(_default_base / "Raw")
    parsed_files_dir: str = str(_default_base / "Parsed")
    projects_dir: str = str(_default_base / "Projects")

    class Config:
        env_file = (".env", "../.env")
        env_prefix = ""

    def get_sqlite_path(self) -> str:
        """获取并展开 SQLite 数据库路径"""
        path = Path(self.sqlite_db_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        return str(path)

    def get_chroma_path(self) -> str:
        """获取并展开 ChromaDB 持久化路径"""
        path = Path(self.chroma_persist_dir).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    def get_raw_files_path(self) -> str:
        """获取并展开原始文件存储路径"""
        path = Path(self.raw_files_dir).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    def get_parsed_files_path(self) -> str:
        """获取并展开解析文件存储路径"""
        path = Path(self.parsed_files_dir).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    def get_projects_path(self) -> str:
        """获取并展开项目文件夹路径"""
        path = Path(self.projects_dir).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        return str(path)


settings = Settings()
