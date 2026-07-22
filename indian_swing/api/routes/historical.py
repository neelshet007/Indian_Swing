from __future__ import annotations

import asyncio
from datetime import date
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy import select, update, delete, text

from indian_swing.database.connection import get_sync_session
from indian_swing.database.models import (
    HistoricalScanSession,
    PaperTrade,
    Recommendation,
    ScanJob,
)
from indian_swing.recommendations.automation import HistoricalScanManager
from pathlib import Path

from indian_swing.core.logging_setup import get_logger
logger = get_logger(__name__)

router = APIRouter()
_manager = HistoricalScanManager()
_active_task: Optional[asyncio.Task] = None
_active_session_id: Optional[str] = None


@router.on_event("startup")
def run_migrations():
    with get_sync_session() as session:
        try:
            session.execute(text("ALTER TABLE sw_historical_scan_sessions ADD COLUMN IF NOT EXISTS strategy_name VARCHAR(80);"))
            session.commit()
            logger.info("Database migration (strategy_name column) executed successfully.")
        except Exception as e:
            logger.error(f"Failed to run migration: {e}")


@router.get("/progress")
async def get_progress():
    """Get progress of the active historical scan session."""
    session_obj = None
    if _active_session_id:
        with get_sync_session() as session:
            session_obj = session.get(HistoricalScanSession, _active_session_id)
    if not session_obj:
        session_obj = _manager.get_active_session()
    if not session_obj:
        return {"status": "idle", "session": None}

    # Fetch counts
    with get_sync_session() as session:
        completed = session.execute(
            select(PaperTrade).where(PaperTrade.status == "Closed")
        ).scalars().all()
        active = session.execute(
            select(PaperTrade).where(PaperTrade.status == "Active")
        ).scalars().all()
        
        status = session_obj.status
        is_running = (_active_task is not None and not _active_task.done() and session_obj.id == _active_session_id)
        if status == "active" and not is_running:
            status = "paused"

        return {
            "status": "running" if is_running else status,
            "session_id": session_obj.id,
            "strategy_name": session_obj.strategy_name or "sivcs_vcp",
            "completed_days": session_obj.completed_days,
            "total_days": session_obj.total_days,
            "queue": session_obj.queue,
            "current_date": session_obj.current_date,
            "current_symbol": session_obj.current_symbol,
            "stocks_scanned": session_obj.stocks_scanned,
            "total_stocks": session_obj.total_stocks,
            "recommendations_today": session_obj.recommendations_today,
            "paper_trades_created": session_obj.paper_trades_created,
            "completed_trades": len(completed),
            "active_trades": len(active),
            "eta_minutes": round(session_obj.eta_minutes or 0.0, 1)
        }


@router.get("/scans")
async def list_historical_scans():
    """List completed historical scans."""
    loop = asyncio.get_running_loop()

    def _fetch():
        with get_sync_session() as session:
            jobs = session.execute(
                select(ScanJob)
                .where(ScanJob.strategy_name.in_(["sivcs_vcp", "amrc"]))
                .order_by(ScanJob.scan_date.desc())
            ).scalars().all()

            results = []
            for job in jobs:
                # Count active / closed trades for this scan
                recs = session.execute(
                    select(Recommendation).where(Recommendation.scan_uuid == job.scan_uuid)
                ).scalars().all()
                rec_ids = [r.id for r in recs]
                
                active_count = 0
                closed_count = 0
                if rec_ids:
                    active_count = len(session.execute(
                        select(PaperTrade).where(
                            PaperTrade.recommendation_id.in_(rec_ids),
                            PaperTrade.status == "Active"
                        )
                    ).scalars().all())
                    closed_count = len(session.execute(
                        select(PaperTrade).where(
                            PaperTrade.recommendation_id.in_(rec_ids),
                            PaperTrade.status == "Closed"
                        )
                    ).scalars().all())

                duration = 0.0
                if job.completed_at and job.started_at:
                    duration = (job.completed_at - job.started_at).total_seconds()

                results.append({
                    "scan_uuid": job.scan_uuid,
                    "scan_date": str(job.scan_date),
                    "status": job.status,
                    "stocks_scanned": job.stocks_scanned,
                    "recommendations_count": job.recommendations_created,
                    "duration_seconds": round(duration, 1),
                    "strategy_version": job.strategy_version,
                    "indicator_version": job.notes.get("indicator_version", "1.0.0") if isinstance(job.notes, dict) else "1.0.0",
                    "data_provider": "Upstox",
                    "market_status": job.market_status,
                    "active_trades": active_count,
                    "closed_trades": closed_count,
                    "strategy_name": job.strategy_name
                })
            return results

    return await loop.run_in_executor(None, _fetch)


