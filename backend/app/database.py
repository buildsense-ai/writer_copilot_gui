from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

# 获取 SQLite 数据库路径
sqlite_path = settings.get_sqlite_path()

# 创建 SQLite 数据库连接
# check_same_thread=False 允许多线程访问
sqlite_dsn = f"sqlite:///{sqlite_path}"

engine = create_engine(
    sqlite_dsn,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """初始化数据库表"""
    Base.metadata.create_all(bind=engine)
