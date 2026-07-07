from __future__ import annotations

import asyncio
from datetime import date

import numpy as np
import pandas as pd
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from indian_swing.config.settings import settings
from indian_swing.core.lookback_engine import DynamicLookbackEngine
from indian_swing.data.pipeline import DataPipeline
from indian_swing.database.connection import dispose_engine, get_sync_session, init_db
from indian_swing.database.models import Recommendation, ScanJob, Signal, Stock
from indian_swing.database.repositories.ohlcv_repo import OHLCVRepository
from indian_swing.database.repositories.stock_repo import StockRepository
from indian_swing.recommendations.scanner import RecommendationScanner
from indian_swing.strategies.institutional_vcp import InstitutionalVCP


@pytest.fixture()
def configured_db(tmp_path):
    original_url = settings.database.url
    original_env = settings.app_env
    settings.database.url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    settings.app_env = "test"
    asyncio.run(dispose_engine())
    asyncio.run(init_db())
    yield
    asyncio.run(dispose_engine())
    settings.database.url = original_url
    settings.app_env = original_env


def _build_daily_frame(end_date: str, periods: int, start_price: float, end_price: float, breakout_price: float) -> pd.DataFrame:
    index = pd.bdate_range(end=end_date, periods=periods)
    closes = np.linspace(start_price, end_price, periods)
    closes[-30:-20] = np.linspace(end_price * 0.97, end_price * 0.985, 10)
    closes[-20:-10] = np.linspace(end_price * 0.985, end_price * 0.992, 10)
    closes[-10:-1] = np.linspace(end_price * 0.992, end_price * 0.997, 9)
    closes[-1] = breakout_price

    highs = closes * np.concatenate([np.full(periods - 30, 1.02), np.linspace(1.018, 1.006, 30)])
    lows = closes * np.concatenate([np.full(periods - 30, 0.98), np.linspace(0.982, 0.995, 30)])
    opens = (highs + lows) / 2
    volumes = np.full(periods, 220_000)
    volumes[-20:-1] = 120_000
    volumes[-1] = 480_000

    frame = pd.DataFrame(
        {
            "open": opens,
            "high": np.maximum(highs, closes),
            "low": np.minimum(lows, closes),
            "close": closes,
            "volume": volumes,
        },
        index=index,
    )
    frame.index.name = "date"
    return frame


def _seed_stock_and_data(symbol: str = "TEST", benchmark_symbol: str = "^NSEI") -> tuple[Stock, date]:
    stock_frame = _build_daily_frame("2025-06-30", 320, 70, 176, 181)
    benchmark_frame = _build_daily_frame("2025-06-30", 320, 100, 126, 127)

    with get_sync_session() as session:
        stock_repo = StockRepository(session)
        stock = stock_repo.upsert(symbol=symbol, name="Test Industries", exchange="NSE", sector="Industrials", industry="Industrials")
        benchmark = stock_repo.upsert(
            symbol=benchmark_symbol,
            name="NIFTY 50",
            exchange=settings.scanner.benchmark_exchange,
            instrument_type="INDEX",
        )
        ohlcv_repo = OHLCVRepository(session)
        ohlcv_repo.bulk_insert_ignore(DataPipeline._df_to_records(stock_frame, stock.id, "1d"))
        ohlcv_repo.bulk_insert_ignore(DataPipeline._df_to_records(benchmark_frame, benchmark.id, "1d"))
        ohlcv_repo.replace_timeframe(stock.id, "1wk", DataPipeline._df_to_records(stock_frame.resample("W-FRI").agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna(), stock.id, "1wk"))
        ohlcv_repo.replace_timeframe(benchmark.id, "1wk", DataPipeline._df_to_records(benchmark_frame.resample("W-FRI").agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna(), benchmark.id, "1wk"))
        return stock, stock_frame.index[-1].date()


@pytest.mark.asyncio
async def test_dynamic_lookback_is_explicit_and_not_source_parsed(configured_db):
    strategy = InstitutionalVCP()
    assert DynamicLookbackEngine.get_required_lookback(strategy) >= 252


@pytest.mark.asyncio
async def test_strategy_generates_explainable_signal(configured_db):
    stock, scan_date = _seed_stock_and_data()
    scanner = RecommendationScanner()
    context = scanner._load_strategy_context(stock, DynamicLookbackEngine.get_required_lookback(scanner.strategy), scan_date)
    signals = scanner.strategy.generate_signals(stock.symbol, context)

    assert len(signals) == 1
    signal = signals[0]
    assert signal.explanation["Liquidity"]["status"] == "PASS"
    assert signal.explanation["Breakout"]["status"] == "PASS"
    assert signal.metadata["position_size"] > 0


@pytest.mark.asyncio
async def test_database_integrity_blocks_duplicates_and_broken_references(configured_db):
    stock, scan_date = _seed_stock_and_data(symbol="DUPL")
    with get_sync_session() as session:
        repo = OHLCVRepository(session)
        frame = repo.to_dataframe(stock.id, scan_date.replace(year=scan_date.year - 1), scan_date, "1d")
        records = DataPipeline._df_to_records(frame.iloc[-2:], stock.id, "1d")
        assert repo.bulk_insert_ignore(records) == 0

    with pytest.raises(IntegrityError):
        with get_sync_session() as session:
            session.add(
                Recommendation(
                    scan_job_id="missing-scan",
                    signal_id="missing-signal",
                    stock_id="missing-stock",
                    scan_date=scan_date,
                    strategy_name="sivcs_vcp",
                    strategy_version="2.0.0",
                    rank=1,
                    confidence_score=0.9,
                    risk_level="MEDIUM",
                    entry_price=100,
                    stop_loss=90,
                    target_price=120,
                    risk_per_share=10,
                    risk_pct=10,
                    explanation={},
                )
            )


@pytest.mark.asyncio
async def test_scan_persistence_is_deterministic_across_reruns(configured_db, monkeypatch):
    stock, scan_date = _seed_stock_and_data(symbol="SCAN")
    scanner = RecommendationScanner()

    async def _skip_pipeline(*_args, **_kwargs):
        return None

    monkeypatch.setattr(scanner.pipeline, "run_incremental", _skip_pipeline)
    monkeypatch.setattr(scanner, "_load_universe_and_stocks", lambda: [stock])

    first = await scanner.scan(scan_date=scan_date)
    second = await scanner.scan(scan_date=scan_date)

    assert first.recommendations_saved == 1
    assert second.recommendations_saved == 1

    with get_sync_session() as session:
        scan_jobs = session.execute(select(ScanJob)).scalars().all()
        recommendations = session.execute(select(Recommendation)).scalars().all()
        signals = session.execute(select(Signal)).scalars().all()
        assert len(scan_jobs) == 1
        assert len(recommendations) == 1
        assert len(signals) == 1
        assert recommendations[0].explanation["Risk"]["status"] == "PASS"