@router.get("/scans/{scan_uuid}/recommendations")
async def get_scan_recommendations(scan_uuid: str):
    """Get recommendations snapshot for a specific scan."""
    loop = asyncio.get_running_loop()

    def _fetch():
        with get_sync_session() as session:
            recs = session.execute(
                select(Recommendation).where(Recommendation.scan_uuid == scan_uuid)
            ).scalars().all()

            results = []
            for r in recs:
                sig = r.signal
                explanation = sig.explanation if sig else {}
                results.append({
                    "recommendation_uuid": r.recommendation_uuid,
                    "symbol": r.stock.symbol,
                    "company_name": r.stock.name,
                    "entry_price": r.entry_price,
                    "stop_loss": r.stop_loss,
                    "target_price": r.target_price,
                    "risk_reward": sig.risk_reward if sig else 0.0,
                    "confidence_score": r.confidence_score,
                    "stage": explanation.get("Stage", {}).get("status", "N/A"),
                    "relative_strength": explanation.get("Relative Strength", {}).get("status", "N/A"),
                    "vcp_status": explanation.get("VCP", {}).get("status", "N/A"),
                    "breakout_status": explanation.get("Breakout", {}).get("status", "N/A"),
                    "explanation": r.explanation,
                    "reasons": sig.reasons if sig else []
                })
            return results

    return await loop.run_in_executor(None, _fetch)


@router.get("/paper-trades")
async def list_paper_trades():
    """List all paper trades."""
    loop = asyncio.get_running_loop()

    def _fetch():
        with get_sync_session() as session:
            trades = session.execute(
                select(PaperTrade).order_by(PaperTrade.entry_date.desc(), PaperTrade.created_at.desc())
            ).scalars().all()

            return [
                {
                    "id": t.id,
                    "symbol": t.symbol,
                    "status": t.status,
                    "entry_date": str(t.entry_date) if t.entry_date else None,
                    "exit_date": str(t.exit_date) if t.exit_date else None,
                    "holding_days": t.holding_days,
                    "entry_price": t.entry_price if t.entry_price is not None else (t.recommendation.entry_price if t.recommendation else None),
                    "exit_price": t.exit_price,
                    "pnl": t.pnl,
                    "pnl_absolute": t.pnl_absolute,
                    "r_multiple": t.r_multiple,
                    "max_favorable_excursion": t.max_favorable_excursion,
                    "max_adverse_excursion": t.max_adverse_excursion,
                    "exit_reason": t.exit_reason,
                    "original_target_price": t.original_target_price,
                    "stop_loss": t.stop_loss,
                    "execution_universe": t.execution_universe,
                    "accuracy_pct": round(t.recommendation.confidence_score * 100, 1) if (t.recommendation and t.recommendation.confidence_score is not None) else 0.0,
                    "recommendation_date": str(t.recommendation.scan_date) if (t.recommendation and t.recommendation.scan_date) else None,
                    "scan_uuid": t.recommendation.scan_uuid if t.recommendation else None,
                    "recommendation_uuid": t.recommendation.recommendation_uuid if t.recommendation else None,
                    "strategy_name": t.recommendation.strategy_name if t.recommendation else "sivcs_vcp",
                }
                for t in trades
            ]

    return await loop.run_in_executor(None, _fetch)


