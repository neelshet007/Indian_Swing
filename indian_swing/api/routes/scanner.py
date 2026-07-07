from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, BackgroundTasks

from indian_swing.core.scanner import SIVCSScanner

router = APIRouter()

# Global state to hold real-time scan progress
ACTIVE_SCAN_STATE = {
    "total_stocks": 0,
    "completed": 0,
    "failed": 0,
    "remaining": 0,
    "current_symbol": "",
    "current_stage": "Idle"
}

@router.get("/progress")
async def get_progress():
    """Returns the real-time progress of the active scan."""
    return ACTIVE_SCAN_STATE


@router.post("/run")
async def trigger_scan(
    background_tasks: BackgroundTasks,
    scan_date: Optional[date] = None,
):
    """Trigger a manual scan. Runs in the background, returns immediately."""
    global ACTIVE_SCAN_STATE
    
    if ACTIVE_SCAN_STATE["current_stage"] not in ("Idle", "Completed", "Failed"):
        return {"status": "error", "detail": "A scan is already running"}
        
    ACTIVE_SCAN_STATE["current_stage"] = "Starting..."
    ACTIVE_SCAN_STATE["completed"] = 0
    ACTIVE_SCAN_STATE["failed"] = 0
    ACTIVE_SCAN_STATE["total_stocks"] = 0
    
    target_date = scan_date or date.today()
    
    async def _scan():
        from indian_swing.core.logging_setup import get_logger
        logger = get_logger(__name__)
        
        try:
            logger.info("Scan Background Task: Initialized")
            # Run SIVCSScanner in a separate thread so it doesn't block the async event loop
            import asyncio
            loop = asyncio.get_event_loop()
            scanner = SIVCSScanner()
            
            def update_progress(state):
                global ACTIVE_SCAN_STATE
                ACTIVE_SCAN_STATE.update(state)
                
            from indian_swing.database.connection import get_sync_session
            from indian_swing.database.models import ScanJob, Signal, Recommendation, Stock
            from datetime import datetime
            
            logger.info("Scan Background Task: Starting executor")
            scan_date = target_date
            
            # 1. Create ScanJob
            def _create_job():
                with get_sync_session() as session:
                    job = ScanJob(scan_date=scan_date, status="running", started_at=datetime.utcnow())
                    session.add(job)
                    session.commit()
                    return job.id
            job_id = await loop.run_in_executor(None, _create_job)
            
            # 2. Run scan
            signals = await loop.run_in_executor(None, scanner.run_scan, update_progress, target_date)
            
            # 3. Save to DB
            def _save_signals():
                with get_sync_session() as session:
                    # Clean up existing recommendations and signals for this scan_date to avoid duplicates
                    from sqlalchemy import delete, select
                    existing_signals = session.execute(
                        select(Signal.id).where(Signal.signal_date == scan_date)
                    ).scalars().all()
                    
                    if existing_signals:
                        session.execute(
                            delete(Recommendation).where(Recommendation.signal_id.in_(existing_signals))
                        )
                        session.execute(
                            delete(Signal).where(Signal.id.in_(existing_signals))
                        )
                        
                    job = session.get(ScanJob, job_id)
                    job.total_stocks = ACTIVE_SCAN_STATE["total_stocks"]
                    job.stocks_scanned = ACTIVE_SCAN_STATE["completed"]
                    job.signals_generated = len(signals)
                    
                    if not signals:
                        job.status = "completed"
                        job.completed_at = datetime.utcnow()
                        session.commit()
                        return
                    stocks = session.execute(select(Stock)).scalars().all()
                    stock_map = {s.symbol: s.id for s in stocks}
                    
                    rank = 1
                    for s in signals:
                        stock_id = stock_map.get(s.symbol)
                        if not stock_id:
                            logger.error(f"Save Signals: Could not find stock_id for symbol {s.symbol}")
                            continue
                        
                        try:
                            # create signal
                            new_signal = Signal(
                                stock_id=stock_id,
                                strategy_name=scanner.strategy.__class__.__name__,
                                signal_date=scan_date,
                                direction=s.direction.value if hasattr(s.direction, "value") else str(s.direction),
                                entry_price=s.entry_price,
                                stop_loss=s.stop_loss,
                                target_1=s.target_1,
                                target_2=s.target_2,
                                risk_reward=s.risk_reward,
                                confidence_score=s.confidence_score,
                                quality=s.quality.value if hasattr(s.quality, "value") else str(s.quality),
                                holding_days=s.holding_days,
                                reasons=s.reasons,
                                metadata_=s.metadata
                            )
                            session.add(new_signal)
                            session.flush() # get signal id
                            
                            # create recommendation
                            rec = Recommendation(
                                stock_id=stock_id,
                                signal_id=new_signal.id,
                                scan_date=scan_date,
                                rank=rank,
                                confidence_score=s.confidence_score,
                                risk_level=s.risk_level.value if hasattr(s.risk_level, "value") else str(s.risk_level),
                                summary=f"{s.symbol} Breakout Setup"
                            )
                            session.add(rec)
                            rank += 1
                        except Exception as e:
                            logger.error(f"Save Signals: Failed to save signal for {s.symbol}: {e}")
                            session.rollback()
                        
                    job.recommendations_created = rank - 1
                    job.status = "completed"
                    job.completed_at = datetime.utcnow()
                    session.commit()
            
            await loop.run_in_executor(None, _save_signals)
            
            # Reset stage when done
            ACTIVE_SCAN_STATE["current_stage"] = "Completed"
            ACTIVE_SCAN_STATE["current_symbol"] = ""
            logger.info("Scan Background Task: Completed successfully")
            
        except Exception as e:
            logger.error(f"Scan Background Task: Crashed with exception: {e}")
            ACTIVE_SCAN_STATE["current_stage"] = "Failed"
            ACTIVE_SCAN_STATE["current_symbol"] = f"Crash: {str(e)}"
 
    background_tasks.add_task(_scan)
    return {"status": "queued", "scan_date": str(target_date)}


@router.get("/jobs")
async def list_scan_jobs(limit: int = 20):
    from sqlalchemy import select
    from indian_swing.database.connection import get_sync_session
    from indian_swing.database.models import ScanJob
    import asyncio

    def _fetch_jobs():
        with get_sync_session() as session:
            result = session.execute(
                select(ScanJob).order_by(ScanJob.created_at.desc()).limit(limit)
            )
            return result.scalars().all()

    loop = asyncio.get_event_loop()
    jobs = await loop.run_in_executor(None, _fetch_jobs)

    return [
        {
            "id": j.id,
            "scan_date": str(j.scan_date),
            "status": j.status,
            "total_stocks": getattr(j, "total_stocks", 0),
            "stocks_scanned": j.stocks_scanned,
            "signals_generated": j.signals_generated,
            "recommendations_created": j.recommendations_created,
            "error": j.error,
            "started_at": str(j.started_at) if j.started_at else None,
            "completed_at": str(j.completed_at) if j.completed_at else None,
        }
        for j in jobs
    ]
