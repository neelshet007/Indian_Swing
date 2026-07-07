from indian_swing.database.connection import get_sync_session
from sqlalchemy import text

def find_420():
    with get_sync_session() as session:
        # Search all records in sw_ohlcv on 2026-07-06 for close close to 420.5
        res = session.execute(text("SELECT stock_id, close, volume FROM sw_ohlcv WHERE date='2026-07-06' AND timeframe='1d' AND close BETWEEN 420 AND 421;"))
        print("Close between 420 and 421 on 2026-07-06:")
        for r in res.fetchall():
            s_name = session.execute(text(f"SELECT symbol FROM sw_stocks WHERE id={r[0]};")).scalar()
            print(f"Stock: {s_name} (ID {r[0]}), Close: {r[1]}, Vol: {r[2]}")

if __name__ == "__main__":
    find_420()
