from indian_swing.database.connection import get_sync_session
from sqlalchemy import text

def find_exact_close():
    with get_sync_session() as session:
        res = session.execute(text("SELECT stock_id, close FROM sw_ohlcv WHERE date='2026-07-06' AND timeframe='1d' AND close=420.5;"))
        print("Exact matches for 420.5:", res.fetchall())
        
        # Or look for stock_id = 171 on 2026-07-06 across ALL timeframes
        res2 = session.execute(text("SELECT date, open, high, low, close, timeframe FROM sw_ohlcv WHERE stock_id=171 AND date='2026-07-06';"))
        print("Stock 171 on 2026-07-06:")
        for r in res2.fetchall():
            print(r)

if __name__ == "__main__":
    find_exact_close()
