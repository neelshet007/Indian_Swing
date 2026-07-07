from indian_swing.database.connection import get_sync_session
from sqlalchemy import text

def check_stock_details():
    with get_sync_session() as session:
        # Check stock 171
        res = session.execute(text("SELECT * FROM sw_stocks WHERE id=171;"))
        print("Stock 171:", res.fetchone())
        
        # Check if any stock has close price around 420.5 on 2026-07-06
        res2 = session.execute(text("SELECT stock_id, close, volume FROM sw_ohlcv WHERE date='2026-07-06' AND timeframe='1d' AND close BETWEEN 418 AND 422;"))
        matches = res2.fetchall()
        print("Stocks with close ~420.5 on 2026-07-06:")
        for m in matches:
            stock_res = session.execute(text(f"SELECT symbol FROM sw_stocks WHERE id={m[0]};"))
            print(f"Stock ID: {m[0]}, Symbol: {stock_res.scalar()}, Close: {m[1]}, Volume: {m[2]}")

if __name__ == "__main__":
    check_stock_details()
