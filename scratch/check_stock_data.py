from indian_swing.database.connection import get_sync_session
from sqlalchemy import text
import pandas as pd

def check_stock_data(stock_id):
    with get_sync_session() as session:
        res = session.execute(text(f"SELECT date, open, high, low, close, volume, timeframe, is_adjusted FROM sw_ohlcv WHERE stock_id={stock_id} ORDER BY date DESC LIMIT 20;"))
        rows = res.fetchall()
        print(f"Data for stock {stock_id}:")
        df = pd.DataFrame(rows, columns=["date", "open", "high", "low", "close", "volume", "timeframe", "is_adjusted"])
        print(df.to_string())

if __name__ == "__main__":
    check_stock_data(171)
