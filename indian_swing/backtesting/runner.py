"""
Portfolio-level backtesting runner.
Supports: multiple strategies × multiple stocks, position sizing,
slippage, brokerage, STT, trailing stops, partial exits.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Sequence

import pandas as pd

from indian_swing.backtesting.metrics import compute_metrics, compute_monthly_returns
from indian_swing.backtesting.trade import Trade, TradeStatus
from indian_swing.config.settings import settings
from indian_swing.core.logging_setup import get_logger
from indian_swing.database.connection import get_session
from indian_swing.database.models import BacktestResult
from indian_swing.database.repositories.ohlcv_repo import OHLCVRepository
from indian_swing.database.models import Stock
from indian_swing.strategies.base import BaseStrategy, StrategySignal
from indian_swing.strategies.registry import strategy_registry

logger = get_logger(__name__)


@dataclass
class BacktestConfig:
    strategy_names: list[str]
    symbols: list[str]
    start_date: date
    end_date: date
    initial_capital: float = 1_000_000.0
    max_positions: int = 10
    risk_per_trade_pct: float = 2.0
    brokerage_pct: float = 0.0003
    stt_pct: float = 0.001
    slippage_pct: float = 0.0005
    max_holding_days: int = 30
    use_trailing_stop: bool = False
    trailing_stop_pct: float = 5.0


@dataclass
class BacktestRunResult:
    config: BacktestConfig
    trades: list[Trade]
    equity_curve: list[dict]
    metrics: dict
    monthly_returns: dict
    strategy_breakdown: dict  # strategy_name -> metrics


class BacktestRunner:
    def __init__(self, config: BacktestConfig) -> None:
        self.config = config
        self.cfg = settings.backtesting

    async def run(self) -> BacktestRunResult:
        """Execute full backtest and return results."""
        strategy_registry.discover()
        strategies = [strategy_registry.get(n) for n in self.config.strategy_names]

        # Load all OHLCV data
        ohlcv_data = await self._load_ohlcv()

        capital = self.config.initial_capital
        open_trades: list[Trade] = []
        all_trades: list[Trade] = []
        equity_curve: list[dict] = []

        trading_dates = self._get_trading_dates(ohlcv_data)

        for current_date in trading_dates:
            # Close trades that hit stop/target
            capital = self._process_exits(current_date, open_trades, all_trades, ohlcv_data, capital)

            # Expire old trades
            capital = self._expire_old_trades(current_date, open_trades, all_trades, ohlcv_data, capital)

            # Generate new signals
            if len(open_trades) < self.config.max_positions:
                new_trades = await self._generate_entries(
                    current_date, strategies, ohlcv_data, open_trades, capital
                )
                capital = self._enter_trades(new_trades, open_trades, capital)

            # Mark to market
            market_value = self._mark_to_market(current_date, open_trades, ohlcv_data)
            equity_curve.append({"date": str(current_date), "equity": capital + market_value})

        # Force-close open trades at end
        for trade in list(open_trades):
            self._close_trade(trade, trading_dates[-1], ohlcv_data, "CLOSED_MANUAL")
            all_trades.append(trade)
            open_trades.remove(trade)

        metrics = compute_metrics(
            all_trades,
            equity_curve,
            self.config.initial_capital,
            self.config.start_date,
            self.config.end_date,
        )
        monthly = compute_monthly_returns(equity_curve)
        breakdown = self._strategy_breakdown(all_trades)

        logger.info(
            "backtest.complete",
            strategies=self.config.strategy_names,
            trades=len(all_trades),
            cagr=metrics.get("cagr"),
            sharpe=metrics.get("sharpe_ratio"),
        )

        return BacktestRunResult(
            config=self.config,
            trades=all_trades,
            equity_curve=equity_curve,
            metrics=metrics,
            monthly_returns=monthly,
            strategy_breakdown=breakdown,
        )

    async def _load_ohlcv(self) -> dict[str, pd.DataFrame]:
        """Load OHLCV for all symbols from DB."""
        data: dict[str, pd.DataFrame] = {}
        async with get_session() as session:
            for symbol in self.config.symbols:
                from sqlalchemy import select
                result = await session.execute(select(Stock).where(Stock.symbol == symbol))
                stock = result.scalar_one_or_none()
                if stock is None:
                    logger.warning("backtest.stock_not_found", symbol=symbol)
                    continue
                repo = OHLCVRepository(session, type(None))
                df = await repo.to_dataframe(stock.stock_uuid, self.config.start_date, self.config.end_date)
                if not df.empty:
                    data[symbol] = df
        return data

    def _get_trading_dates(self, ohlcv_data: dict[str, pd.DataFrame]) -> list[date]:
        if not ohlcv_data:
            return []
        all_dates: set[date] = set()
        for df in ohlcv_data.values():
            all_dates.update(d.date() for d in df.index)
        return sorted(d for d in all_dates if self.config.start_date <= d <= self.config.end_date)

    def _process_exits(
        self,
        current_date: date,
        open_trades: list[Trade],
        all_trades: list[Trade],
        ohlcv_data: dict[str, pd.DataFrame],
        capital: float,
    ) -> float:
        for trade in list(open_trades):
            if trade.symbol not in ohlcv_data:
                continue
            df = ohlcv_data[trade.symbol]
            day_data = df[df.index.date == current_date]
            if day_data.empty:
                continue

            row = day_data.iloc[0]
            high, low, close = row["high"], row["low"], row["close"]

            # Update MFE/MAE
            if trade.direction == "LONG":
                favorable = high - trade.entry_price
                adverse = trade.entry_price - low
            else:
                favorable = trade.entry_price - low
                adverse = high - trade.entry_price

            trade.mfe = max(trade.mfe, favorable)
            trade.mae = max(trade.mae, adverse)

            # Trailing stop
            if self.config.use_trailing_stop and trade.direction == "LONG":
                trail_stop = close * (1 - self.config.trailing_stop_pct / 100)
                trade.stop_loss = max(trade.stop_loss, trail_stop)

            # Check stop hit
            if trade.direction == "LONG" and low <= trade.stop_loss:
                exit_price = trade.stop_loss
                costs = self._compute_costs(trade, exit_price)
                trade.commission = costs["commission"]
                trade.taxes = costs["taxes"]
                trade.exit_date = current_date
                trade.exit_price = exit_price * (1 - self.config.slippage_pct)
                trade.status = TradeStatus.CLOSED_STOP
                capital += trade.entry_price * trade.quantity + trade.net_pnl
                open_trades.remove(trade)
                all_trades.append(trade)
                continue

            # Check target hit
            if trade.direction == "LONG" and high >= trade.target_1:
                exit_price = trade.target_1
                costs = self._compute_costs(trade, exit_price)
                trade.commission = costs["commission"]
                trade.taxes = costs["taxes"]
                trade.exit_date = current_date
                trade.exit_price = exit_price
                trade.status = TradeStatus.CLOSED_TARGET
                capital += trade.entry_price * trade.quantity + trade.net_pnl
                open_trades.remove(trade)
                all_trades.append(trade)

        return capital

    def _expire_old_trades(
        self,
        current_date: date,
        open_trades: list[Trade],
        all_trades: list[Trade],
        ohlcv_data: dict[str, pd.DataFrame],
        capital: float,
    ) -> float:
        for trade in list(open_trades):
            if (current_date - trade.entry_date).days > self.config.max_holding_days:
                self._close_trade(trade, current_date, ohlcv_data, "CLOSED_EXPIRED")
                open_trades.remove(trade)
                all_trades.append(trade)
                capital += trade.entry_price * trade.quantity + trade.net_pnl
        return capital

    def _close_trade(
        self, trade: Trade, close_date: date, ohlcv_data: dict, status: str
    ) -> None:
        df = ohlcv_data.get(trade.symbol)
        close_price = trade.entry_price
        if df is not None:
            day = df[df.index.date == close_date]
            if not day.empty:
                close_price = day.iloc[0]["close"]
        costs = self._compute_costs(trade, close_price)
        trade.exit_date = close_date
        trade.exit_price = close_price
        trade.status = TradeStatus[status]
        trade.commission = costs["commission"]
        trade.taxes = costs["taxes"]

    async def _generate_entries(
        self,
        current_date: date,
        strategies: list[BaseStrategy],
        ohlcv_data: dict[str, pd.DataFrame],
        open_trades: list[Trade],
        capital: float,
    ) -> list[tuple[StrategySignal, str]]:
        open_symbols = {t.symbol for t in open_trades}
        candidates: list[tuple[StrategySignal, str]] = []

        for symbol, df in ohlcv_data.items():
            if symbol in open_symbols:
                continue
            hist = df[df.index.date <= current_date]
            if hist.empty:
                continue

            for strategy in strategies:
                try:
                    signals = strategy.generate_signals(symbol, hist, current_date)
                    for sig in signals:
                        candidates.append((sig, strategy.name))
                except Exception as e:
                    logger.warning("backtest.signal_error", symbol=symbol, strategy=strategy.name, error=str(e))

        # Sort by confidence score
        candidates.sort(key=lambda x: x[0].confidence_score, reverse=True)
        slots = self.config.max_positions - len(open_trades)
        return candidates[:slots]

    def _enter_trades(
        self,
        candidates: list[tuple[StrategySignal, str]],
        open_trades: list[Trade],
        capital: float,
    ) -> float:
        for signal, strategy_name in candidates:
            if len(open_trades) >= self.config.max_positions:
                break
            risk_amount = capital * (self.config.risk_per_trade_pct / 100)
            risk_per_share = abs(signal.entry_price - signal.stop_loss)
            if risk_per_share <= 0:
                continue
            quantity = max(1, int(risk_amount / risk_per_share))
            cost = quantity * signal.entry_price * (1 + self.config.brokerage_pct + self.config.slippage_pct)
            if cost > capital * 0.3:  # Never put >30% in one trade
                quantity = max(1, int(capital * 0.3 / signal.entry_price))
                cost = quantity * signal.entry_price

            if cost > capital:
                continue

            trade = Trade(
                symbol=signal.symbol,
                strategy=strategy_name,
                entry_date=date.today(),
                entry_price=signal.entry_price,
                stop_loss=signal.stop_loss,
                target_1=signal.target_1,
                target_2=signal.target_2,
                quantity=quantity,
                direction=signal.direction.value,
            )
            open_trades.append(trade)
            capital -= cost

        return capital

    def _mark_to_market(
        self,
        current_date: date,
        open_trades: list[Trade],
        ohlcv_data: dict[str, pd.DataFrame],
    ) -> float:
        total = 0.0
        for trade in open_trades:
            df = ohlcv_data.get(trade.symbol)
            if df is None:
                total += trade.entry_price * trade.quantity
                continue
            day = df[df.index.date == current_date]
            close = day.iloc[0]["close"] if not day.empty else trade.entry_price
            total += close * trade.quantity
        return total

    def _compute_costs(self, trade: Trade, exit_price: float) -> dict:
        turnover = exit_price * trade.quantity
        return {
            "commission": turnover * self.config.brokerage_pct * 2,
            "taxes": turnover * self.config.stt_pct,
        }

    def _strategy_breakdown(self, trades: list[Trade]) -> dict:
        breakdown = {}
        strategies = {t.strategy for t in trades}
        for strat in strategies:
            strat_trades = [t for t in trades if t.strategy == strat]
            closed = [t for t in strat_trades if t.exit_date is not None]
            if not closed:
                continue
            winners = [t for t in closed if t.is_winner]
            breakdown[strat] = {
                "total_trades": len(closed),
                "win_rate": round(len(winners) / len(closed) * 100, 2),
                "avg_return_pct": round(sum(t.return_pct for t in closed) / len(closed), 2),
                "total_pnl": round(sum(t.net_pnl for t in closed), 2),
            }
        return breakdown
