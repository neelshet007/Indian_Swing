from indian_swing.database.connection import get_sync_session
from sqlalchemy import text

def search_420_5():
    with get_sync_session() as session:
        res = session.execute(text("SELECT stock_id, date, timeframe, close FROM sw_ohlcv WHERE close = 420.5 OR close BETWEEN 420.4 AND 420.6;"))
        print("Matches for close ~420.5:")
        for r in res.fetchall():
            s_symbol = session.execute(text(f"SELECT symbol FROM sw_stocks WHERE id={r[0]};")).scalar()
            print(f"Stock: {s_symbol} (ID {r[0]}), Date: {r[1]}, Timeframe: {r[2]}, Close: {r[3]}")

if __name__ == "__main__":
    search_420_5()
