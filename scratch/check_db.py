from indian_swing.database.connection import get_sync_session
from sqlalchemy import text

def check_db_rows():
    with get_sync_session() as session:
        res = session.execute(text("SELECT * FROM sw_signals;"))
        signals = res.fetchall()
        print("Signals:", len(signals))
        for sig in signals:
            print(sig)
            
        res2 = session.execute(text("SELECT * FROM sw_recommendations;"))
        recs = res2.fetchall()
        print("Recommendations:", len(recs))
        for rec in recs:
            print(rec)

if __name__ == "__main__":
    check_db_rows()
