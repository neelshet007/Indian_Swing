from __future__ import annotations

from datetime import date
from typing import Sequence

import pandas as pd
from sqlalchemy import and_, delete, select, insert
from sqlalchemy.orm import Session

from indian_swing.database.models import OHLCV
from indian_swing.database.repositories.base import BaseRepository


class OHLCVRepository(BaseRepository[OHLCV]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, OHLCV)

    def get_range(
        self,
        stock_id: int,
        start: date,
        end: date,
        timeframe: str = "1d",
    ) -> Sequence[OHLCV]:
        return self._session.execute(
            select(OHLCV)
            .where(
                and_(
                    OHLCV.stock_id == stock_id,
                    OHLCV.date >= start,
                    OHLCV.date <= end,
                    OHLCV.timeframe == timeframe,
                )
            )
            .order_by(OHLCV.date)
        ).scalars().all()

    def get_latest_date(self, stock_id: int, timeframe: str = "1d") -> date | None:
        result = self._session.execute(
            select(OHLCV.date)
            .where(and_(OHLCV.stock_id == stock_id, OHLCV.timeframe == timeframe))
            .order_by(OHLCV.date.desc())
            .limit(1)
        ).scalar_one_or_none()
        return result

    def to_dataframe(
        self,
        stock_id: int,
        start: date,
        end: date,
        timeframe: str = "1d",
    ) -> pd.DataFrame:
        rows = self.get_range(stock_id, start, end, timeframe)
        if not rows:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        data = [
            {
                "date": r.date,
                "open": r.open,
                "high": r.high,
                "low": r.low,
                "close": r.close,
                "volume": r.volume,
            }
            for r in rows
        ]
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        return df

    def bulk_insert_ignore(self, records: list[dict]) -> int:
        if not records:
            return 0
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert
        stmt = sqlite_insert(OHLCV).values(records).on_conflict_do_nothing(
            index_elements=["stock_id", "date", "timeframe"]
        )
        result = self._session.execute(stmt)
        self._session.flush()
        return result.rowcount or 0
