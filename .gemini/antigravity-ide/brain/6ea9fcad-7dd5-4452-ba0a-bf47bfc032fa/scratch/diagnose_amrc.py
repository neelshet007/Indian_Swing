from indian_swing.database.connection import get_sync_session
from indian_swing.database.models import ScanJob
from sqlalchemy import select

with get_sync_session() as session:
    jobs = session.execute(
        select(ScanJob)
        .where(ScanJob.strategy_name == "amrc")
        .order_by(ScanJob.scan_date.desc())
        .limit(5)
    ).scalars().all()
    
    print(f"Found {len(jobs)} AMRC scan jobs.")
    for j in jobs:
        print(f"Date: {j.scan_date} | Recs: {j.recommendations_created} | Status: {j.status}")
        print(f"Filter Summary: {j.filter_summary}")
        print("-" * 50)
