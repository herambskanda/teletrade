"""Database connection and session management."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine

from config.settings import get_settings
from src.database.models import Base

settings = get_settings()

# Convert the database URL for async support
async_database_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
sync_database_url = settings.database_url

# Create async engine
async_engine = create_async_engine(
    async_database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Create sync engine for migrations and admin tasks
sync_engine = create_engine(
    sync_database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Create session factories
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

SessionLocal = sessionmaker(
    sync_engine,
    autocommit=False,
    autoflush=False
)


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_db_session() -> Session:
    """Get a synchronous database session."""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


async def init_database():
    """Initialize the database schema."""
    async with async_engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)


def init_database_sync():
    """Initialize the database schema synchronously."""
    Base.metadata.create_all(bind=sync_engine)