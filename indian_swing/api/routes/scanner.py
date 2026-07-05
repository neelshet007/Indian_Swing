from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, BackgroundTasks

from indian_swing.recommendations.scanner import RecommendationScanner

router = APIRouter()


@router.post("/run")
async def trigger_scan(
    background_tasks: BackgroundTasks,
):
    """Trigger a manual scan. Runs in the background, returns immediately."""
    async def _scan():
        scanner = RecommendationScanner()
        await scanner.scan(date.today())

    background_tasks.add_task(_scan)
    return {"status": "queued", "scan_date": str(date.today())}


@router.get("/jobs")
async def list_scan_jobs(limit: int = 20):
    from sqlalchemy import select
    from indian_swing.database.connection import get_session
    from indian_swing.database.models import ScanJob

    async with get_session() as session:
        result = await session.execute(
            select(ScanJob).order_by(ScanJob.created_at.desc()).limit(limit)
        )
        jobs = result.scalars().all()

    return [
        {
            "id": j.id,
            "scan_date": str(j.scan_date),
            "status": j.status,
            "stocks_scanned": j.stocks_scanned,
            "signals_generated": j.signals_generated,
            "recommendations_created": j.recommendations_created,
            "error": j.error,
            "started_at": str(j.started_at) if j.started_at else None,
            "completed_at": str(j.completed_at) if j.completed_at else None,
        }
        for j in jobs
    ]
