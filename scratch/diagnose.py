"""
Forensic Diagnosis Script — SwingIQ Recommendation Pipeline
Run: python scratch/diagnose.py
"""
import sys
import json
from datetime import date, timedelta

sys.path.insert(0, ".")

from indian_swing.database.connection import get_sync_session
from indian_swing.database.models import Recommendation, ScanJob, Signal
from indian_swing.database.repositories.ohlcv_repo import OHLCVRepository
from indian_swing.database.repositories.stock_repo import StockRepository
from sqlalchemy import select, func

TARGET_DATE = date(2026, 7, 15)

SEP = "-" * 70
print(SEP)
print("STEP 1 — SCAN JOB STATUS")
print(SEP)
with get_sync_session() as session:
    jobs = session.execute(
        select(ScanJob).where(ScanJob.scan_date == TARGET_DATE).order_by(ScanJob.created_at.desc())
    ).scalars().all()
    if not jobs:
        print(f"NO ScanJob records for {TARGET_DATE}")
    for j in jobs:
        print(f"  scan_uuid       : {j.scan_uuid}")
        print(f"  status          : {j.status}")
        print(f"  total_stocks    : {j.total_stocks}")
        print(f"  stocks_scanned  : {j.stocks_scanned}")
        print(f"  failed_stocks   : {j.failed_stocks}")
        print(f"  signals_gen     : {j.signals_generated}")
        print(f"  recs_created    : {j.recommendations_created}")
        print(f"  filter_summary  : {json.dumps(j.filter_summary, indent=4)}")
        print(f"  validation_summ : {json.dumps(j.validation_summary, indent=4)}")
        print(f"  started_at      : {j.started_at}")
        print(f"  completed_at    : {j.completed_at}")
        print(f"  notes           : {json.dumps(j.notes, indent=4) if j.notes else 'None'}")
        print()

print(SEP)
print("STEP 2 — RECOMMENDATION COUNT IN DATABASE")
print(SEP)
with get_sync_session() as session:
    for job in session.execute(
        select(ScanJob).where(ScanJob.scan_date == TARGET_DATE).order_by(ScanJob.created_at.desc())
    ).scalars().all():
        recs = session.execute(
            select(func.count()).where(Recommendation.scan_uuid == job.scan_uuid)
        ).scalar()
        sigs = session.execute(
            select(func.count()).where(Signal.scan_uuid == job.scan_uuid)
        ).scalar()
        print(f"  scan_uuid={job.scan_uuid[:12]}...  status={job.status}")
        print(f"    sw_signals count        : {sigs}")
        print(f"    sw_recommendations count: {recs}")

print(SEP)
print("STEP 3 — VALIDATOR RULE MISMATCH CHECK")
print(SEP)
print("  Validator checks explanation.keys() == required_steps")
print("  Required steps in validator  : {Market Filter, Sector Filter, Liquidity, Trend, Stage, Relative Strength, VCP, Breakout, Risk}")
print("  Strategy explanation produces : {Market Filter, Sector Filter, Liquidity, Trend, Stage, Relative Strength, VCP, Breakout, Risk}")

with get_sync_session() as session:
    for job in session.execute(
        select(ScanJob).where(ScanJob.scan_date == TARGET_DATE)
    ).scalars().all():
        recs = session.execute(
            select(Recommendation).where(Recommendation.scan_uuid == job.scan_uuid)
        ).scalars().all()
        print(f"\n  scan_uuid={job.scan_uuid[:12]} — {len(recs)} recommendations found in DB")
        for rec in recs[:3]:
            exp = rec.explanation or {}
            exp_keys = set(exp.keys())
            required_steps = {"Market Filter", "Sector Filter", "Liquidity", "Trend", "Stage", "Relative Strength", "VCP", "Breakout", "Risk"}
            keys_match = exp_keys == required_steps
            all_pass = all(v.get("status") == "PASS" for v in exp.values())
            print(f"    rec.id={rec.id[:12]}  explanation_keys_match={keys_match}  all_rules_pass={all_pass}")
            if not keys_match:
                print(f"      DB has keys  : {sorted(exp_keys)}")
                print(f"      Expected keys: {sorted(required_steps)}")

