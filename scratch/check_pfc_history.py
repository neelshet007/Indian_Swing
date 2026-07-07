from indian_swing.database.connection import get_sync_session
from sqlalchemy import text

def check_pfc_history():
    with get_sync_session() as session:
        res = session.execute(text("SELECT date, open, high, low, close, volume FROM sw_ohlcv WHERE stock_id=379 AND date BETWEEN '2026-07-01' AND '2026-07-07' AND timeframe='1d';"))
        print("PFC History:")
        for r in res.fetchall():
            print(r)

if __name__ == "__main__":
    check_pfc_history()
