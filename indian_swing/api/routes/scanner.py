from __future__ import annotations

import asyncio
from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from indian_swing.database.connection import get_sync_session
from indian_swing.database.models import ScanJob
from indian_swing.recommendations.scanner import RecommendationScanner

router = APIRouter()
_scanner = RecommendationScanner()
_active_task: asyncio.Task | None = None


@router.get("/progress")
async def get_progress():
    return _scanner.progress_state


@router.post("/run")
async def trigger_scan(scan_date: Optional[date] = None, force_refresh: bool = False):
    global _active_task
    if _active_task is not None and not _active_task.done():
        raise HTTPException(status_code=409, detail="A scan is already running")

    target_date = scan_date or date.today()

    if not force_refresh:
        loop = asyncio.get_running_loop()
        def _check_existing():
            with get_sync_session() as session:
                return session.execute(
                    select(ScanJob).where(
                        ScanJob.scan_date == target_date,
                        ScanJob.status == "completed"
                    )
                ).scalars().first()
        existing_job = await loop.run_in_executor(None, _check_existing)
        if existing_job:
            return {"status": "completed", "scan_uuid": existing_job.scan_uuid, "scan_date": str(target_date)}

    _active_task = asyncio.create_task(_scanner.scan(scan_date=target_date, force_refresh=force_refresh))
    return {"status": "queued", "scan_date": str(target_date)}


@router.get("/jobs")
async def list_scan_jobs(limit: int = 20):
    loop = asyncio.get_running_loop()

    def _fetch():
        with get_sync_session() as session:
            jobs = session.execute(
                select(ScanJob).order_by(ScanJob.created_at.desc()).limit(limit)
            ).scalars().all()
            return [
                {
                    "id": job.scan_uuid,
                    "scan_date": str(job.scan_date),
                    "status": job.status,
                    "strategy_name": job.strategy_name,
                    "strategy_version": job.strategy_version,
                    "total_stocks": job.total_stocks,
                    "stocks_scanned": job.stocks_scanned,
                    "signals_generated": job.signals_generated,
                    "recommendations_created": job.recommendations_created,
                    "failed_stocks": job.failed_stocks,
                    "filter_summary": job.filter_summary,
                    "validation_summary": job.validation_summary,
                    "errors": job.notes.get("errors", []) if isinstance(job.notes, dict) else [],
                    "error": job.error,
                    "started_at": job.started_at.isoformat() if job.started_at else None,
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                }
                for job in jobs
            ]

    return await loop.run_in_executor(None, _fetch)
