from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from indian_swing.database.connection import get_sync_session
from indian_swing.database.models import Stock
from indian_swing.database.repositories.stock_repo import StockRepository
from indian_swing.database.repositories.ohlcv_repo import OHLCVRepository

router = APIRouter()


@router.get("/")
async def list_stocks(
    active_only: bool = Query(True),
    sector: Optional[str] = Query(None),
    limit: int = Query(100, le=2000),
    offset: int = Query(0),
):
    import asyncio
    loop = asyncio.get_event_loop()

    def _fetch():
        with get_sync_session() as session:
            q = select(Stock)
            if active_only:
                q = q.where(Stock.is_active == True)
            if sector:
                q = q.where(Stock.sector == sector)
            q = q.order_by(Stock.symbol).offset(offset).limit(limit)
            stocks = session.execute(q).scalars().all()
            ohlcv_repo = OHLCVRepository(session)
            return [_stock_dict(s, ohlcv_repo.get_latest_close(s.id)) for s in stocks]

    return await loop.run_in_executor(None, _fetch)


@router.get("/{symbol}")
async def get_stock(symbol: str):
    import asyncio
    loop = asyncio.get_event_loop()

    def _fetch():
        with get_sync_session() as session:
            stock = StockRepository(session).get_by_symbol(symbol.upper())
            if not stock:
                return None
            ohlcv_repo = OHLCVRepository(session)
            return _stock_dict(stock, ohlcv_repo.get_latest_close(stock.id))

    stock_data = await loop.run_in_executor(None, _fetch)
    if not stock_data:
        raise HTTPException(status_code=404, detail=f"Stock '{symbol}' not found.")
    return stock_data


@router.get("/{symbol}/ohlcv")
async def get_ohlcv(
    symbol: str,
    timeframe: str = Query("1d"),
    days: int = Query(365, le=3650),
):
    from datetime import date, timedelta
    import asyncio
    loop = asyncio.get_event_loop()

    def _fetch():
        with get_sync_session() as session:
            stock = StockRepository(session).get_by_symbol(symbol.upper())
            if not stock:
                return None, []
            end = date.today()
            start = end - timedelta(days=days)
            rows = OHLCVRepository(session).get_range(stock.id, start, end, timeframe)
            return stock, rows

    stock, rows = await loop.run_in_executor(None, _fetch)
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock '{symbol}' not found.")

    return [
        {"date": str(r.date), "open": r.open, "high": r.high, "low": r.low, "close": r.close, "volume": r.volume}
        for r in rows
    ]


def _stock_dict(s: Stock, current_price: float = None) -> dict:
    return {
        "id": s.id,
        "symbol": s.symbol,
        "name": s.name,
        "sector": s.sector,
        "industry": s.industry,
        "market_cap_category": s.market_cap_category,
        "is_active": s.is_active,
        "current_price": current_price,
    }
