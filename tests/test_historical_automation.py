from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta
import pytest
from sqlalchemy import select

from indian_swing.config.settings import settings
from indian_swing.database.connection import dispose_engine, get_sync_session, init_db
from indian_swing.database.models import (
    HistoricalScanSession,
    PaperTrade,
    Recommendation,
    ScanJob,
    Signal,
    Stock,
)
from indian_swing.database.repositories.ohlcv_repo import OHLCVRepository
from indian_swing.database.repositories.stock_repo import StockRepository
from indian_swing.recommendations.automation import (
    HistoricalScanManager,
    validate_date,
)
from indian_swing.data.pipeline import DataPipeline


@pytest.fixture()
def test_db(tmp_path):
    original_url = settings.database.url
    original_env = settings.app_env
    settings.database.url = f"sqlite+aiosqlite:///{tmp_path / 'test_automation.db'}"
    settings.app_env = "test"
    asyncio.run(dispose_engine())
    asyncio.run(init_db())
    yield
    asyncio.run(dispose_engine())
    settings.database.url = original_url
    settings.app_env = original_env


def test_date_validation():
    assert validate_date("11/06/26") == date(2026, 6, 11)
    assert validate_date(" 15/12/25 ") == date(2025, 12, 15)
    assert validate_date("invalid-date") is None
    assert validate_date("32/01/26") is None


def test_session_management(test_db):
    manager = HistoricalScanManager()
    
    # Assert no active session at first
    assert manager.get_active_session() is None

    # Create session
    dates = [date(2026, 6, 11), date(2026, 6, 12)]
    session = manager.create_session(dates)
    assert session is not None
    assert session.total_days == 2
    assert session.completed_days == 0
    assert session.queue == ["11/06/26", "12/06/26"]
    assert session.status == "active"

    # Get active session
    active = manager.get_active_session()
    assert active is not None
    assert active.id == session.id


def test_paper_trade_simulation(test_db):
    manager = HistoricalScanManager()

    # Seed stock and recommendation
    with get_sync_session() as session:
        stock_repo = StockRepository(session)
        stock = stock_repo.upsert(symbol="TEST", name="Test Inc", exchange="NSE")
        
        job = ScanJob(
            scan_uuid="scan-1",
            environment="TEST",
            strategy_name="sivcs_vcp",
            strategy_version="2.0.0",
            scan_date=date(2026, 6, 11),
            status="completed",
            total_stocks=1,
            started_at=datetime.utcnow()
        )
        session.add(job)
        session.flush()

        signal = Signal(
            scan_uuid="scan-1",
            stock_uuid=stock.stock_uuid,
            strategy_name="sivcs_vcp",
            strategy_version="2.0.0",
            signal_date=date(2026, 6, 11),
            direction="LONG",
            entry_price=100.0,
            stop_loss=90.0,
            target_1=120.0,
            target_2=130.0,
            risk_reward=2.0,
            confidence_score=0.9,
            quality="STRONG",
            risk_level="MEDIUM",
            holding_days=10,
        )
        session.add(signal)
        session.flush()

        rec = Recommendation(
            scan_uuid="scan-1",
            signal_id=signal.id,
            stock_uuid=stock.stock_uuid,
            scan_date=date(2026, 6, 11),
            strategy_name="sivcs_vcp",
            strategy_version="2.0.0",
            rank=1,
            confidence_score=0.9,
            risk_level="MEDIUM",
            entry_price=100.0,
            stop_loss=90.0,
            target_price=120.0,
            risk_per_share=10.0,
            risk_pct=10.0,
            position_size=100,
            explanation={},
        )
        session.add(rec)
        session.flush()

        # Seed OHLCV prices
        # Day 2: Price reaches entry but doesn't exit
        # Day 3: Hits target price
        ohlcv_repo = OHLCVRepository(session)
        records = [
            {"stock_uuid": stock.stock_uuid, "date": date(2026, 6, 11), "timeframe": "1d", "open": 98.0, "high": 99.0, "low": 97.0, "close": 98.5, "volume": 100000, "is_adjusted": True},
            {"stock_uuid": stock.stock_uuid, "date": date(2026, 6, 12), "timeframe": "1d", "open": 99.0, "high": 105.0, "low": 98.0, "close": 102.0, "volume": 100000, "is_adjusted": True},
            {"stock_uuid": stock.stock_uuid, "date": date(2026, 6, 15), "timeframe": "1d", "open": 103.0, "high": 122.0, "low": 102.0, "close": 121.0, "volume": 100000, "is_adjusted": True},
        ]
        ohlcv_repo.bulk_insert_ignore(records)
        session.commit()

    # Step 1: Create pending trade
    with get_sync_session() as session:
        created = manager.create_pending_trades(session, "scan-1")
        assert created == 1
        
        trade = session.execute(select(PaperTrade)).scalar_one()
        assert trade.status == "Pending"

    # Step 2: Update on Recommendation Day (should not trigger since current_date == scan_date)
    with get_sync_session() as session:
        manager.update_paper_trades(session, date(2026, 6, 11))
        trade = session.get(PaperTrade, trade.id)
        assert trade.status == "Pending"

    # Step 3: Update on next day (date 2026-06-12) - High reaches 105, triggers entry at 100
    with get_sync_session() as session:
        manager.update_paper_trades(session, date(2026, 6, 12))
        trade = session.get(PaperTrade, trade.id)
        assert trade.status == "Active"
        assert trade.entry_date == date(2026, 6, 12)
        assert trade.entry_price == 100.0

    # Step 4: Update on target day (date 2026-06-15) - High reaches 122, triggers target exit
    with get_sync_session() as session:
        manager.update_paper_trades(session, date(2026, 6, 15))
        trade = session.get(PaperTrade, trade.id)
        assert trade.status == "Closed"
        assert trade.exit_date == date(2026, 6, 15)
        assert trade.exit_price == 120.0
        assert trade.exit_reason == "Target"
        assert trade.pnl == 20.0  # (120 - 100)/100 * 100 = 20%
        assert trade.pnl_absolute == 2000.0  # 20 * 100 shares
        assert trade.r_multiple == 2.0  # (120 - 100)/(100 - 90) = 2.0
