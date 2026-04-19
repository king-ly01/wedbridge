"""数据库连接配置"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://wedbridge:wedbridge@db:5432/wedbridge")

engine = create_engine(
    DATABASE_URL,
    pool_size=50,           # 增加基础连接数
    max_overflow=100,       # 增加溢出连接数
    pool_timeout=60,        # 增加超时时间
    pool_recycle=1800,
    pool_pre_ping=True      # 连接前检测，避免使用失效连接
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
