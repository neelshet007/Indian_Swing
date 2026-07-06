from typing import List, Optional
from datetime import date
from sqlalchemy import select, and_, func
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from indian_swing.database.models import Stock, OHLCV

class MarketDataRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_stock_by_symbol(self, symbol: str) -> Optional[Stock]:
        stmt = select(Stock).where(Stock.symbol == symbol)
        return self.session.execute(stmt).scalar_one_or_none()
        
    def get_active_stocks(self) -> List[Stock]:
        stmt = select(Stock).where(Stock.is_active == True)
        return list(self.session.execute(stmt).scalars().all())

    def get_latest_ohlcv_date(self, stock_id: int, timeframe: str = "1d") -> Optional[date]:
        stmt = select(func.max(OHLCV.date)).where(
            and_(OHLCV.stock_id == stock_id, OHLCV.timeframe == timeframe)
        )
        return self.session.execute(stmt).scalar()
        
    def get_earliest_ohlcv_date(self, stock_id: int, timeframe: str = "1d") -> Optional[date]:
        stmt = select(func.min(OHLCV.date)).where(
            and_(OHLCV.stock_id == stock_id, OHLCV.timeframe == timeframe)
        )
        return self.session.execute(stmt).scalar()

    def get_ohlcv_data(self, stock_id: int, timeframe: str = "1d") -> List[OHLCV]:
        stmt = select(OHLCV).where(
            and_(OHLCV.stock_id == stock_id, OHLCV.timeframe == timeframe)
        ).order_by(OHLCV.date.asc())
        return list(self.session.execute(stmt).scalars().all())

    def bulk_insert_ohlcv(self, records: List[dict]):
        if not records:
            return
            
        # Using SQLite ON CONFLICT DO NOTHING behavior
        stmt = sqlite_insert(OHLCV).values(records)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["stock_id", "date", "timeframe"]
        )
        self.session.execute(stmt)
        self.session.commit()
