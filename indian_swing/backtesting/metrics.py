"""
Performance metrics engine.
All institutional-grade metrics: CAGR, Sharpe, Sortino, Calmar, Expectancy.
"""
from __future__ import annotations

import math
from datetime import date
from typing import Sequence

import numpy as np
import pandas as pd

from indian_swing.backtesting.trade import Trade


def compute_metrics(
    trades: list[Trade],
    equity_curve: list[dict],
    initial_capital: float,
    start_date: date,
    end_date: date,
) -> dict:
    """Compute all backtest performance metrics from trade list and equity curve."""

    closed = [t for t in trades if t.exit_date is not None]
    if not closed:
        return _empty_metrics(initial_capital)

    final_capital = equity_curve[-1]["equity"] if equity_curve else initial_capital
    total_return = (final_capital - initial_capital) / initial_capital * 100
    years = max((end_date - start_date).days / 365.25, 0.01)
    cagr = ((final_capital / initial_capital) ** (1 / years) - 1) * 100

    # Win/Loss stats
    winners = [t for t in closed if t.is_winner]
    losers = [t for t in closed if not t.is_winner]
    win_rate = len(winners) / len(closed) * 100 if closed else 0
    avg_gain = np.mean([t.return_pct for t in winners]) if winners else 0.0
    avg_loss = np.mean([t.return_pct for t in losers]) if losers else 0.0

    # Expectancy
    expectancy = (win_rate / 100 * avg_gain) + ((1 - win_rate / 100) * avg_loss)

    # Equity curve metrics
    eq_series = _equity_series(equity_curve)
    daily_returns = eq_series.pct_change().dropna()

    sharpe = _sharpe(daily_returns)
    sortino = _sortino(daily_returns)
    max_dd, max_dd_pct = _max_drawdown(eq_series)
    calmar = cagr / abs(max_dd_pct) if max_dd_pct != 0 else 0

    return {
        "initial_capital": initial_capital,
        "final_capital": round(final_capital, 2),
        "total_return_pct": round(total_return, 2),
        "cagr": round(cagr, 2),
        "sharpe_ratio": round(sharpe, 3),
        "sortino_ratio": round(sortino, 3),
        "calmar_ratio": round(calmar, 3),
        "max_drawdown_pct": round(max_dd_pct, 2),
        "win_rate": round(win_rate, 2),
        "total_trades": len(closed),
        "winning_trades": len(winners),
        "losing_trades": len(losers),
        "avg_gain_pct": round(float(avg_gain), 2),
        "avg_loss_pct": round(float(avg_loss), 2),
        "expectancy": round(float(expectancy), 2),
        "avg_holding_days": round(np.mean([t.holding_days for t in closed]), 1),
        "profit_factor": _profit_factor(winners, losers),
    }


def compute_monthly_returns(equity_curve: list[dict]) -> dict[str, float]:
    """Returns {YYYY-MM: return_pct} for each month."""
    if not equity_curve:
        return {}
    eq = _equity_series(equity_curve)
    monthly = eq.resample("ME").last()
    monthly_returns = monthly.pct_change().dropna() * 100
    return {str(dt.date())[:7]: round(v, 2) for dt, v in monthly_returns.items()}


def _equity_series(equity_curve: list[dict]) -> pd.Series:
    df = pd.DataFrame(equity_curve)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()
    return df["equity"]


def _sharpe(daily_returns: pd.Series, risk_free_daily: float = 0.0001896) -> float:
    excess = daily_returns - risk_free_daily
    if excess.std() == 0:
        return 0.0
    return float(excess.mean() / excess.std() * math.sqrt(252))


def _sortino(daily_returns: pd.Series, risk_free_daily: float = 0.0001896) -> float:
    excess = daily_returns - risk_free_daily
    downside = excess[excess < 0]
    if len(downside) == 0 or downside.std() == 0:
        return float("inf")
    return float(excess.mean() / downside.std() * math.sqrt(252))


def _max_drawdown(equity: pd.Series) -> tuple[float, float]:
    peak = equity.cummax()
    drawdown = equity - peak
    max_dd = float(drawdown.min())
    max_dd_pct = float((drawdown / peak).min() * 100) if peak.max() > 0 else 0.0
    return max_dd, max_dd_pct


def _profit_factor(winners: list[Trade], losers: list[Trade]) -> float:
    gross_profit = sum(t.net_pnl for t in winners)
    gross_loss = abs(sum(t.net_pnl for t in losers))
    return round(gross_profit / gross_loss, 2) if gross_loss > 0 else float("inf")


def _empty_metrics(initial_capital: float) -> dict:
    return {
        "initial_capital": initial_capital,
        "final_capital": initial_capital,
        "total_return_pct": 0.0,
        "cagr": 0.0,
        "sharpe_ratio": 0.0,
        "sortino_ratio": 0.0,
        "calmar_ratio": 0.0,
        "max_drawdown_pct": 0.0,
        "win_rate": 0.0,
        "total_trades": 0,
        "winning_trades": 0,
        "losing_trades": 0,
        "avg_gain_pct": 0.0,
        "avg_loss_pct": 0.0,
        "expectancy": 0.0,
        "avg_holding_days": 0.0,
        "profit_factor": 0.0,
    }
