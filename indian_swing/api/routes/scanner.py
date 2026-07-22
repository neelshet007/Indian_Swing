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
async def trigger_scan(scan_date: Optional[date] = None, strategy: str = "all", force_refresh: bool = False):
    global _active_task
    if _active_task is not None and not _active_task.done():
        raise HTTPException(status_code=409, detail="A scan is already running")

    target_date = scan_date or date.today()
    if target_date > date.today():
        raise HTTPException(status_code=400, detail="Cannot run scans for future dates")

    from indian_swing.strategies.registry import strategy_registry

    if strategy == "all":
        strategies_to_run = ["sivcs_vcp", "amrc"]
    else:
        strategies_to_run = [strategy]

    # Validate strategies
    for s in strategies_to_run:
        try:
            strategy_registry.get(s)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    if not force_refresh:
        loop = asyncio.get_running_loop()
        def _check_existing():
            with get_sync_session() as session:
                completed_count = 0
                for s in strategies_to_run:
                    job = session.execute(
                        select(ScanJob).where(
                            ScanJob.scan_date == target_date,
                            ScanJob.status == "completed",
                            ScanJob.strategy_name == s
                        )
                    ).scalars().first()
                    if job:
                        completed_count += 1
                return completed_count == len(strategies_to_run)

        all_completed = await loop.run_in_executor(None, _check_existing)
        if all_completed:
            return {"status": "completed", "scan_date": str(target_date)}

    async def _run_scans():
        for s in strategies_to_run:
            try:
                _scanner.strategy = strategy_registry.get(s)
                await _scanner.scan(scan_date=target_date, force_refresh=force_refresh)
            except Exception as exc:
                # Log error and continue to next strategy
                import logging
                logging.getLogger(__name__).error(f"Failed to run strategy {s} in background: {exc}")

    _active_task = asyncio.create_task(_run_scans())
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
