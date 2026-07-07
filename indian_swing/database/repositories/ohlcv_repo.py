from __future__ import annotations

from datetime import date
from typing import Sequence

import pandas as pd
from sqlalchemy import and_, delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from indian_swing.database.models import OHLCV
from indian_swing.database.repositories.base import BaseRepository


class OHLCVRepository(BaseRepository[OHLCV]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, OHLCV)

    def get_range(self, stock_uuid: str, start: date, end: date, timeframe: str = "1d") -> Sequence[OHLCV]:
        return self._session.execute(
            select(OHLCV)
            .where(
                and_(
                    OHLCV.stock_uuid == stock_uuid,
                    OHLCV.date >= start,
                    OHLCV.date <= end,
                    OHLCV.timeframe == timeframe,
                )
            )
            .order_by(OHLCV.date)
        ).scalars().all()

    def get_coverage(self, stock_uuid: str, timeframe: str = "1d") -> tuple[date | None, date | None, int]:
        row = self._session.execute(
            select(func.min(OHLCV.date), func.max(OHLCV.date), func.count())
            .where(and_(OHLCV.stock_uuid == stock_uuid, OHLCV.timeframe == timeframe))
        ).one()
        return row[0], row[1], int(row[2] or 0)

    def get_latest_date(self, stock_uuid: str, timeframe: str = "1d") -> date | None:
        return self._session.execute(
            select(OHLCV.date)
            .where(and_(OHLCV.stock_uuid == stock_uuid, OHLCV.timeframe == timeframe))
            .order_by(OHLCV.date.desc())
            .limit(1)
        ).scalar_one_or_none()

    def get_latest_close(self, stock_uuid: str, timeframe: str = "1d") -> float | None:
        return self._session.execute(
            select(OHLCV.close)
            .where(and_(OHLCV.stock_uuid == stock_uuid, OHLCV.timeframe == timeframe))
            .order_by(OHLCV.date.desc())
            .limit(1)
        ).scalar_one_or_none()

    def to_dataframe(self, stock_uuid: str, start: date, end: date, timeframe: str = "1d") -> pd.DataFrame:
        rows = self.get_range(stock_uuid, start, end, timeframe)
        if not rows:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        frame = pd.DataFrame(
            {
                "date": row.date,
                "open": row.open,
                "high": row.high,
                "low": row.low,
                "close": row.close,
                "volume": row.volume,
            }
            for row in rows
        )
        frame["date"] = pd.to_datetime(frame["date"])
        frame = frame.sort_values("date").set_index("date")
        frame.index.name = "date"
        return frame

    def bulk_insert_ignore(self, records: list[dict]) -> int:
        if not records:
            return 0

        dialect = self._session.bind.dialect.name
        if dialect == "postgresql":
            stmt = pg_insert(OHLCV).values(records)
            stmt = stmt.on_conflict_do_nothing(index_elements=["stock_uuid", "date", "timeframe"])
            result = self._session.execute(stmt)
            self._session.flush()
            return result.rowcount or 0

        existing = set(
            self._session.execute(
                select(OHLCV.stock_uuid, OHLCV.date, OHLCV.timeframe).where(
                    and_(
                        OHLCV.stock_uuid.in_({record["stock_uuid"] for record in records}),
                        OHLCV.timeframe.in_({record["timeframe"] for record in records}),
                    )
                )
            ).all()
        )
        inserted = 0
        for record in records:
            key = (record["stock_uuid"], record["date"], record["timeframe"])
            if key in existing:
                continue
            self._session.add(OHLCV(**record))
            existing.add(key)
            inserted += 1
        self._session.flush()
        return inserted

    def replace_timeframe(self, stock_uuid: str, timeframe: str, records: list[dict]) -> int:
        self._session.execute(
            delete(OHLCV).where(and_(OHLCV.stock_uuid == stock_uuid, OHLCV.timeframe == timeframe))
        )
        count = self.bulk_insert_ignore(records)
        self._session.flush()
        return count
