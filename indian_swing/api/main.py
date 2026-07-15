"""
FastAPI application entry point.
Mounts all routers, configures CORS, lifespan events, and background scheduler.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from indian_swing.config.settings import settings
from indian_swing.core.logging_setup import configure_logging, get_logger
from indian_swing.database.connection import dispose_engine, init_db

configure_logging(level=settings.log_level, fmt=settings.log_format)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app.startup", env=settings.app_env)
    await init_db()

    # Auto-discover strategies
    from indian_swing.strategies.registry import strategy_registry
    strategy_registry.discover()
    logger.info("strategies.loaded", count=len(strategy_registry))

    # Start APScheduler for nightly scans
    if settings.scanner.enabled:
        _start_scheduler()

    yield

    logger.info("app.shutdown")
    await dispose_engine()


def _start_scheduler() -> None:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from indian_swing.recommendations.scanner import RecommendationScanner

    scheduler = AsyncIOScheduler()

    async def _run_scan():
        scanner = RecommendationScanner()
        await scanner.scan()

    cron_parts = settings.scanner.cron.split()
    scheduler.add_job(
        _run_scan,
        CronTrigger(
            minute=cron_parts[0],
            hour=cron_parts[1],
            day_of_week=cron_parts[4] if len(cron_parts) > 4 else "*",
        ),
        id="nightly_scan",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("scheduler.started", cron=settings.scanner.cron)


app = FastAPI(
    title="Indian Swing Trading Platform",
    description="Institutional-grade swing trading recommendation system for Indian equities.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
from indian_swing.api.routes import (  # noqa: E402
    backtest,
    recommendations,
    replay,
    scanner,
    scans,
    stocks,
    strategies,
)

app.include_router(stocks.router, prefix="/api/stocks", tags=["Stocks"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["Recommendations"])
app.include_router(scans.router, prefix="/api/scans", tags=["Scans"])
app.include_router(backtest.router, prefix="/api/backtest", tags=["Backtesting"])
app.include_router(replay.router, prefix="/api/replay", tags=["Replay"])
app.include_router(scanner.router, prefix="/api/scanner", tags=["Scanner"])
app.include_router(strategies.router, prefix="/api/strategies", tags=["Strategies"])


@app.get("/api/health")
async def health():
    from indian_swing.database.connection import get_engine
    from sqlalchemy import text
    try:
        engine = get_engine()
        # Test connection directly
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected", "version": "1.0.0", "env": settings.app_env}
    except Exception as e:
        # Cleanly return the error message without crashing
        return {"status": "error", "db": "disconnected", "error": str(e), "version": "1.0.0"}
