from __future__ import annotations

import asyncio
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

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
        }

    async def scan(self, scan_date: date | None = None, force_refresh: bool = False) -> ScanResult:
        scan_date = scan_date or date.today()
        result = ScanResult(scan_date=scan_date)
        lookback = DynamicLookbackEngine.get_required_lookback(self.strategy)

        stocks = await asyncio.get_running_loop().run_in_executor(None, self._load_universe_and_stocks)
        benchmark_symbol = settings.scanner.benchmark_symbol
        pipeline_symbols = [stock.symbol for stock in stocks]
        if benchmark_symbol not in pipeline_symbols:
            pipeline_symbols.append(benchmark_symbol)

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
            }
        )

        try:
            self.progress_state["current_stage"] = "Checking Database"
            await self.pipeline.run_incremental(
                pipeline_symbols,
                required_daily_bars=lookback,
                end=scan_date,
                force_refresh=force_refresh,
            )

            existing_signal_keys: set[tuple[str, str, str]] = set()
            filter_counter: Counter[str] = Counter()
            validation_counter: Counter[str] = Counter()
            persisted: list[tuple[Stock, StrategyContext, StrategySignal]] = []

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
                    )
                    self.progress_state["current_stage"] = "Running Strategy"
                    signals = self.strategy.generate_signals(stock.symbol, context)
                    if not signals:
                        filter_counter["Rejected"] += 1
                        result.stocks_scanned += 1
                        self.progress_state["completed"] = result.stocks_scanned
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
                        persisted.append((stock, context, signal))

                    result.stocks_scanned += 1
                    self.progress_state["completed"] = result.stocks_scanned
                except Exception as exc:
                    result.failed_stocks += 1
                    result.errors.append(f"{stock.symbol}: {exc}")
                    self.progress_state["failed"] = result.failed_stocks
                    logger.error("scanner.stock_failed", symbol=stock.symbol, stage=self.progress_state["current_stage"], error=str(exc))

            self.progress_state["current_stage"] = "Saving Recommendation"
            await asyncio.get_running_loop().run_in_executor(
                None,
                self._persist_scan_results,
                result.scan_uuid,
                scan_date,
                persisted,
                filter_counter,
                validation_counter,
            )

            result.signals_generated = len(persisted)
            result.recommendations_saved = len(persisted)
            result.filter_summary = dict(filter_counter)
            result.validation_summary = dict(validation_counter)
            await asyncio.get_running_loop().run_in_executor(None, self._complete_scan_job, result)
            self.progress_state["status"] = "completed"
            self.progress_state["current_stage"] = "Completed"
        except Exception as exc:
            await asyncio.get_running_loop().run_in_executor(None, self._fail_scan_job, result.scan_uuid, str(exc))
            self.progress_state["status"] = "failed"
            self.progress_state["current_stage"] = "Failed"
            raise

        return result

    def _load_universe_and_stocks(self) -> list[Stock]:
        with get_sync_session() as session:
            UniverseLoader(session).load_universe()
            return list(StockRepository(session).get_active())

    def _create_scan_job(self, scan_date: date, total_stocks: int) -> str:
        with get_sync_session() as session:
            existing = session.execute(
                select(ScanJob).where(
                    ScanJob.environment == settings.environment_name,
                    ScanJob.strategy_name == self.strategy.name,
                    ScanJob.strategy_version == self.strategy.version,
                    ScanJob.scan_date == scan_date,
                )
            ).scalar_one_or_none()
            if existing:
                session.execute(delete(Recommendation).where(Recommendation.scan_uuid == existing.id))
                session.execute(delete(Signal).where(Signal.scan_uuid == existing.id))
                session.delete(existing)
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
            )
            session.add(job)
            session.flush()
            return job.id

    def _load_strategy_context(self, stock: Stock, lookback: int, scan_date: date) -> StrategyContext:
        with get_sync_session() as session:
            repo = OHLCVRepository(session)
            start = scan_date - timedelta(days=int(lookback * 1.8))
            daily = repo.to_dataframe(stock.stock_uuid, start, scan_date, "1d")
            if daily.empty:
                raise ValueError("No daily history available")
            benchmark = StockRepository(session).get_by_symbol(
                settings.scanner.benchmark_symbol,
                exchange=settings.scanner.benchmark_exchange,
            )
            benchmark_daily = None
            if benchmark is not None:
                benchmark_daily = repo.to_dataframe(benchmark.id, start, scan_date, "1d")
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
            job.completed_at = datetime.utcnow()

    def _fail_scan_job(self, scan_uuid: str, error: str) -> None:
        with get_sync_session() as session:
            job = session.get(ScanJob, scan_uuid)
            if job is None:
                return
            job.status = "failed"
            job.error = error
            job.completed_at = datetime.utcnow()
