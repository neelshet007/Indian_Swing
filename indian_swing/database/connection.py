"""
SQLAlchemy sync engine wrapped for async usage via run_in_executor.
Python 3.14 compatible — no greenlet required.
Uses PostgreSQL via psycopg2 and asyncpg.
"""
from __future__ import annotations

import asyncio
from contextlib import contextmanager, asynccontextmanager
from typing import Generator, AsyncGenerator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from indian_swing.config.settings import settings
from indian_swing.core.logging_setup import get_logger

logger = get_logger(__name__)

_engine = None
_SessionLocal = None


def _get_sync_url(async_url: str) -> str:
    """Convert aiosqlite URL to sync sqlite URL."""
    return async_url.replace("sqlite+aiosqlite", "sqlite").replace("postgresql+asyncpg", "postgresql")


def get_engine():
    global _engine
    if _engine is None:
        sync_url = _get_sync_url(settings.database.url)
        connect_args = {}

        _engine = create_engine(
            sync_url,
            connect_args=connect_args,
            echo=settings.database.echo,
        )

    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), expire_on_commit=False, autoflush=False)
    return _SessionLocal


@contextmanager
def get_sync_session() -> Generator[Session, None, None]:
    """Sync context manager for use inside run_in_executor."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@asynccontextmanager
async def get_session() -> AsyncGenerator[Session, None]:
    """
    Async-compatible session context manager.
    Runs the session synchronously but in the default executor thread pool.
    Yields a regular Session (not AsyncSession).
    """
    loop = asyncio.get_event_loop()
    # For simple use: just use sync session in async context
    # Heavy operations should use run_in_executor explicitly
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def init_db() -> None:
    """Create all tables. Idempotent."""
    from indian_swing.database.models import Base  # noqa: F401

    loop = asyncio.get_event_loop()
    engine = get_engine()

    def _create():
        Base.metadata.create_all(bind=engine)

    await loop.run_in_executor(None, _create)
    logger.info("database.initialized", url=settings.database.url)


async def dispose_engine() -> None:
    global _engine
    if _engine:
        _engine.dispose()
        _engine = None