@router.get("/report")
async def get_performance_report():
    """Get performance stats report."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _manager.generate_final_report)


@router.get("/export")
async def download_excel_report(universe: str = "all", accuracy: str = "all"):
    """Download generated Excel journal report with filtering options."""
    loop = asyncio.get_running_loop()
    
    def _generate_and_get_path():
        temp_dir = Path("c:/Indian_Swing/scratch")
        temp_dir.mkdir(parents=True, exist_ok=True)
        filename = f"indian_swing_historical_journal_{universe}_{accuracy}.xlsx"
        excel_path = temp_dir / filename
        
        with get_sync_session() as session:
            _manager.generate_excel_report(
                session, 
                universe=universe, 
                accuracy=accuracy, 
                save_path=str(excel_path)
            )
        return excel_path

    excel_path = await loop.run_in_executor(None, _generate_and_get_path)

    if excel_path.exists():
        return FileResponse(
            path=excel_path,
            filename=f"indian_swing_historical_journal_{universe}_{accuracy}.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    raise HTTPException(status_code=404, detail="Excel file not generated yet")


@router.post("/start")
async def start_historical_scan(payload: dict):
    global _active_task, _active_session_id
    if _active_task is not None and not _active_task.done():
        raise HTTPException(status_code=409, detail="A scan session is already running")

    _manager.stop_requested = False

    strategy_name = payload.get("strategy", "sivcs_vcp")
    from indian_swing.strategies.registry import strategy_registry
    try:
        _manager.scanner.strategy = strategy_registry.get(strategy_name)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    from_date_str = payload.get("from_date")
    to_date_str = payload.get("to_date")
    
    if not from_date_str or not to_date_str:
        raise HTTPException(status_code=400, detail="Missing from_date or to_date")
        
    from datetime import datetime
    try:
        from_date = datetime.strptime(from_date_str, "%Y-%m-%d").date()
        to_date = datetime.strptime(to_date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    if from_date > to_date:
        raise HTTPException(status_code=400, detail="from_date must be before or equal to to_date")

    from indian_swing.database.repositories.stock_repo import StockRepository
    from indian_swing.config.settings import settings
    from indian_swing.database.models import Stock, OHLCV
    
    benchmark_symbol = settings.scanner.benchmark_symbol
    lookback = 282
    try:
        await _manager.scanner.pipeline.run_incremental(
            [benchmark_symbol],
            required_daily_bars=lookback,
            end=to_date,
            force_refresh=False
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch benchmark data: {exc}")

    with get_sync_session() as session:
        benchmark_stock = StockRepository(session).get_by_symbol(
            benchmark_symbol,
            exchange=settings.scanner.benchmark_exchange
        )
        if not benchmark_stock:
            raise HTTPException(status_code=400, detail="Benchmark stock metadata not found")

        candles = session.execute(
            select(OHLCV)
            .where(OHLCV.stock_uuid == benchmark_stock.stock_uuid)
            .where(OHLCV.timeframe == "1d")
            .where(OHLCV.date >= from_date)
            .where(OHLCV.date <= to_date)
            .order_by(OHLCV.date)
        ).scalars().all()
        trading_dates = [c.date for c in candles]

    if not trading_dates:
        raise HTTPException(status_code=400, detail="No active trading days found in the selected date range")

    session_obj = _manager.create_session(trading_dates, strategy_name=strategy_name)
    _active_session_id = session_obj.id

    async def _run():
        total = len(trading_dates)
        start_time = datetime.now()
        
        for idx in range(0, total):
            if _manager.stop_requested:
                logger.info("historical.scan_stopped_by_user")
                with get_sync_session() as db_session:
                    s_obj = db_session.get(HistoricalScanSession, session_obj.id)
                    if s_obj:
                        s_obj.status = "paused"
                        db_session.flush()
                        db_session.commit()
                break

            curr_date = trading_dates[idx]
            date_str = curr_date.strftime("%d/%m/%y")
            logger.info("historical.day_started", day=idx+1, total=total, date=date_str)
            result = await _manager.scanner.scan(scan_date=curr_date, force_refresh=False)

            with get_sync_session() as db_session:
                s_obj = db_session.get(HistoricalScanSession, session_obj.id)
                if s_obj:
                    s_obj.current_date = date_str
                    s_obj.status = "active"
                    db_session.flush()
                    db_session.commit()

            with get_sync_session() as db_session:
                _manager.update_paper_trades(db_session, curr_date)

            with get_sync_session() as db_session:
                trades_created = _manager.create_pending_trades(db_session, result.scan_uuid)
                
                completed_count = len(db_session.execute(
                    select(PaperTrade).where(PaperTrade.status == "Closed")
                ).scalars().all())
                active_count = len(db_session.execute(
                    select(PaperTrade).where(PaperTrade.status == "Active")
                ).scalars().all())

                processed = idx + 1
                elapsed = (datetime.now() - start_time).total_seconds()
                avg_time = elapsed / processed if processed > 0 else 0
                remaining = total - (idx + 1)
                eta_min = (avg_time * remaining) / 60.0

                s_obj = db_session.get(HistoricalScanSession, session_obj.id)
                if s_obj:
                    s_obj.completed_days = idx + 1
                    s_obj.stocks_scanned = result.stocks_scanned
                    s_obj.total_stocks = result.stocks_scanned + result.failed_stocks
                    s_obj.recommendations_today = result.recommendations_saved
                    s_obj.paper_trades_created = trades_created
                    s_obj.completed_trades = completed_count
                    s_obj.active_trades = active_count
                    s_obj.eta_minutes = eta_min
                    if idx + 1 == total:
                        s_obj.status = "completed"
                    db_session.flush()
                    db_session.commit()

                _manager.generate_excel_report(db_session)
            
            logger.info("historical.day_completed", day=idx+1, total=total, date=date_str, recs_found=result.recommendations_saved, trades_created=trades_created)

    _active_task = asyncio.create_task(_run())
    return {"status": "started", "total_days": len(trading_dates)}


@router.post("/resume")
async def resume_historical_scan(payload: dict = None):
    """Resume historical scan in the background."""
    global _active_task, _active_session_id
    if _active_task is not None and not _active_task.done():
        raise HTTPException(status_code=409, detail="A scan session is already running")

    _manager.stop_requested = False
    session_id = payload.get("session_id") if payload else None

    with get_sync_session() as session:
        if session_id:
            session_obj = session.get(HistoricalScanSession, session_id)
        else:
            session_obj = _manager.get_active_session()

        if not session_obj:
            raise HTTPException(status_code=404, detail="No historical scan found to resume")

        session_id = session_obj.id
        completed_days = session_obj.completed_days
        queue = list(session_obj.queue)
        strategy_name = session_obj.strategy_name or "sivcs_vcp"

    _active_session_id = session_id

    # Load strategy
    from indian_swing.strategies.registry import strategy_registry
    _manager.scanner.strategy = strategy_registry.get(strategy_name)

    async def _run():
        from datetime import datetime
        
        # Re-parse dates
        dates = []
        for ds in queue:
            from indian_swing.recommendations.automation import validate_date
            parsed = validate_date(ds)
            if parsed:
                dates.append(parsed)

        total = len(dates)
        start_idx = completed_days
        
        start_time = datetime.now()
        for idx in range(start_idx, total):
            if _manager.stop_requested:
                logger.info("historical.scan_stopped_by_user")
                with get_sync_session() as db_session:
                    s_obj = db_session.get(HistoricalScanSession, session_id)
                    if s_obj:
                        s_obj.status = "paused"
                        db_session.flush()
                        db_session.commit()
                break

            curr_date = dates[idx]
            date_str = curr_date.strftime("%d/%m/%y")
            logger.info("historical.day_started", day=idx+1, total=total, date=date_str)
            
            # Run scan first to fetch/download OHLCV data for curr_date
            result = await _manager.scanner.scan(scan_date=curr_date, force_refresh=False)

            # Update session progress info
            with get_sync_session() as db_session:
                s_obj = db_session.get(HistoricalScanSession, session_id)
                if s_obj:
                    s_obj.current_date = date_str
                    s_obj.status = "active"
                    db_session.flush()
                    db_session.commit()

            # Run paper trade checks AFTER scan is complete so data exists in the database
            with get_sync_session() as db_session:
                _manager.update_paper_trades(db_session, curr_date)

            # Insert pending trades and update stats
            with get_sync_session() as db_session:
                trades_created = _manager.create_pending_trades(db_session, result.scan_uuid)
                
                # Fetch counts
                completed_count = len(db_session.execute(
                    select(PaperTrade).where(PaperTrade.status == "Closed")
                ).scalars().all())
                active_count = len(db_session.execute(
                    select(PaperTrade).where(PaperTrade.status == "Active")
                ).scalars().all())

                # Calculate ETA
                processed = idx + 1 - start_idx
                elapsed = (datetime.now() - start_time).total_seconds()
                avg_time = elapsed / processed if processed > 0 else 0
                remaining = total - (idx + 1)
                eta_min = (avg_time * remaining) / 60.0

                s_obj = db_session.get(HistoricalScanSession, session_id)
                if s_obj:
                    s_obj.completed_days = idx + 1
                    s_obj.stocks_scanned = result.stocks_scanned
                    s_obj.total_stocks = result.stocks_scanned + result.failed_stocks
                    s_obj.recommendations_today = result.recommendations_saved
                    s_obj.paper_trades_created = trades_created
                    s_obj.completed_trades = completed_count
                    s_obj.active_trades = active_count
                    s_obj.eta_minutes = eta_min
                    if idx + 1 == total:
                        s_obj.status = "completed"
                    db_session.flush()
                    db_session.commit()

                # Excel auto-update
                _manager.generate_excel_report(db_session)
            
            logger.info("historical.day_completed", day=idx+1, total=total, date=date_str, recs_found=result.recommendations_saved, trades_created=trades_created)

    _active_task = asyncio.create_task(_run())
    return {"status": "resumed"}


@router.post("/pause")
async def pause_historical_scan():
    """Pause the currently running historical scan session."""
    _manager.stop_requested = True
    return {"status": "pause_requested"}


@router.get("/sessions")
async def list_sessions():
    """List all historical scan sessions."""
    loop = asyncio.get_running_loop()
    def _fetch():
        with get_sync_session() as session:
            sessions = session.execute(
                select(HistoricalScanSession)
                .order_by(HistoricalScanSession.created_at.desc())
            ).scalars().all()
            return [
                {
                    "id": s.id,
                    "total_days": s.total_days,
                    "completed_days": s.completed_days,
                    "status": "active" if (_active_task is not None and not _active_task.done() and s.id == _active_session_id) else (s.status if s.status != "active" else "paused"),
                    "strategy_name": s.strategy_name or "sivcs_vcp",
                    "current_date": s.current_date,
                    "stocks_scanned": s.stocks_scanned,
                    "recommendations_today": s.recommendations_today,
                    "paper_trades_created": s.paper_trades_created,
                    "created_at": s.created_at.isoformat() if s.created_at else None
                }
                for s in sessions
            ]
    return await loop.run_in_executor(None, _fetch)


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a historical scan session by ID."""
    with get_sync_session() as session:
        s_obj = session.get(HistoricalScanSession, session_id)
        if s_obj:
            session.delete(s_obj)
            session.commit()
            return {"status": "deleted"}
        raise HTTPException(status_code=404, detail="Session not found")
