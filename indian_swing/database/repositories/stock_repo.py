from __future__ import annotations

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from indian_swing.database.models import Stock
from indian_swing.database.repositories.base import BaseRepository


class StockRepository(BaseRepository[Stock]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Stock)

    def get_by_symbol(self, symbol: str) -> Stock | None:
        return self._session.execute(
            select(Stock).where(Stock.symbol == symbol)
        ).scalar_one_or_none()

    def get_active(self) -> Sequence[Stock]:
        return self._session.execute(
            select(Stock).where(Stock.is_active == True).order_by(Stock.symbol)
        ).scalars().all()

    def upsert(self, symbol: str, name: str, **kwargs) -> Stock:
        stock = self.get_by_symbol(symbol)
        if stock is None:
            stock = Stock(symbol=symbol, name=name, **kwargs)
            self.add(stock)
        else:
            stock.name = name
            for k, v in kwargs.items():
                setattr(stock, k, v)
            self._session.flush()
        return stock

    def bulk_upsert(self, records: list[dict]) -> int:
        count = 0
        for rec in records:
            rec = dict(rec)
            symbol = rec.pop("symbol")
            name = rec.pop("name")
            self.upsert(symbol, name, **rec)
            count += 1
        return count
