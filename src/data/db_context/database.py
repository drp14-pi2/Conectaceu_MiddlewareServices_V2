"""Database connection and session configuration"""
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool
from typing import AsyncGenerator

from src.infrastructure.configuration.settings import settings

# Create engine with MySQL configuration
engine = create_async_engine(
    # Enforce async on URL
    url=settings.DATABASE_URL.replace("mysql+pymysql", "mysql+aiomysql"),
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    echo=settings.DATABASE_ECHO,
    connect_args={
        "connect_timeout": 10,
        "charset": "utf8mb4",
        "use_unicode": True,
    }
)

# MySQL-specific session settings
@event.listens_for(engine.sync_engine, "connect")
def set_mysql_session_vars(dbapi_connection, connection_record):
    """Set MySQL session variables on connection"""
    cursor = dbapi_connection.cursor()
    cursor.execute("SET time_zone = '-03:00'")
    cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
    cursor.execute("SET NAMES utf8mb4")
    cursor.execute("SET CHARACTER SET utf8mb4")
    cursor.execute("SET character_set_connection=utf8mb4")
    cursor.execute("SET collation_connection = utf8mb4_0900_as_cs")
    cursor.close()

# Session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

def get_db_session() -> AsyncSession:
    """For non-FastAPI contexts (console scripts). Caller manages lifecycle."""
    return AsyncSessionLocal()
