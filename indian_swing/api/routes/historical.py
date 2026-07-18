from __future__ import annotations

import asyncio
from datetime import date
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy import select

from indian_swing.database.connection import get_sync_session
from indian_swing.database.models import (
    HistoricalScanSession,
    PaperTrade,
    Recommendation,
    ScanJob,
)
from indian_swing.recommendations.automation import HistoricalScanManager
from pathlib import Path

router = APIRouter()
_manager = HistoricalScanManager()
_active_task: Optional[asyncio.Task] = None


@router.get("/progress")
async def get_progress():
    """Get progress of the active historical scan session."""
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
        
        return {
            "status": "running" if session_obj.status == "active" else session_obj.status,
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
                .where(ScanJob.strategy_name == "sivcs_vcp")
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
                    "closed_trades": closed_count
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
                    "risk_reward": r.risk_reward,
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
                    "entry_price": t.entry_price,
                    "exit_price": t.exit_price,
                    "pnl": t.pnl,
                    "pnl_absolute": t.pnl_absolute,
                    "r_multiple": t.r_multiple,
                    "max_favorable_excursion": t.max_favorable_excursion,
                    "max_adverse_excursion": t.max_adverse_excursion,
                    "exit_reason": t.exit_reason
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
async def download_excel_report():
    """Download generated Excel journal report."""
    excel_path = Path("c:/Indian_Swing/indian_swing_historical_journal.xlsx")
    if not excel_path.exists():
        # Trigger generation dynamically
        with get_sync_session() as session:
            _manager.generate_excel_report(session)

    if excel_path.exists():
        return FileResponse(
            path=excel_path,
            filename="indian_swing_historical_journal.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    raise HTTPException(status_code=404, detail="Excel file not generated yet")


@router.post("/resume")
async def resume_historical_scan(background_tasks: BackgroundTasks):
    """Resume historical scan in the background."""
    global _active_task
    if _active_task is not None and not _active_task.done():
        raise HTTPException(status_code=409, detail="A scan session is already running")

    session_obj = _manager.get_active_session()
    if not session_obj:
        raise HTTPException(status_code=404, detail="No active historical scan found to resume")

    # Run in background non-interactively
    async def _run():
        from datetime import datetime
        manager = HistoricalScanManager()
        
        # Re-parse dates
        dates = []
        for ds in session_obj.queue:
            from indian_swing.recommendations.automation import validate_date
            parsed = validate_date(ds)
            if parsed:
                dates.append(parsed)

        total = len(dates)
        start_idx = session_obj.completed_days
        
        start_time = datetime.now()
        for idx in range(start_idx, total):
            curr_date = dates[idx]
            
            # Update session progress info
            with get_sync_session() as db_session:
                # Re-fetch session
                s_obj = db_session.get(HistoricalScanSession, session_obj.id)
                if s_obj:
                    s_obj.current_date = curr_date.strftime("%d/%m/%y")
                    s_obj.status = "active"
                    db_session.flush()

            # Run paper trade checks
            with get_sync_session() as db_session:
                manager.update_paper_trades(db_session, curr_date)

            # Run scan
            result = await manager.scanner.scan(scan_date=curr_date, force_refresh=False)

            # Insert pending trades and update stats
            with get_sync_session() as db_session:
                trades_created = manager.create_pending_trades(db_session, result.scan_uuid)
                
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

                # Excel auto-update
                manager.generate_excel_report(db_session)

    _active_task = asyncio.create_task(_run())
    return {"status": "resumed"}
