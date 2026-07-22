import sys
sys.path.insert(0, ".")
from indian_swing.database.connection import get_sync_session
from indian_swing.database.models import Stock, OHLCV
from sqlalchemy import func

with get_sync_session() as s:
    stock = s.query(Stock).filter(Stock.symbol == "AARON").first()
    if stock:
        c_1d = s.query(func.count(OHLCV.id)).filter(OHLCV.stock_uuid == stock.stock_uuid, OHLCV.timeframe == "1d").scalar()
        min_date = s.query(func.min(OHLCV.date)).filter(OHLCV.stock_uuid == stock.stock_uuid, OHLCV.timeframe == "1d").scalar()
        max_date = s.query(func.max(OHLCV.date)).filter(OHLCV.stock_uuid == stock.stock_uuid, OHLCV.timeframe == "1d").scalar()
        print(f"Stock: {stock.symbol}")
        print(f"  Count: {c_1d}")
        print(f"  Min Date: {min_date}")
        print(f"  Max Date: {max_date}")
    else:
        print("Stock AARON not found.")
