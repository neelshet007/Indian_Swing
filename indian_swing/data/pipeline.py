from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Callable, Any

import pandas as pd

from indian_swing.config.settings import settings
from indian_swing.core.exceptions import DataValidationError
from indian_swing.core.logging_setup import get_logger
from indian_swing.data.cleaner import OHLCVCleaner, OHLCVResampler
from indian_swing.data.provider_factory import get_provider
from indian_swing.data.validator import OHLCVValidator
from indian_swing.database.connection import get_sync_session
from indian_swing.database.repositories.ohlcv_repo import OHLCVRepository
from indian_swing.database.repositories.stock_repo import StockRepository

logger = get_logger(__name__)


@dataclass
class PipelineResult:
    symbol: str
    success: bool
    records_added: int = 0
    error: str | None = None


@dataclass
class PipelineSummary:
    total: int = 0
    succeeded: int = 0
    failed: int = 0
    records_added: int = 0
    errors: list[str] = field(default_factory=list)


class DataPipeline:
    def __init__(self) -> None:
        self._provider = get_provider()
        self._validator = OHLCVValidator()
        self._cleaner = OHLCVCleaner()
        self._resampler = OHLCVResampler()
        self._bulk_cache: dict[str, pd.DataFrame] = {}

    async def run_incremental(
        self,
        symbols: list[str],
        required_daily_bars: int,
        end: date | None = None,
        force_refresh: bool = False,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> PipelineSummary:
        end = end or date.today()
        start = end - timedelta(days=int(required_daily_bars * 2.2))
        return await self.run_full(
            symbols=symbols,
            start=start,
            end=end,
            force_refresh=force_refresh,
            required_daily_bars=required_daily_bars,
            progress_callback=progress_callback,
        )

    async def run_full(
        self,
        symbols: list[str],
        start: date,
        end: date,
        force_refresh: bool = False,
        required_daily_bars: int | None = None,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> PipelineSummary:
        def _get_coverages():
            with get_sync_session() as session:
                from sqlalchemy import select, func
                from indian_swing.database.models import Stock, OHLCV
                rows = session.execute(
                    select(
                        Stock.symbol,
                        func.min(OHLCV.date),
                        func.max(OHLCV.date),
                        func.count(OHLCV.id)
                    )
                    .join(OHLCV, OHLCV.stock_uuid == Stock.stock_uuid)
                    .where(OHLCV.timeframe == "1d")
                    .group_by(Stock.symbol)
                ).all()
                return {row[0]: (row[1], row[2], row[3]) for row in rows}

        symbols_to_fetch = []
        fetch_start = start
        fetch_start_map = {}

        if not force_refresh:
            loop = asyncio.get_running_loop()
            coverages = await loop.run_in_executor(None, _get_coverages)
            
            for sym in symbols:
                earliest, latest, count = coverages.get(sym, (None, None, 0))
                
                if earliest is None or latest is None or count == 0:
                    symbols_to_fetch.append(sym)
                    fetch_start_map[sym] = start
                else:
                    if latest < end:
                        symbols_to_fetch.append(sym)
                        fetch_start_map[sym] = latest + timedelta(days=1)
            
            if fetch_start_map:
                fetch_start = fetch_start_map
        else:
            symbols_to_fetch = symbols

        if not symbols_to_fetch:
            # logger.info("pipeline.bulk_fetch_skip", count=len(symbols))
            self._bulk_cache = {}
        else:
            try:
                log_start = min(fetch_start.values()) if isinstance(fetch_start, dict) else fetch_start
                logger.info("pipeline.bulk_fetch_start", count=len(symbols_to_fetch), start=str(log_start), end=str(end))
                self._bulk_cache = await self._provider.fetch_bulk_ohlcv(symbols_to_fetch, fetch_start, end)
                # logger.info("pipeline.bulk_fetch_complete", count=len(self._bulk_cache))
            except Exception as e:
                logger.warning("pipeline.bulk_fetch_failed", error=str(e))
                self._bulk_cache = {}

        summary = PipelineSummary(total=len(symbols))
        sem = asyncio.Semaphore(8)  # Limit concurrent connection usage

        state = {
            "completed": 0,
            "total": len(symbols),
            "start_time": asyncio.get_running_loop().time(),
        }

        async def sem_process(sym: str) -> PipelineResult:
            async with sem:
                res = await self._process_symbol(
                    sym, start, end, force_refresh, required_daily_bars, progress_callback, state
                )
                state["completed"] += 1
                return res

        tasks = [sem_process(s) for s in symbols]
        results = await asyncio.gather(*tasks)

        for symbol, result in zip(symbols, results):
            if result.success:
                summary.succeeded += 1
                summary.records_added += result.records_added
            else:
                summary.failed += 1
                if result.error:
                    summary.errors.append(f"{symbol}: {result.error}")
                    logger.error("pipeline.symbol_failed", symbol=symbol, error=result.error)
        logger.info("pipeline.complete", succeeded=summary.succeeded, failed=summary.failed, records=summary.records_added)
        self._bulk_cache = {}
        return summary

    async def _process_symbol(
        self,
        symbol: str,
        required_start: date,
        end: date,
        force_refresh: bool,
        required_daily_bars: int | None,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
        state: dict[str, Any] | None = None,
    ) -> PipelineResult:
        loop = asyncio.get_running_loop()

        async def _run() -> PipelineResult:
            def _coverage() -> tuple[str | None, date | None, date | None, int]:
                with get_sync_session() as session:
                    stock = StockRepository(session).get_by_symbol(symbol) or StockRepository(session).get_by_symbol(
                        symbol,
                        exchange=settings.scanner.benchmark_exchange,
                    )
                    if stock is None:
                        return None, None, None, 0
                    start_date, latest_date, count = OHLCVRepository(session).get_coverage(stock.stock_uuid, "1d")
                    return stock.stock_uuid, start_date, latest_date, count

            stock_uuid, earliest, latest, count = await loop.run_in_executor(None, _coverage)
            if stock_uuid is None:
                return PipelineResult(symbol=symbol, success=False, error="Stock not found in universe")

            fetch_ranges: list[tuple[date, date]] = []
            req_bars = required_daily_bars or settings.pipeline.min_trading_days
            
            db_status = "Checking..."
            action = "Checking..."
            
            if force_refresh:
                fetch_ranges.append((required_start, end))
                db_status = "Forced Refresh"
                action = "Downloading Full Range..."
            else:
                if earliest is None or latest is None or count == 0:
                    fetch_ranges.append((required_start, end))
                    db_status = "Empty"
                    action = "Downloading Full Range..."
                else:
                    # Calculate missing left range
                    if required_start < earliest:
                        left_end = earliest - timedelta(days=1)
                        if required_start <= left_end:
                            fetch_ranges.append((required_start, left_end))
                    
                    # Calculate missing right range
                    if end > latest:
                        right_start = latest + timedelta(days=1)
                        if right_start <= end:
                            fetch_ranges.append((right_start, end))
                            
                    if fetch_ranges:
                        db_status = "Partial"
                        avail_str = f"{earliest} → {latest}"
                        miss_str = ", ".join(f"{fs} → {fe}" for fs, fe in fetch_ranges)
                        action = f"Downloading Missing Candles ({miss_str})..."
                    else:
                        db_status = "Complete"
                        action = "Loading from Database"

            # Progress Reporting calculation
            if state and progress_callback:
                elapsed = loop.time() - state["start_time"]
                completed = state["completed"]
                if completed > 0:
                    speed = completed / elapsed
                    remaining = state["total"] - completed
                    eta_mins = max(0, int(remaining / speed / 60))
                    eta_str = f"{eta_mins} Minutes"
                else:
                    eta_str = "Calculating..."
                
                pct = completed / state["total"] if state["total"] > 0 else 0
                filled = int(20 * pct)
                progress_bar = "█" * filled + "░" * (20 - filled)
                
                progress_data = {
                    "completed_days": completed,
                    "total_days": state["total"],
                    "current_symbol": symbol,
                    "current_stage": f"Preparing {symbol} ({db_status})",
                    "eta_minutes": eta_str if completed > 0 else 0,
                    "db_status": db_status,
                    "action": action,
                    "progress_bar": progress_bar
                }
                progress_callback(progress_data)
                
                # Callback runs for API/UI progress, but we skip direct stdout prints to save memory and console clutter
                pass

            frames: list[pd.DataFrame] = []
            rows_downloaded = 0
            for fetch_start, fetch_end in fetch_ranges:
                if symbol in self._bulk_cache:
                    cached_df = self._bulk_cache[symbol]
                    if not cached_df.empty:
                        mask = (cached_df.index.date >= fetch_start) & (cached_df.index.date <= fetch_end)
                        fetched = cached_df.loc[mask]
                        if not fetched.empty:
                            frames.append(fetched)
                            rows_downloaded += len(fetched)
                    continue

                # logger.info("pipeline.fetch_missing", symbol=symbol, start=str(fetch_start), end=str(fetch_end))
                fetched = await self._provider.fetch_ohlcv(symbol, fetch_start, fetch_end)
                if fetched is not None and not fetched.empty:
                    frames.append(fetched)
                    rows_downloaded += len(fetched)

            if not fetch_ranges and count > 0:
                return PipelineResult(symbol=symbol, success=True, records_added=0)
                
            if not frames:
                if count > 0:
                    return PipelineResult(symbol=symbol, success=True, records_added=0)
                return PipelineResult(symbol=symbol, success=False, error="No data returned")

            merged = pd.concat(frames).sort_index()
            if (force_refresh or count < req_bars) and len(merged) < req_bars:
                missing = req_bars - len(merged)
                extra_days = int(missing * 1.7) + 14
                extended_start = required_start - timedelta(days=extra_days)
                logger.info("pipeline.extend_fetch", symbol=symbol, missing=missing, start=str(extended_start), end=str(required_start - timedelta(days=1)))
                try:
                    fetched_extra = await self._provider.fetch_ohlcv(symbol, extended_start, required_start - timedelta(days=1))
                    if fetched_extra is not None and not fetched_extra.empty:
                        frames.append(fetched_extra)
                        merged = pd.concat(frames).sort_index()
                except Exception as e:
                    logger.warning("pipeline.extend_fetch_failed", symbol=symbol, error=str(e))
            try:
                validated = self._validator.validate(merged, symbol, enforce_min=False)
            except DataValidationError as exc:
                return PipelineResult(symbol=symbol, success=False, error=str(exc))
            cleaned = self._cleaner.clean(validated)

            if not cleaned.index.is_monotonic_increasing:
                raise DataValidationError(f"[{symbol}] Data is not in correct chronological order.")

            def _store() -> int:
                try:
                    with get_sync_session() as session:
                        stock = StockRepository(session).get_by_symbol(symbol) or StockRepository(session).get_by_symbol(
                            symbol,
                            exchange=settings.scanner.benchmark_exchange,
                        )
                        if stock is None:
                            raise ValueError(f"Stock missing during store for {symbol}")
                        repo = OHLCVRepository(session)
                        daily_records = self._df_to_records(cleaned, stock.stock_uuid, "1d")
                        inserted = repo.bulk_insert_ignore(daily_records)

                        provider_name = self._provider.name
                        if provider_name.lower() != "upstox":
                            logger.error(f"[PROVIDER WARNING] Non-Upstox provider detected: {provider_name}")
                            raise ValueError(f"Non-Upstox provider detected: {provider_name}")

                        # logger.info(
                        #     f"\n[UPSTOX VERIFIED]\n"
                        #     f"{symbol}\n"
                        #     f"Provider: Upstox\n"
                        #     f"Rows Downloaded: {rows_downloaded}\n"
                        #     f"Rows Inserted: {inserted}\n"
                        #     f"Status: SUCCESS"
                        # )

                        if force_refresh:
                            daily_full = cleaned
                            coverage_start = required_start
                        else:
                            db_earliest = repo.get_coverage(stock.stock_uuid, "1d")[0]
                            coverage_start = db_earliest or required_start
                            daily_full = repo.to_dataframe(stock.stock_uuid, coverage_start, end, "1d")

                        weekly = self._resampler.resample(daily_full, "1wk")
                        monthly = self._resampler.resample(daily_full, "1mo")
                        repo.replace_timeframe(stock.stock_uuid, "1wk", self._df_to_records(weekly, stock.stock_uuid, "1wk"))
                        repo.replace_timeframe(stock.stock_uuid, "1mo", self._df_to_records(monthly, stock.stock_uuid, "1mo"))

                        # logger.info("pipeline.store_debug", symbol=symbol, uuid=stock.stock_uuid, coverage_start=str(coverage_start), len_daily_full=len(daily_full))
                        if required_daily_bars and len(daily_full) < required_daily_bars:
                            raise DataValidationError(
                                f"[{symbol}] Only {len(daily_full)} bars after load; require {required_daily_bars}"
                            )
                        return inserted
                except Exception as e:
                    # logger.error("pipeline.store_exception", symbol=symbol, error=str(e), type=type(e).__name__)
                    raise

            try:
                inserted = await loop.run_in_executor(None, _store)
                return PipelineResult(symbol=symbol, success=True, records_added=inserted)
            except Exception as exc:
                return PipelineResult(symbol=symbol, success=False, error=str(exc))

        result = await _run()
        if not result.success:
            err = result.error or ""
            is_permanent = (
                "No daily history available" in err or
                "No data returned" in err or
                "No instrument key found" in err or
                "Stock not found in universe" in err
            )
            if is_permanent:
                logger.warning("pipeline.deactivating_invalid_stock", symbol=symbol, reason=err)
                def _deactivate():
                    with get_sync_session() as session:
                        stock = StockRepository(session).get_by_symbol(symbol) or StockRepository(session).get_by_symbol(
                            symbol,
                            exchange=settings.scanner.benchmark_exchange,
                        )
                        if stock:
                            stock.is_active = False
                            session.commit()
                try:
                    await loop.run_in_executor(None, _deactivate)
                except Exception as e:
                    logger.warning("pipeline.deactivate_failed", symbol=symbol, error=str(e))
        return result

    @staticmethod
    def _df_to_records(df: pd.DataFrame, stock_uuid: str, timeframe: str) -> list[dict]:
        records: list[dict] = []
        for idx, row in df.iterrows():
            records.append(
                {
                    "stock_uuid": stock_uuid,
                    "date": idx.date() if hasattr(idx, "date") else idx,
                    "timeframe": timeframe,
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": int(row["volume"]),
                }
            )
        return records
