from indian_swing.database.connection import get_sync_session
from sqlalchemy import text

def check_jobs():
    with get_sync_session() as session:
        res = session.execute(text("SELECT id, scan_date, status, total_stocks, stocks_scanned, signals_generated, recommendations_created, started_at, completed_at FROM sw_scan_jobs ORDER BY started_at DESC;"))
        print("Jobs:")
        for r in res.fetchall():
            print(r)

if __name__ == "__main__":
    check_jobs()