print(SEP)
print("STEP 4 — API QUERY TRACE (get_latest)")
print(SEP)
print("  /api/scans/latest uses: status='completed' ORDER BY scan_date DESC")
print("  /api/recommendations/{uuid} uses: get_by_scan(uuid)")
with get_sync_session() as session:
    from sqlalchemy import case
    latest = session.execute(
        select(ScanJob)
        .where(ScanJob.status == "completed")
        .order_by(ScanJob.scan_date.desc(), ScanJob.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    if latest:
        print(f"  Latest completed scan_uuid : {latest.scan_uuid}")
        print(f"  scan_date                  : {latest.scan_date}")
        rec_count = session.execute(
            select(func.count()).where(Recommendation.scan_uuid == latest.scan_uuid)
        ).scalar()
        print(f"  Recommendations via scan_uuid: {rec_count}")
    else:
        print("  NO completed scan jobs found at all!")

print(SEP)
print("STEP 5 — get_by_date() QUERY TRACE")
print(SEP)
print("  get_by_date picks status IN ['running','completed'], orders RUNNING first, then COMPLETED")
print("  BUG CHECK: If a 'running' scan exists with 0 recs it hides the completed scan")
with get_sync_session() as session:
    from sqlalchemy import case as sa_case
    latest_scan_uuid = session.execute(
        select(ScanJob.scan_uuid)
        .where(ScanJob.scan_date == TARGET_DATE)
        .where(ScanJob.status.in_(["running", "completed"]))
        .order_by(
            sa_case((ScanJob.status == "running", 1), (ScanJob.status == "completed", 2), else_=3).asc(),
            ScanJob.created_at.desc()
        )
        .limit(1)
    ).scalar_one_or_none()
    print(f"  get_by_date({TARGET_DATE}) resolves to scan_uuid: {latest_scan_uuid}")
    if latest_scan_uuid:
        recs = session.execute(
            select(func.count()).where(Recommendation.scan_uuid == latest_scan_uuid)
        ).scalar()
        status = session.execute(
            select(ScanJob.status).where(ScanJob.scan_uuid == latest_scan_uuid)
        ).scalar()
        print(f"  That job status      : {status}")
        print(f"  Recommendation count : {recs}")
        if status == "running":
            print("  *** BUG: get_by_date is returning a RUNNING job which has 0 recommendations! ***")

print(SEP)
print("STEP 6 — ORPHAN / STALE RUNNING JOBS")
print(SEP)
with get_sync_session() as session:
    running = session.execute(
        select(ScanJob).where(ScanJob.status == "running")
    ).scalars().all()
    print(f"  Total 'running' ScanJob rows in DB: {len(running)}")
    for r in running:
        recs = session.execute(
            select(func.count()).where(Recommendation.scan_uuid == r.scan_uuid)
        ).scalar()
        print(f"    scan_uuid={r.scan_uuid[:12]} date={r.scan_date} started={r.started_at} recs={recs}")

print(SEP)
print("STEP 7 — DATA AVAILABILITY (252 bar check for sample stocks)")
print(SEP)
with get_sync_session() as session:
    stocks = session.execute(select(StockRepository(session).__class__)).scalars().all() if False else []
    from indian_swing.database.repositories.stock_repo import StockRepository
    stocks = list(StockRepository(session).get_active())[:10]
    repo = OHLCVRepository(session)
    for stock in stocks:
        start = TARGET_DATE - timedelta(days=int(252 * 1.8))
        df = repo.to_dataframe(stock.stock_uuid, start, TARGET_DATE, "1d")
        passed = "OK" if len(df) >= 252 else f"FAIL ({len(df)} < 252 required)"
        print(f"  {stock.symbol:20s} bars={len(df):4d}  {passed}")

print(SEP)
print("DIAGNOSIS COMPLETE")
print(SEP)
