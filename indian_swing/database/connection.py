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
    from indian_swing.database.models import Base, PaperTrade, Recommendation
    from indian_swing.database.connection import get_sync_session
    from indian_swing.core.universe_badge import badge_lookup
    from sqlalchemy import select

    from sqlalchemy import select, text

    engine = get_engine()
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, lambda: Base.metadata.create_all(bind=engine))
    
    def _migrate_and_backfill():
        # Schema migration: Add new columns if they do not exist
        with engine.connect() as conn:
            for col_name, col_type in [
                ("original_target_price", "FLOAT"),
                ("stop_loss", "FLOAT"),
                ("execution_universe", "VARCHAR(30)")
            ]:
                try:
                    # In SQLite or Postgres, we can try altering the table in separate transactions
                    with conn.begin():
                        conn.execute(text(f"ALTER TABLE sw_paper_trades ADD COLUMN {col_name} {col_type}"))
                except Exception:
                    pass
        
        # Backfill existing paper trades
        with get_sync_session() as session:
            trades = session.execute(select(PaperTrade)).scalars().all()
            updated_count = 0
            for t in trades:
                updated = False
                rec = t.recommendation
                if rec:
                    if t.original_target_price is None:
                        t.original_target_price = rec.target_price
                        updated = True
                    if t.stop_loss is None:
                        t.stop_loss = rec.stop_loss
                        updated = True
                
                if t.execution_universe is None:
                    is_nifty500 = badge_lookup.has_badge(t.symbol, "NIFTY 500")
                    t.execution_universe = "NIFTY500" if is_nifty500 else "NON_NIFTY500"
                    updated = True
                
                if updated:
                    updated_count += 1
            
            if updated_count > 0:
                session.commit()
                logger.info("database.backfilled_paper_trades", count=updated_count)

    await loop.run_in_executor(None, _migrate_and_backfill)
    logger.info("database.initialized", url=settings.database.url, environment=settings.app_env)


async def dispose_engine() -> None:
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
