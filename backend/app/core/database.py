from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models import Base


def get_engine():
    """获取数据库引擎"""
    if not settings.DATABASE_URL:
        raise ValueError("DATABASE_URL not configured")
    
    return create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
    )


def get_session_local():
    """获取数据库会话工厂"""
    engine = get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """初始化数据库，创建所有表"""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def get_db():
    """数据库依赖注入"""
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
