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
    from indian_swing.core.universe import UniverseManager
    from indian_swing.data.pipeline import DataPipeline
    from datetime import date, timedelta

    scheduler = AsyncIOScheduler()

    async def _run_scan():
        try:
            logger.info("scheduler.run_scan.start_data_sync")
            manager = UniverseManager()
            await manager.sync_to_db()
            syms = await manager.get_active_symbols()

            pipeline = DataPipeline()
            end_date = date.today()
            start_date = end_date - timedelta(days=settings.pipeline.lookback_years * 365)
            await pipeline.run_full(syms, start=start_date, end=end_date, force_refresh=False)
            logger.info("scheduler.run_scan.data_sync_complete")
        except Exception as e:
            logger.error("scheduler.run_scan.data_sync_error", error=str(e))

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
    stocks,
    strategies,
)

app.include_router(stocks.router, prefix="/api/stocks", tags=["Stocks"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["Recommendations"])
app.include_router(backtest.router, prefix="/api/backtest", tags=["Backtesting"])
app.include_router(replay.router, prefix="/api/replay", tags=["Replay"])
app.include_router(scanner.router, prefix="/api/scanner", tags=["Scanner"])
app.include_router(strategies.router, prefix="/api/strategies", tags=["Strategies"])


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0", "env": settings.app_env}
