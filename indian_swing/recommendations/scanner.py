from __future__ import annotations

import asyncio
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import delete, select

from indian_swing.config.settings import settings
from indian_swing.core.logging_setup import get_logger
from indian_swing.core.lookback_engine import DynamicLookbackEngine
from indian_swing.data.pipeline import DataPipeline
from indian_swing.data.universe import UniverseLoader
from indian_swing.database.connection import get_sync_session
from indian_swing.database.models import Recommendation, ScanJob, Signal, Stock
from indian_swing.database.repositories.ohlcv_repo import OHLCVRepository
from indian_swing.database.repositories.stock_repo import StockRepository
from indian_swing.indicators.calculator import IndicatorCalculator
from indian_swing.notifications.telegram_notifier import notify_recommendations
from indian_swing.recommendations.validator import RecommendationValidator
from indian_swing.strategies.base import StrategyContext, StrategySignal
from indian_swing.strategies.registry import strategy_registry

logger = get_logger(__name__)


@dataclass
class ScanResult:
    scan_date: date
    scan_uuid: str = ""
    signals_generated: int = 0
    stocks_scanned: int = 0
    recommendations_saved: int = 0
    failed_stocks: int = 0
    filter_summary: dict[str, int] = field(default_factory=dict)
    validation_summary: dict[str, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    analytics: dict[str, Any] = field(default_factory=dict)


class RecommendationScanner:
    def __init__(self) -> None:
        strategy_registry.discover()
        self.strategy = strategy_registry.get("sivcs_vcp")
        self.pipeline = DataPipeline()
        self.validator = RecommendationValidator()
        self.progress_state = {
            "status": "idle",
            "scan_uuid": None,
            "scan_date": None,
            "total_stocks": 0,
            "completed": 0,
            "failed": 0,
            "current_symbol": None,
            "current_stage": "Idle",
            "errors": [],
        }

    async def scan(self, scan_date: date | None = None, force_refresh: bool = False) -> ScanResult:
        scan_date = scan_date or date.today()

        if not force_refresh:
            loop = asyncio.get_running_loop()
            def _check_completed():
                with get_sync_session() as session:
                    return session.execute(
                        select(ScanJob).where(
                            ScanJob.scan_date == scan_date,
                            ScanJob.status == "completed",
                            ScanJob.strategy_name == self.strategy.name,
                            ScanJob.strategy_version == self.strategy.version
                        )
                    ).scalars().first()
            existing_job = await loop.run_in_executor(None, _check_completed)
            if existing_job:
                result = ScanResult(
                    scan_date=scan_date,
                    scan_uuid=existing_job.scan_uuid,
                    signals_generated=existing_job.signals_generated,
                    stocks_scanned=existing_job.stocks_scanned,
                    recommendations_saved=existing_job.recommendations_created,
                    failed_stocks=existing_job.failed_stocks,
                    filter_summary=existing_job.filter_summary,
                    validation_summary=existing_job.validation_summary,
                    errors=existing_job.notes.get("errors", []) if isinstance(existing_job.notes, dict) else []
                )
                self.progress_state.update({
                    "status": "completed",
                    "scan_uuid": existing_job.scan_uuid,
                    "scan_date": str(scan_date),
                    "total_stocks": existing_job.total_stocks,
                    "completed": existing_job.stocks_scanned,
                    "failed": existing_job.failed_stocks,
                    "errors": result.errors
                })
                return result

        result = ScanResult(scan_date=scan_date)
        lookback = DynamicLookbackEngine.get_required_lookback(self.strategy)

        active_stocks, inactive_stocks = await asyncio.get_running_loop().run_in_executor(None, self._load_universe_and_stocks)
        stocks = active_stocks
        benchmark_symbol = settings.scanner.benchmark_symbol
        pipeline_symbols = [stock.symbol for stock in stocks]
        if benchmark_symbol not in pipeline_symbols:
            pipeline_symbols.append(benchmark_symbol)

        # Add inactive stock warnings to errors so they surface in the UI
        inactive_errors = [
            f"[INACTIVE] {s.symbol} ({s.name or 'Unknown'}): marked inactive — delisted or no valid history"
            for s in inactive_stocks
        ]
        result.errors.extend(inactive_errors)

        result.scan_uuid = await asyncio.get_running_loop().run_in_executor(None, self._create_scan_job, scan_date, len(stocks))
        self.progress_state.update(
            {
                "status": "running",
                "scan_uuid": result.scan_uuid,
                "scan_date": str(scan_date),
                "total_stocks": len(stocks),
                "completed": 0,
                "failed": 0,
                "current_symbol": None,
                "current_stage": "Loading Universe",
                "errors": list(inactive_errors),
            }
        )

        try:
            # Download benchmark data first
            self.progress_state["current_symbol"] = benchmark_symbol
            self.progress_state["current_stage"] = "Downloading Benchmark Data"
            try:
                await self.pipeline.run_incremental(
                    [benchmark_symbol],
                    required_daily_bars=lookback,
                    end=scan_date,
                    force_refresh=force_refresh,
                    progress_callback=lambda p: self.progress_state.update(p),
                )
            except Exception as exc:
                logger.error("scanner.benchmark_fetch_failed", symbol=benchmark_symbol, error=str(exc))

            # Download universe data in bulk first
            self.progress_state["current_symbol"] = "All Universe Stocks"
            self.progress_state["current_stage"] = "Downloading Universe Data"
            try:
                all_symbols = [s.symbol for s in stocks]
                await self.pipeline.run_incremental(
                    all_symbols,
                    required_daily_bars=lookback,
                    end=scan_date,
                    force_refresh=force_refresh,
                    progress_callback=lambda p: self.progress_state.update(p),
                )
            except Exception as exc:
                logger.error("scanner.universe_fetch_failed", error=str(exc))

            existing_signal_keys: set[tuple[str, str, str]] = set()
            filter_counter: Counter[str] = Counter()
            validation_counter: Counter[str] = Counter()
            persisted: list[tuple[Stock, StrategyContext, StrategySignal]] = []

            # Analytics state
            funnel_pass: Counter[str] = Counter()
            funnel_fail: Counter[str] = Counter()
            failure_reasons: dict[str, Counter[str]] = {}
            stock_journeys: dict[str, dict] = {}

            # Load benchmark once before loop to avoid duplicate queries
            benchmark_stock = None
            benchmark_daily = None
            with get_sync_session() as session:
                benchmark_stock = StockRepository(session).get_by_symbol(
                    settings.scanner.benchmark_symbol,
                    exchange=settings.scanner.benchmark_exchange,
                )
                if benchmark_stock is not None:
                    repo = OHLCVRepository(session)
                    start = scan_date - timedelta(days=int(lookback * 1.8))
                    benchmark_daily = repo.to_dataframe(benchmark_stock.stock_uuid, start, scan_date, "1d")

            for stock in stocks:
                self.progress_state["current_symbol"] = stock.symbol
                self.progress_state["current_stage"] = "Generating Indicators"
                try:
                    context = await asyncio.get_running_loop().run_in_executor(
                        None,
                        self._load_strategy_context,
                        stock,
                        lookback,
                        scan_date,
                        benchmark_stock,
                        benchmark_daily,
                    )
                    self.progress_state["current_stage"] = "Running Strategy"
                    signals = self.strategy.generate_signals(stock.symbol, context)

                    audit = getattr(self.strategy, "_last_audit_explanation", {})
                    journey = {"failed_at": None, "stages": {}}
                    for stage_name, stage_data in audit.items():
                        status = stage_data.get("status")
                        journey["stages"][stage_name] = status
                        if status == "PASS":
                            funnel_pass[stage_name] += 1
                        elif status == "FAIL":
                            funnel_fail[stage_name] += 1
                            journey["failed_at"] = stage_name
                            reason = str(stage_data.get("details", {}).get("reason") or "Failed condition")
                            if stage_name not in failure_reasons:
                                failure_reasons[stage_name] = Counter()
                            failure_reasons[stage_name][reason] += 1
                            break
                    stock_journeys[stock.symbol] = journey

                    if not signals:
                        filter_counter["Rejected"] += 1
                        result.stocks_scanned += 1
                        self.progress_state["completed"] = result.stocks_scanned
                        if result.stocks_scanned % 10 == 0 or result.stocks_scanned == len(stocks):
                            await asyncio.get_running_loop().run_in_executor(
                                None,
                                self._update_scan_job_progress,
                                result.scan_uuid,
                                result.stocks_scanned,
                                result.failed_stocks,
                                dict(filter_counter),
                                dict(validation_counter),
                            )
                        continue

                    self.progress_state["current_stage"] = "Validating Recommendation"
                    latest_daily_date = str(context.daily.index[-1].date())
                    for signal in signals:
                        validation = self.validator.validate(
                            stock=stock,
                            context=context,
                            signal=signal,
                            existing_signal_keys=existing_signal_keys,
                            latest_daily_date=latest_daily_date,
                        )
                        if not validation.valid:
                            validation_counter[validation.reason or "Rejected"] += 1
                            continue
                        existing_signal_keys.add((stock.stock_uuid, signal.metadata.get("strategy_name", ""), latest_daily_date))
                        filter_counter["BUY"] += 1
                        
                        # Add BUY to journey
                        if stock.symbol in stock_journeys:
                            stock_journeys[stock.symbol]["stages"]["BUY"] = "PASS"
                        funnel_pass["BUY"] += 1

                        persisted.append((stock, context, signal))

                        # Save immediately to the database
                        rank = len(persisted)
                        await asyncio.get_running_loop().run_in_executor(
                            None,
                            self._save_single_recommendation,
                            result.scan_uuid,
                            scan_date,
                            stock,
                            signal,
                            rank,
                        )

                    result.stocks_scanned += 1
                    self.progress_state["completed"] = result.stocks_scanned
                    if result.stocks_scanned % 10 == 0 or result.stocks_scanned == len(stocks):
                        await asyncio.get_running_loop().run_in_executor(
                            None,
                            self._update_scan_job_progress,
                            result.scan_uuid,
                            result.stocks_scanned,
                            result.failed_stocks,
                            dict(filter_counter),
                            dict(validation_counter),
                        )
                except Exception as exc:
                    result.stocks_scanned += 1
                    result.failed_stocks += 1
                    error_msg = f"{stock.symbol}: {exc}"
                    result.errors.append(error_msg)
                    self.progress_state["completed"] = result.stocks_scanned
                    self.progress_state["failed"] = result.failed_stocks
                    if "errors" not in self.progress_state:
                        self.progress_state["errors"] = []
                    self.progress_state["errors"].append(error_msg)
                    logger.error("scanner.stock_failed", symbol=stock.symbol, stage=self.progress_state["current_stage"], error=str(exc))
                    if result.stocks_scanned % 10 == 0 or result.stocks_scanned == len(stocks):
                        await asyncio.get_running_loop().run_in_executor(
                            None,
                            self._update_scan_job_progress,
                            result.scan_uuid,
                            result.stocks_scanned,
                            result.failed_stocks,
                            dict(filter_counter),
                            dict(validation_counter),
                        )

            result.signals_generated = len(persisted)
            result.recommendations_saved = len(persisted)
            result.filter_summary = dict(filter_counter)
            result.validation_summary = dict(validation_counter)
            
            result.analytics = {
                "funnel": {
                    "Universe": {"pass": len(stocks), "fail": 0},
                    **{
                        stage: {"pass": funnel_pass[stage], "fail": funnel_fail[stage]}
                        for stage in set(funnel_pass.keys()).union(funnel_fail.keys())
                    }
                },
                "failure_reasons": {
                    stage: dict(counts) for stage, counts in failure_reasons.items()
                },
                "stock_journeys": stock_journeys,
                "pipeline_health": {
                    "total_stocks": len(stocks),
                    "failed_data_load": result.failed_stocks,
                    "errors": result.errors
                }
            }

            await asyncio.get_running_loop().run_in_executor(None, self._complete_scan_job, result)
            self.progress_state["status"] = "completed"
            self.progress_state["current_stage"] = "Completed"

            # ----------------------------------------------------------------
            # Telegram notification — non-invasive, isolated step.
            # Runs *after* the scan is fully committed to the DB.
            # Any failure here is caught inside notify_recommendations and
            # logged; it never affects the scan result or pipeline status.
            # ----------------------------------------------------------------
            try:
                await asyncio.get_running_loop().run_in_executor(
                    None,
                    self._send_telegram_notification,
                    persisted,
                )
            except Exception as tg_exc:  # noqa: BLE001
                logger.error(
                    "scanner.telegram_notification_failed",
                    error=str(tg_exc),
                )

        except Exception as exc:
            await asyncio.get_running_loop().run_in_executor(None, self._fail_scan_job, result.scan_uuid, str(exc))
            self.progress_state["status"] = "failed"
            self.progress_state["current_stage"] = "Failed"
            raise

        return result

    def _save_single_recommendation(
        self,
        scan_uuid: str,
        scan_date: date,
        stock: Stock,
        signal: StrategySignal,
        rank: int,
    ) -> None:
        with get_sync_session() as session:
            signal_model = Signal(
                scan_uuid=scan_uuid,
                stock_uuid=stock.stock_uuid,
                strategy_name=self.strategy.name,
                strategy_version=self.strategy.version,
                signal_date=scan_date,
                direction=signal.direction.value,
                entry_price=signal.entry_price,
                stop_loss=signal.stop_loss,
                target_1=signal.target_1,
                target_2=signal.target_2,
                risk_reward=signal.risk_reward,
                confidence_score=signal.confidence_score,
                quality=signal.quality.value,
                risk_level=signal.risk_level.value,
                holding_days=signal.holding_days,
                reasons=signal.reasons,
                explanation=signal.explanation,
                indicator_snapshot=signal.indicator_snapshot,
                metadata_=signal.metadata,
            )
            session.add(signal_model)
            session.flush()

            recommendation = Recommendation(
                scan_uuid=scan_uuid,
                signal_id=signal_model.id,
                stock_uuid=stock.stock_uuid,
                scan_date=scan_date,
                strategy_name=self.strategy.name,
                strategy_version=self.strategy.version,
                rank=rank,
                confidence_score=signal.confidence_score,
                risk_level=signal.risk_level.value,
                entry_price=signal.entry_price,
                stop_loss=signal.stop_loss,
                target_price=signal.target_1,
                risk_per_share=round(signal.entry_price - signal.stop_loss, 4),
                risk_pct=signal.risk_pct,
                position_size=signal.metadata.get("position_size"),
                portfolio_weight_pct=signal.metadata.get("portfolio_weight_pct"),
                explanation=signal.explanation,
                summary="; ".join(signal.reasons[:3]),
            )
            session.add(recommendation)

            job = session.get(ScanJob, scan_uuid)
            if job is not None:
                job.signals_generated = rank
                job.recommendations_created = rank

    def _update_scan_job_progress(
        self,
        scan_uuid: str,
        stocks_scanned: int,
        failed_stocks: int,
        filter_summary: dict,
        validation_summary: dict,
    ) -> None:
        with get_sync_session() as session:
            job = session.get(ScanJob, scan_uuid)
            if job is not None:
                job.stocks_scanned = stocks_scanned
                job.failed_stocks = failed_stocks
                job.filter_summary = filter_summary
                job.validation_summary = validation_summary

    def _load_universe_and_stocks(self) -> tuple[list[Stock], list[Stock]]:
        with get_sync_session() as session:
            UniverseLoader(session).load_universe()
            from sqlalchemy import select
            from indian_swing.database.models import Stock
            all_stocks = session.execute(
                select(Stock)
                .where(Stock.environment == settings.app_env.upper())
                .order_by(Stock.symbol)
            ).scalars().all()
            active = [s for s in all_stocks if s.is_active]
            inactive = [s for s in all_stocks if not s.is_active]
            return active, inactive

    def _create_scan_job(self, scan_date: date, total_stocks: int) -> str:
        with get_sync_session() as session:
            existing_jobs = session.execute(
                select(ScanJob).where(
                    ScanJob.environment == settings.environment_name,
                    ScanJob.strategy_name == self.strategy.name,
                    ScanJob.strategy_version == self.strategy.version,
                    ScanJob.scan_date == scan_date,
                )
            ).scalars().all()
            for existing in existing_jobs:
                session.execute(delete(Recommendation).where(Recommendation.scan_uuid == existing.scan_uuid))
                session.execute(delete(Signal).where(Signal.scan_uuid == existing.scan_uuid))
                session.delete(existing)
            if existing_jobs:
                session.flush()

            job = ScanJob(
                environment=settings.environment_name,
                strategy_name=self.strategy.name,
                strategy_version=self.strategy.version,
                scan_date=scan_date,
                market_status="closed" if scan_date <= date.today() else "scheduled",
                status="running",
                total_stocks=total_stocks,
                started_at=datetime.utcnow(),
                notes={
                    "trading_date": str(scan_date),
                    "strategy_version": self.strategy.version,
                    "scanner_version": "1.0.0",
                    "indicator_version": "1.0.0",
                    "configuration_hash": "default",
                    "universe_version": "1.0.0",
                    "errors": []
                }
            )
            session.add(job)
            session.flush()
            return job.scan_uuid

    def _load_strategy_context(
        self,
        stock: Stock,
        lookback: int,
        scan_date: date,
        benchmark_stock: Stock | None = None,
        benchmark_daily: pd.DataFrame | None = None,
    ) -> StrategyContext:
        with get_sync_session() as session:
            repo = OHLCVRepository(session)
            start = scan_date - timedelta(days=int(lookback * 1.8))
            daily = repo.to_dataframe(stock.stock_uuid, start, scan_date, "1d")
            if daily.empty:
                raise ValueError("No daily history available")
            if benchmark_stock is None:
                benchmark_stock = StockRepository(session).get_by_symbol(
                    settings.scanner.benchmark_symbol,
                    exchange=settings.scanner.benchmark_exchange,
                )
            if benchmark_daily is None and benchmark_stock is not None:
                benchmark_daily = repo.to_dataframe(benchmark_stock.stock_uuid, start, scan_date, "1d")
            bundle = IndicatorCalculator.build(daily, benchmark_daily if benchmark_daily is not None and not benchmark_daily.empty else None)
            return StrategyContext(
                symbol=stock.symbol,
                exchange=stock.exchange,
                daily=bundle.daily,
                weekly=bundle.weekly,
                benchmark_daily=bundle.benchmark_daily,
                as_of_date=scan_date,
            )

    def _persist_scan_results(
        self,
        scan_uuid: str,
        scan_date: date,
        items: list[tuple[Stock, StrategyContext, StrategySignal]],
        filter_counter: Counter[str],
        validation_counter: Counter[str],
    ) -> None:
        ranked = sorted(items, key=lambda item: item[2].confidence_score, reverse=True)[: settings.scanner.max_recommendations]
        with get_sync_session() as session:
            for rank, (stock, _context, signal) in enumerate(ranked, start=1):
                signal_model = Signal(
                    scan_uuid=scan_uuid,
                    stock_uuid=stock.stock_uuid,
                    strategy_name=self.strategy.name,
                    strategy_version=self.strategy.version,
                    signal_date=scan_date,
                    direction=signal.direction.value,
                    entry_price=signal.entry_price,
                    stop_loss=signal.stop_loss,
                    target_1=signal.target_1,
                    target_2=signal.target_2,
                    risk_reward=signal.risk_reward,
                    confidence_score=signal.confidence_score,
                    quality=signal.quality.value,
                    risk_level=signal.risk_level.value,
                    holding_days=signal.holding_days,
                    reasons=signal.reasons,
                    explanation=signal.explanation,
                    indicator_snapshot=signal.indicator_snapshot,
                    metadata_=signal.metadata,
                )
                session.add(signal_model)
                session.flush()

                recommendation = Recommendation(
                    scan_uuid=scan_uuid,
                    signal_id=signal_model.id,
                    stock_uuid=stock.stock_uuid,
                    scan_date=scan_date,
                    strategy_name=self.strategy.name,
                    strategy_version=self.strategy.version,
                    rank=rank,
                    confidence_score=signal.confidence_score,
                    risk_level=signal.risk_level.value,
                    entry_price=signal.entry_price,
                    stop_loss=signal.stop_loss,
                    target_price=signal.target_1,
                    risk_per_share=round(signal.entry_price - signal.stop_loss, 4),
                    risk_pct=signal.risk_pct,
                    position_size=signal.metadata.get("position_size"),
                    portfolio_weight_pct=signal.metadata.get("portfolio_weight_pct"),
                    explanation=signal.explanation,
                    summary="; ".join(signal.reasons[:3]),
                )
                session.add(recommendation)

            job = session.get(ScanJob, scan_uuid)
            if job is not None:
                job.signals_generated = len(ranked)
                job.recommendations_created = len(ranked)
                job.filter_summary = dict(filter_counter)
                job.validation_summary = dict(validation_counter)

    def _complete_scan_job(self, result: ScanResult) -> None:
        with get_sync_session() as session:
            job = session.get(ScanJob, result.scan_uuid)
            if job is None:
                return
            job.status = "completed"
            job.stocks_scanned = result.stocks_scanned
            job.signals_generated = result.signals_generated
            job.recommendations_created = result.recommendations_saved
            job.failed_stocks = result.failed_stocks
            job.filter_summary = result.filter_summary
            job.validation_summary = result.validation_summary
            notes = dict(job.notes) if isinstance(job.notes, dict) else {}
            notes["errors"] = result.errors
            notes["analytics"] = getattr(result, "analytics", {})
            job.notes = notes
            job.completed_at = datetime.utcnow()

    def _fail_scan_job(self, scan_uuid: str, error: str) -> None:
        with get_sync_session() as session:
            job = session.get(ScanJob, scan_uuid)
            if job is None:
                return
            job.status = "failed"
            job.error = error
            job.completed_at = datetime.utcnow()

    def _send_telegram_notification(
        self,
        persisted: list[tuple[Stock, StrategyContext, StrategySignal]],
    ) -> None:
        """Build lightweight recommendation dicts and forward to the Telegram notifier.

        This method is the *only* bridge between the scanner and the
        notifications package.  It intentionally extracts a minimal,
        serialisable snapshot so the notifier has zero dependency on ORM
        objects or strategy internals.
        """
        rec_dicts: list[dict[str, Any]] = [
            {
                "symbol": stock.symbol,
                "company_name": stock.name,
                "action": signal.direction.value.upper(),
                "entry_price": signal.entry_price,
                "target_1": signal.target_1,
                "target_2": signal.target_2,
                "stop_loss": signal.stop_loss,
                "confidence_score": signal.confidence_score,
                "explanation": signal.explanation or {},
            }
            for stock, _context, signal in persisted
        ]
        notify_recommendations(rec_dicts)
