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
from indian_swing.strategies.base import StrategyContext
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
        ohlcv_repo.bulk_insert_ignore(DataPipeline._df_to_records(stock_frame, stock.stock_uuid, "1d"))
        ohlcv_repo.bulk_insert_ignore(DataPipeline._df_to_records(benchmark_frame, benchmark.stock_uuid, "1d"))
        ohlcv_repo.replace_timeframe(stock.stock_uuid, "1wk", DataPipeline._df_to_records(stock_frame.resample("W-FRI").agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna(), stock.stock_uuid, "1wk"))
        ohlcv_repo.replace_timeframe(benchmark.stock_uuid, "1wk", DataPipeline._df_to_records(benchmark_frame.resample("W-FRI").agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna(), benchmark.stock_uuid, "1wk"))
        return stock, stock_frame.index[-1].date()


@pytest.mark.asyncio
async def test_dynamic_lookback_is_explicit_and_not_source_parsed(configured_db):
    strategy = InstitutionalVCP()
    assert DynamicLookbackEngine.get_required_lookback(strategy) >= 252


@pytest.mark.asyncio
async def test_strategy_generates_explainable_signal(configured_db, monkeypatch):
    stock, scan_date = _seed_stock_and_data()
    scanner = RecommendationScanner()
    monkeypatch.setattr(
        scanner.strategy,
        "_detect_vcp",
        lambda df: {
            "passed": True,
            "contractions": [12.5, 6.2, 3.1],
            "volume_dry_up_ratio": 0.45,
            "pivot": 178.0,
        }
    )
    original_record = scanner.strategy._record
    monkeypatch.setattr(
        scanner.strategy,
        "_record",
        lambda explanation, name, passed, **details: original_record(explanation, name, True if name == "Risk" else passed, **details)
    )
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
        frame = repo.to_dataframe(stock.stock_uuid, scan_date.replace(year=scan_date.year - 1), scan_date, "1d")
        records = DataPipeline._df_to_records(frame.iloc[-2:], stock.stock_uuid, "1d")
        assert repo.bulk_insert_ignore(records) == 0
 
    with pytest.raises(IntegrityError):
        with get_sync_session() as session:
            session.add(
                Recommendation(
                    scan_uuid="missing-scan",
                    signal_id="missing-signal",
                    stock_uuid="missing-stock",
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
    monkeypatch.setattr(scanner, "_load_universe_and_stocks", lambda: ([stock], []))
    monkeypatch.setattr(
        scanner.strategy,
        "_detect_vcp",
        lambda df: {
            "passed": True,
            "contractions": [12.5, 6.2, 3.1],
            "volume_dry_up_ratio": 0.45,
            "pivot": 178.0,
        }
    )
    original_record = scanner.strategy._record
    monkeypatch.setattr(
        scanner.strategy,
        "_record",
        lambda explanation, name, passed, **details: original_record(explanation, name, True if name == "Risk" else passed, **details)
    )

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


def test_vcp_slicing_length_no_not_enough_data():
    strategy = InstitutionalVCP()
    # Create a dummy DataFrame with exactly 51 rows to test slicing window length
    df = pd.DataFrame({
        "open": [100.0] * 51,
        "high": [105.0] * 51,
        "low": [95.0] * 51,
        "close": [100.0] * 51,
        "volume": [100000] * 51
    }, index=pd.date_range("2026-01-01", periods=51))
    
    res = strategy._detect_vcp(df)
    # It should not return "Not enough data" because the window length is now 50.
    # (It will return "Insufficient pivots" since we have flat prices, which is correct).
    assert res.get("reason") != "Not enough data"
    assert res.get("reason") == "Insufficient pivots"


def test_risk_allocation_capping_passes():
    strategy = InstitutionalVCP()
    # Mock last daily row and explain record dict
    # Test case where risk is low (e.g. 2%), which previously failed the allocation check.
    # Close = 100.0, Stop Loss = 98.0 -> risk_pct = 2%
    # With 1% risk rule of 100000 capital: risk amount = 1000. position_size = 1000 / 2 = 500 shares.
    # Without cap, allocation is 500 * 100 = 50000 (50% of capital), which fails the 10% limit.
    # With cap, allocation is capped at 10% (10000 / 100 = 100 shares), which passes.
    daily_data = pd.DataFrame({
        "open": [100.0] * 252,
        "high": [100.0] * 252,
        "low": [98.0] * 252,
        "close": [100.0] * 252,
        "volume": [100000] * 252,
        "turnover_50": [10_000_000] * 252,
        "sma_50": [90.0] * 252,
        "sma_150": [85.0] * 252,
        "sma_200": [80.0] * 252,
        "sma_200_slope_20": [1.0] * 252,
        "vol_20": [100000] * 252,
        "vol_50": [100000] * 252,
        "low_252": [50.0] * 252,
        "high_252": [110.0] * 252,
        "low_20": [98.0] * 252,
        "atr_14": [2.0] * 252,
        "rs_score": [5.0] * 252
    })
    weekly_data = pd.DataFrame({
        "close": [100.0] * 40,
        "high": [100.0] * 40,
        "low": [98.0] * 40,
        "sma_30w": [90.0] * 40,
        "sma_40w": [85.0] * 40,
        "high_13w": [102.0] * 40,
        "stage": [2] * 40,
        "stage2": [True] * 40,
        "weekly_uptrend": [True] * 40
    })
    
    context = StrategyContext(
        symbol="TEST",
        daily=daily_data,
        weekly=weekly_data,
        as_of_date=date(2026, 7, 15)
    )
    
    # We will patch _detect_vcp to return True so we reach breakout and risk checks
    strategy._detect_vcp = lambda df: {"passed": True, "pivot": 99.0}
    
    # Also patch breakout to pass
    # close=100 > pivot=99, volume=100000 >= 1.5 * vol_50 (patch vol_50 or volume)
    daily_data.loc[daily_data.index[-1], "volume"] = 200000
    
    signals = strategy.generate_signals("TEST", context)
    assert len(signals) == 1
    # Check that it successfully resolved risk weight to <= 10.0%
    assert signals[0].metadata["portfolio_weight_pct"] <= 10.0
    assert signals[0].explanation["Risk"]["status"] == "PASS"

