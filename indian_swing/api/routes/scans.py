from __future__ import annotations

import asyncio
from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from indian_swing.database.connection import get_sync_session
from indian_swing.database.models import ScanJob

router = APIRouter()


def _serialize_scan(job: ScanJob) -> dict:
    return {
        "id": job.scan_uuid,
        "scan_uuid": job.scan_uuid,
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


@router.get("/latest")
async def get_latest_scan():
    loop = asyncio.get_running_loop()

    def _fetch() -> dict | None:
        with get_sync_session() as session:
            job = session.execute(
                select(ScanJob)
                .where(ScanJob.status == "completed")
                .order_by(ScanJob.scan_date.desc(), ScanJob.created_at.desc())
                .limit(1)
            ).scalar_one_or_none()
            return _serialize_scan(job) if job else None

    result = await loop.run_in_executor(None, _fetch)
    if result is None:
        raise HTTPException(status_code=404, detail="No completed scan found")
    return result


@router.get("/history")
async def get_scan_history(limit: int = 50):
    loop = asyncio.get_running_loop()

    def _fetch() -> list[dict]:
        with get_sync_session() as session:
            jobs = session.execute(
                select(ScanJob)
                .where(ScanJob.status == "completed")
                .order_by(ScanJob.scan_date.desc(), ScanJob.created_at.desc())
                .limit(limit)
            ).scalars().all()
            return [_serialize_scan(job) for job in jobs]

    return await loop.run_in_executor(None, _fetch)


@router.get("/date/{scan_date_val}")
async def get_scan_by_date(scan_date_val: date):
    loop = asyncio.get_running_loop()

    def _fetch() -> dict | None:
        from datetime import datetime, timedelta
        stale_cutoff = datetime.utcnow() - timedelta(hours=2)
        with get_sync_session() as session:
            # Prefer completed scans; only accept running if started within last 2 hours
            from sqlalchemy import case as sa_case
            job = session.execute(
                select(ScanJob)
                .where(
                    ScanJob.scan_date == scan_date_val,
                    (
                        (ScanJob.status == "completed") |
                        ((ScanJob.status == "running") & (ScanJob.started_at >= stale_cutoff))
                    ),
                )
                .order_by(
                    sa_case((ScanJob.status == "completed", 1), (ScanJob.status == "running", 2), else_=3).asc(),
                    ScanJob.created_at.desc(),
                )
                .limit(1)
            ).scalar_one_or_none()
            return _serialize_scan(job) if job else None

    result = await loop.run_in_executor(None, _fetch)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No scan job found for date {scan_date_val}")
    return result


@router.get("/uuid/{scan_uuid}")
async def get_scan_by_uuid(scan_uuid: str):
    loop = asyncio.get_running_loop()

    def _fetch() -> dict | None:
        with get_sync_session() as session:
            job = session.get(ScanJob, scan_uuid)
            return _serialize_scan(job) if job else None

    result = await loop.run_in_executor(None, _fetch)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Scan job not found for UUID {scan_uuid}")
    return result
