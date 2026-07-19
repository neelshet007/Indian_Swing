"""
Upstox data provider implementation.
Handles instrument master mapping, rate limiting, and V3 historical candle retrieval.
"""
from __future__ import annotations

import asyncio
import gzip
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import httpx
import pandas as pd
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from indian_swing.config.settings import settings
from indian_swing.core.exceptions import DataProviderError
from indian_swing.core.logging_setup import get_logger
from indian_swing.data.providers.base import DataProvider

logger = get_logger(__name__)


class UpstoxProvider(DataProvider):
    """
    Upstox-backed provider.
    Downloads instrument master data once a day to resolve trading symbols to instrument keys.
    """

    def __init__(self) -> None:
        self.access_token = settings.upstox_access_token
        self.cache_dir = settings.cache_dir / "upstox"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._instrument_map: dict[str, str] = {}
        self._metadata_map: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    @property
    def name(self) -> str:
        return "upstox"

    def _get_local_path(self, exchange: str) -> Path:
        return self.cache_dir / f"{exchange}_instruments.json.gz"

    async def _ensure_instrument_map(self) -> None:
        if self._instrument_map:
            return

        async with self._lock:
            # Double-check pattern
            if self._instrument_map:
                return

            for exchange in ["NSE", "global"]:
                local_path = self._get_local_path(exchange)
                should_download = True

                if local_path.exists():
                    mtime = date.fromtimestamp(local_path.stat().st_mtime)
                    if mtime == date.today():
                        should_download = False

                if should_download:
                    url = f"https://assets.upstox.com/market-quote/instruments/exchange/{exchange}.json.gz"
                    try:
                        logger.info("upstox.download_instrument_master", exchange=exchange, url=url)
                        async with httpx.AsyncClient() as client:
                            response = await client.get(url, timeout=30.0)
                            response.raise_for_status()
                            local_path.write_bytes(response.content)
                    except Exception as e:
                        if not local_path.exists():
                            raise DataProviderError(
                                f"Failed to download instrument master for {exchange}: {e}"
                            ) from e
                        logger.warning(
                            "upstox.instrument_download_failed_using_cache",
                            exchange=exchange,
                            error=str(e),
                        )

                try:
                    logger.info("upstox.parse_instrument_master", exchange=exchange, path=str(local_path))
                    # Read the gzip compressed JSON
                    with gzip.open(local_path, "rt", encoding="utf-8") as f:
                        data = json.load(f)
                        for item in data:
                            trading_symbol = item.get("trading_symbol")
                            instrument_key = item.get("instrument_key")
                            segment = item.get("segment")
                            isin = item.get("isin")
                            name = item.get("name") or trading_symbol

                            if not trading_symbol or not instrument_key:
                                continue

                            sym = trading_symbol.strip().upper()

                            # Map NSE/BSE Equities and Indexes
                            if segment in ("NSE_EQ", "BSE_EQ"):
                                self._instrument_map[sym] = instrument_key
                                self._metadata_map[sym] = {
                                    "name": name,
                                    "sector": item.get("sector_name"),
                                    "industry": item.get("industry_name"),
                                    "market_cap": item.get("market_cap"),
                                    "isin": isin,
                                }
                            elif segment == "NSE_INDEX":
                                self._instrument_map[sym] = instrument_key
                                self._metadata_map[sym] = {
                                    "name": name,
                                    "instrument_type": "INDEX",
                                }
                except Exception as e:
                    raise DataProviderError(f"Failed to parse instrument master for {exchange}: {e}") from e

            # Add fallback support for standard indexes & format cleaning
            nifty_key = self._instrument_map.get("NIFTY 50") or "NSE_INDEX|Nifty 50"
            self._instrument_map["^NSEI"] = nifty_key
            self._instrument_map["NIFTY 50"] = nifty_key

    @retry(
        retry=retry_if_exception_type((Exception,)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def fetch_ohlcv(
        self,
        symbol: str,
        start: date,
        end: date,
        timeframe: str = "1d",
    ) -> pd.DataFrame:
        if not self.access_token:
            raise DataProviderError("UPSTOX_ACCESS_TOKEN is not configured")

        await self._ensure_instrument_map()

        sym_upper = symbol.strip().upper()
        if sym_upper.endswith(".NS"):
            sym_upper = sym_upper[:-3]

        instrument_key = self._instrument_map.get(sym_upper)
        if not instrument_key:
            raise DataProviderError(f"No instrument key found for symbol: {symbol}")

        # Map timeframe to Upstox API V3 parameters
        # V3 unit options: minutes, hours, days, weeks, months
        unit = "days"
        interval = "1"
        if timeframe in ("1wk", "week"):
            unit = "weeks"
        elif timeframe in ("1mo", "month"):
            unit = "months"

        to_date_str = end.isoformat()
        from_date_str = start.isoformat()

        # Upstox V3 historical API:
        # GET https://api.upstox.com/v3/historical-candle/{instrument_key}/{unit}/{interval}/{to_date}/{from_date}
        url = f"https://api.upstox.com/v3/historical-candle/{instrument_key}/{unit}/{interval}/{to_date_str}/{from_date_str}"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=20.0)
                if response.status_code == 429:
                    logger.warning("upstox.rate_limited", symbol=symbol)
                    raise Exception("Upstox rate limit hit")
                response.raise_for_status()
                res_data = response.json()
        except Exception as e:
            logger.warning("upstox.fetch_failed", symbol=symbol, error=str(e))
            raise DataProviderError(f"Upstox fetch failed for {symbol}: {e}") from e

        if res_data.get("status") != "success" or "data" not in res_data:
            raise DataProviderError(f"Invalid response from Upstox for {symbol}: {res_data}")

        candles = res_data["data"].get("candles", [])
        if not candles:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        # Upstox returns candles newest first (descending). Reverse to oldest first (ascending).
        candles.reverse()

        # Schema: [Timestamp, Open, High, Low, Close, Volume, OpenInterest]
        df = pd.DataFrame(
            candles,
            columns=["date", "open", "high", "low", "close", "volume", "open_interest"],
        )

        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)

        required = ["open", "high", "low", "close", "volume"]
        df = df[required]

        for col in ["open", "high", "low", "close"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0).astype(int)

        return df.sort_index()

    async def fetch_bulk_ohlcv(
        self,
        symbols: list[str],
        start: date | dict[str, date],
        end: date,
        timeframe: str = "1d",
    ) -> dict[str, pd.DataFrame]:
        # Batch fetching via gathering concurrent tasks with semaphore throttling.
        # We use a semaphore of 10 and stagger task starts with a 0.15s sleep to stay
        # safely within the 500 requests per minute Upstox API limit.
        sem = asyncio.Semaphore(10)

        async def fetch_one(sym: str, idx: int) -> tuple[str, pd.DataFrame]:
            await asyncio.sleep(idx * 0.15)
            async with sem:
                try:
                    sym_start = start.get(sym, start) if isinstance(start, dict) else start
                    df = await self.fetch_ohlcv(sym, sym_start, end, timeframe)
                    return sym, df
                except Exception as e:
                    logger.warning("upstox.bulk_symbol_failed", symbol=sym, error=str(e))
                    return sym, pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        tasks = [fetch_one(s, i) for i, s in enumerate(symbols)]
        results = await asyncio.gather(*tasks)
        return dict(results)

    async def fetch_metadata(self, symbol: str) -> dict[str, Any]:
        await self._ensure_instrument_map()
        sym_upper = symbol.strip().upper()
        if sym_upper.endswith(".NS"):
            sym_upper = sym_upper[:-3]

        metadata = self._metadata_map.get(sym_upper)
        if metadata:
            return {
                "name": metadata.get("name") or symbol,
                "sector": metadata.get("sector"),
                "industry": metadata.get("industry"),
                "market_cap": metadata.get("market_cap"),
                "isin": metadata.get("isin"),
            }
        return {"name": symbol}

    async def health_check(self) -> bool:
        try:
            df = await self.fetch_ohlcv(
                "RELIANCE",
                date.today() - timedelta(days=5),
                date.today(),
            )
            return not df.empty
        except Exception:
            return False
