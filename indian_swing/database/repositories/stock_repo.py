from __future__ import annotations

from typing import Sequence

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from indian_swing.config.settings import settings
from indian_swing.database.models import Stock
from indian_swing.database.repositories.base import BaseRepository


class StockRepository(BaseRepository[Stock]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Stock)

    def get_by_symbol(self, symbol: str, exchange: str = "NSE") -> Stock | None:
        return self._session.execute(
            select(Stock).where(
                and_(
                    Stock.environment == settings.app_env.upper(),
                    Stock.exchange == exchange,
                    Stock.symbol == symbol,
                )
            )
        ).scalar_one_or_none()

    def get_active(self) -> Sequence[Stock]:
        return self._session.execute(
            select(Stock)
            .where(
                and_(
                    Stock.environment == settings.app_env.upper(),
                    Stock.is_active == True,
                )
            )
            .order_by(Stock.exchange, Stock.symbol)
        ).scalars().all()

    def upsert(
        self,
        *,
        symbol: str,
        name: str,
        exchange: str = "NSE",
        instrument_type: str = "EQUITY",
        **kwargs,
    ) -> Stock:
        stock = self.get_by_symbol(symbol, exchange=exchange)
        if stock is None:
            stock = Stock(
                environment=settings.app_env.upper(),
                exchange=exchange,
                symbol=symbol,
                name=name,
                instrument_type=instrument_type,
                **kwargs,
            )
            self.add(stock)
            return stock

        stock.name = name
        stock.instrument_type = instrument_type
        for key, value in kwargs.items():
            setattr(stock, key, value)
        self._session.flush()
        return stock

    def bulk_upsert(self, records: list[dict]) -> int:
        all_stocks = self._session.execute(
            select(Stock).where(Stock.environment == settings.app_env.upper())
        ).scalars().all()
        existing_stocks = {(stock.symbol, stock.exchange): stock for stock in all_stocks}

        count = 0
        for record in records:
            payload = dict(record)
            symbol = payload.pop("symbol")
            name = payload.pop("name")
            exchange = payload.pop("exchange", "NSE")
            instrument_type = payload.pop("instrument_type", "EQUITY")

            key = (symbol, exchange)
            if key in existing_stocks:
                stock = existing_stocks[key]
                stock.name = name
                stock.instrument_type = instrument_type
                for k, v in payload.items():
                    setattr(stock, k, v)
            else:
                stock = Stock(
                    environment=settings.app_env.upper(),
                    exchange=exchange,
                    symbol=symbol,
                    name=name,
                    instrument_type=instrument_type,
                    **payload,
                )
                self.add(stock)
                existing_stocks[key] = stock
            count += 1
        self._session.flush()
        return count
