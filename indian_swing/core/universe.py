"""
Stock universe management — sync DB version.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from indian_swing.config.settings import settings
from indian_swing.core.logging_setup import get_logger
from indian_swing.database.connection import get_sync_session
from indian_swing.database.models import Stock
from indian_swing.database.repositories.stock_repo import StockRepository

logger = get_logger(__name__)

_BUILTIN_NIFTY50 = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR", "ICICIBANK", "KOTAKBANK",
    "BHARTIARTL", "ITC", "AXISBANK", "LT", "SBILIFE", "ASIANPAINT", "HCLTECH",
    "BAJFINANCE", "MARUTI", "ULTRACEMCO", "TITAN", "WIPRO", "NESTLEIND",
    "TECHM", "SUNPHARMA", "INDUSINDBK", "POWERGRID", "NTPC", "ONGC", "TATAMOTORS",
    "BAJAJFINSV", "JSWSTEEL", "HDFCLIFE", "GRASIM", "CIPLA", "TATASTEEL",
    "ADANIENT", "ADANIPORTS", "DIVISLAB", "BPCL", "COALINDIA", "EICHERMOT",
    "HEROMOTOCO", "APOLLOHOSP", "BRITANNIA", "DRREDDY", "SBIN", "TATACONSUM",
    "UPL", "HINDALCO", "SHREECEM", "MM", "BAJAJ-AUTO",
]


@dataclass
class UniverseStock:
    symbol: str
    name: str
    sector: str = ""
    industry: str = ""
    market_cap_category: str = "large"


class UniverseManager:
    async def load(self) -> list[UniverseStock]:
        csv_path = settings.universe_file
        if csv_path.exists():
            return self._load_from_csv(csv_path)
        logger.warning("universe.csv_not_found", path=str(csv_path), fallback="builtin_nifty50")
        return self._builtin()

    async def sync_to_db(self) -> int:
        stocks = await self.load()
        import asyncio
        loop = asyncio.get_event_loop()

        def _upsert():
            with get_sync_session() as session:
                repo = StockRepository(session)
                records = [
                    {
                        "symbol": f"{s.symbol}.NS",
                        "name": s.name,
                        "sector": s.sector or None,
                        "industry": s.industry or None,
                        "market_cap_category": s.market_cap_category,
                    }
                    for s in stocks
                ]
                return repo.bulk_upsert(records)

        count = await loop.run_in_executor(None, _upsert)
        logger.info("universe.synced", count=count)
        return count

    async def get_active_symbols(self) -> list[str]:
        import asyncio
        loop = asyncio.get_event_loop()

        def _fetch():
            with get_sync_session() as session:
                repo = StockRepository(session)
                return [s.symbol for s in repo.get_active()]

        return await loop.run_in_executor(None, _fetch)

    def _load_from_csv(self, path: Path) -> list[UniverseStock]:
        stocks: list[UniverseStock] = []
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                symbol = row.get("symbol") or row.get("Symbol")
                if not symbol:
                    continue
                symbol = symbol.strip().upper()
                name = row.get("name") or row.get("Company Name") or symbol
                sector = row.get("sector") or ""
                industry = row.get("industry") or row.get("Industry") or ""
                stocks.append(UniverseStock(
                    symbol=symbol,
                    name=name,
                    sector=sector,
                    industry=industry,
                    market_cap_category=row.get("market_cap_category", "large"),
                ))
        logger.info("universe.loaded_csv", path=str(path), count=len(stocks))
        return stocks

    def _builtin(self) -> list[UniverseStock]:
        return [UniverseStock(symbol=s, name=s) for s in _BUILTIN_NIFTY50]
