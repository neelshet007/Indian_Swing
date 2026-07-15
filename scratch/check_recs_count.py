import asyncio
from datetime import date
from sqlalchemy import func
from indian_swing.database.connection import get_sync_session
from indian_swing.database.models import Recommendation, Signal, ScanJob

async def check():
    with get_sync_session() as session:
        today_recs = session.query(Recommendation).filter(Recommendation.scan_date == date(2026, 7, 15)).all()
        today_signals = session.query(Signal).filter(Signal.signal_date == date(2026, 7, 15)).all()
        today_jobs = session.query(ScanJob).filter(ScanJob.scan_date == date(2026, 7, 15)).all()
        
        print("=== Today's Scan Status (2026-07-15) ===")
        print(f"Jobs: {len(today_jobs)}")
        for j in today_jobs:
            print(f"- Job UUID={j.scan_uuid}, status={j.status}, scanned={j.stocks_scanned}/{j.total_stocks}, signals={j.signals_generated}, recs={j.recommendations_created}, error={j.error}")
            
        print(f"\nSignals: {len(today_signals)}")
        for s in today_signals[:10]:
            print(f"- Symbol={s.stock_uuid}, strategy={s.strategy_name}, entry={s.entry_price}, stop={s.stop_loss}")
            
        print(f"\nRecommendations: {len(today_recs)}")
        for r in today_recs[:10]:
            print(f"- Symbol={r.stock_uuid}, strategy={r.strategy_name}, rank={r.rank}, entry={r.entry_price}, stop={r.stop_loss}, explanation={r.explanation}")

if __name__ == "__main__":
    asyncio.run(check())
