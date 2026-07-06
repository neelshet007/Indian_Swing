from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, BackgroundTasks

from indian_swing.core.scanner import SIVCSScanner

router = APIRouter()


@router.post("/run")
async def trigger_scan(
    background_tasks: BackgroundTasks,
):
    """Trigger a manual scan. Runs in the background, returns immediately."""
    async def _scan():
        # Run SIVCSScanner in a separate thread so it doesn't block the async event loop
        import asyncio
        loop = asyncio.get_event_loop()
        scanner = SIVCSScanner()
        await loop.run_in_executor(None, scanner.run_scan)

    background_tasks.add_task(_scan)
    return {"status": "queued", "scan_date": str(date.today())}


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
