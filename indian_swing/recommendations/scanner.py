"""
Recommendation Scanner — sync DB version compatible with Python 3.14.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import date, timedelta

import pandas as pd

from indian_swing.config.settings import settings
from indian_swing.core.logging_setup import get_logger
from indian_swing.database.connection import get_sync_session
from indian_swing.database.models import Recommendation, Signal, ScanJob, Stock
from indian_swing.database.repositories.ohlcv_repo import OHLCVRepository
from indian_swing.database.repositories.stock_repo import StockRepository
from indian_swing.strategies.base import StrategySignal
from indian_swing.strategies.registry import strategy_registry

logger = get_logger(__name__)


@dataclass
class ScanResult:
    scan_date: date
    signals_generated: int = 0
    stocks_scanned: int = 0
    recommendations_saved: int = 0
    errors: list[str] = field(default_factory=list)


class RecommendationScanner:
    def __init__(self) -> None:
        self._cfg = settings.scanner
        strategy_registry.discover()
        self._strategies = strategy_registry.all()

    async def scan(self, scan_date: date | None = None) -> ScanResult:
        scan_date = scan_date or date.today()
        result = ScanResult(scan_date=scan_date)

        job_id = self._create_scan_job(scan_date)
        try:
            stocks = self._get_active_stocks()
            logger.info("scanner.start", date=str(scan_date), stocks=len(stocks))

            all_signals: list[tuple[StrategySignal, int]] = []
            loop = asyncio.get_event_loop()

            batch_size = self._cfg.max_workers
            for i in range(0, len(stocks), batch_size):
                batch = stocks[i: i + batch_size]
                tasks = [
                    loop.run_in_executor(None, self._scan_stock_sync, stock, scan_date)
                    for stock in batch
                ]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)

                for stock, br in zip(batch, batch_results):
                    if isinstance(br, Exception):
                        result.errors.append(f"{stock.symbol}: {br}")
                    else:
                        all_signals.extend([(sig, stock.id) for sig in br])
                        result.stocks_scanned += 1

            result.signals_generated = len(all_signals)
            top = self._rank_signals(all_signals)
            self._persist_recommendations(top, scan_date)
            result.recommendations_saved = len(top)
            self._complete_scan_job(job_id, result)

        except Exception as e:
            self._fail_scan_job(job_id, str(e))
            raise

        return result

    def _get_active_stocks(self) -> list[Stock]:
        with get_sync_session() as session:
            repo = StockRepository(session)
            return list(repo.get_active())

    def _scan_stock_sync(self, stock: Stock, scan_date: date) -> list[StrategySignal]:
        signals: list[StrategySignal] = []
        with get_sync_session() as session:
            repo = OHLCVRepository(session)
            start = date(max(1970, scan_date.year - settings.pipeline.lookback_years), scan_date.month, scan_date.day)
            df = repo.to_dataframe(stock.id, start, scan_date)

        if df.empty or len(df) < 60:
            return []

        for strategy in self._strategies:
            try:
                sigs = strategy.generate_signals(stock.symbol, df, scan_date)
                for sig in sigs:
                    sig.metadata["strategy_name"] = strategy.name
                signals.extend(sigs)
            except Exception as e:
                logger.debug("scanner.strategy_error", symbol=stock.symbol, strategy=strategy.name, error=str(e))

        return signals

    def _rank_signals(self, signals: list[tuple[StrategySignal, int]]) -> list[tuple[StrategySignal, int]]:
        quality_map = {"STRONG": 1.0, "MODERATE": 0.6, "WEAK": 0.3}

        def _score(item):
            sig = item[0]
            rr = min(sig.risk_reward / 3, 1.0)
            q = quality_map.get(sig.quality.value, 0.5)
            return 0.4 * sig.confidence_score + 0.3 * rr + 0.2 * q + 0.1

        ranked = sorted(signals, key=_score, reverse=True)
        return ranked[: self._cfg.max_recommendations]

    def _persist_recommendations(self, ranked: list[tuple[StrategySignal, int]], scan_date: date) -> None:
        with get_sync_session() as session:
            for rank, (signal, stock_id) in enumerate(ranked, start=1):
                sig_model = Signal(
                    stock_id=stock_id,
                    strategy_name=signal.metadata.get("strategy_name", "unknown"),
                    signal_date=scan_date,
                    direction=signal.direction.value,
                    entry_price=signal.entry_price,
                    stop_loss=signal.stop_loss,
                    target_1=signal.target_1,
                    target_2=signal.target_2,
                    risk_reward=signal.risk_reward,
                    confidence_score=signal.confidence_score,
                    quality=signal.quality.value,
                    holding_days=signal.holding_days,
                    reasons=signal.reasons,
                    metadata_=signal.metadata,
                )
                session.add(sig_model)
                session.flush()

                rec = Recommendation(
                    stock_id=stock_id,
                    signal_id=sig_model.id,
                    scan_date=scan_date,
                    rank=rank,
                    confidence_score=signal.confidence_score,
                    risk_level=signal.risk_level.value,
                    summary=signal.reasons[0] if signal.reasons else None,
                )
                session.add(rec)

    def _create_scan_job(self, scan_date: date) -> str:
        from datetime import datetime
        with get_sync_session() as session:
            job = ScanJob(scan_date=scan_date, status="running", started_at=datetime.utcnow())
            session.add(job)
            session.flush()
            return job.id

    def _complete_scan_job(self, job_id: str, result: ScanResult) -> None:
        from datetime import datetime
        with get_sync_session() as session:
            job = session.get(ScanJob, job_id)
            if job:
                job.status = "completed"
                job.stocks_scanned = result.stocks_scanned
                job.signals_generated = result.signals_generated
                job.recommendations_created = result.recommendations_saved
                job.completed_at = datetime.utcnow()

    def _fail_scan_job(self, job_id: str, error: str) -> None:
        from datetime import datetime
        with get_sync_session() as session:
            job = session.get(ScanJob, job_id)
            if job:
                job.status = "failed"
                job.error = error
                job.completed_at = datetime.utcnow()
