from typing import List, Optional
from datetime import date
from sqlalchemy import select, and_, func

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
            
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Database insert started for {len(records)} OHLCV records")
        
        stock_ids = list(set(r["stock_id"] for r in records))
        timeframes = list(set(r["timeframe"] for r in records))
        dates = list(set(r["date"] for r in records))
        
        stmt = select(OHLCV.stock_id, OHLCV.date, OHLCV.timeframe).where(
            and_(
                OHLCV.stock_id.in_(stock_ids),
                OHLCV.timeframe.in_(timeframes),
                OHLCV.date.in_(dates)
            )
        )
        
        existing_tuples = set()
        for row in self.session.execute(stmt).fetchall():
            existing_tuples.add((row[0], str(row[1])[:10], row[2]))
        
        inserted_count = 0
        skipped_count = 0
        
        for record in records:
            try:
                # Normalize record date for comparison
                d_str = str(record["date"])
                if " " in d_str: d_str = d_str.split(" ")[0]
                elif "T" in d_str: d_str = d_str.split("T")[0]
                
                key = (record["stock_id"], d_str[:10], record["timeframe"])
                if key in existing_tuples:
                    skipped_count += 1
                else:
                    new_ohlcv = OHLCV(**record)
                    self.session.add(new_ohlcv)
                    inserted_count += 1
            except Exception as e:
                logger.error(f"Failed to process OHLCV record for stock_id {record.get('stock_id')}: {e}")
                
        self.session.commit()
        logger.info(f"Transaction committed: Inserted {inserted_count}, Skipped (duplicate) {skipped_count}")
