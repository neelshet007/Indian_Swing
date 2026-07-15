"""
Cleanup: Mark all stale 'running' ScanJobs as 'failed'.
Safe to run multiple times (idempotent).
"""
import sys
from datetime import datetime, timedelta

sys.path.insert(0, ".")

from indian_swing.database.connection import get_sync_session
from indian_swing.database.models import ScanJob
from sqlalchemy import select

STALE_THRESHOLD_MINUTES = 60  # mark running jobs older than this as failed

with get_sync_session() as session:
    cutoff = datetime.utcnow() - timedelta(minutes=STALE_THRESHOLD_MINUTES)
    stale_jobs = session.execute(
        select(ScanJob).where(
            ScanJob.status == "running",
            ScanJob.started_at < cutoff,
        )
    ).scalars().all()
    print(f"Found {len(stale_jobs)} stale running job(s) to mark as failed.")
    for job in stale_jobs:
        job.status = "failed"
        job.error = "Orphaned: server was killed or crashed mid-scan"
        job.completed_at = datetime.utcnow()
        print(f"  Marked failed: scan_uuid={job.scan_uuid} date={job.scan_date} started={job.started_at}")
    print("Done — all stale jobs are now status='failed'.")
