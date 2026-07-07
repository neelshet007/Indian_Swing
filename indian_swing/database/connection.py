from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from indian_swing.config.settings import settings
from indian_swing.core.logging_setup import get_logger

logger = get_logger(__name__)

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def _get_sync_url(database_url: str) -> str:
    return database_url.replace("sqlite+aiosqlite", "sqlite").replace("postgresql+asyncpg", "postgresql")


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        sync_url = _get_sync_url(settings.database.url)
        connect_args = {"check_same_thread": False} if sync_url.startswith("sqlite") else {}
        _engine = create_engine(
            sync_url,
            connect_args=connect_args,
            pool_pre_ping=True,
            echo=settings.database.echo,
            future=True,
        )

        if sync_url.startswith("sqlite"):
            @event.listens_for(_engine, "connect")
            def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(),
            expire_on_commit=False,
            autoflush=False,
            future=True,
        )
    return _SessionLocal


@contextmanager
def get_sync_session() -> Generator[Session, None, None]:
    session = get_session_factory()()
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
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def init_db() -> None:
    from indian_swing.database.models import Base

    engine = get_engine()
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, lambda: Base.metadata.create_all(bind=engine))
    logger.info("database.initialized", url=settings.database.url, environment=settings.app_env)


async def dispose_engine() -> None:
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
