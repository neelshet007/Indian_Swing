from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from indian_swing.backtesting.runner import BacktestConfig, BacktestRunner

router = APIRouter()


class BacktestRequest(BaseModel):
    strategy_names: list[str]
    symbols: list[str]
    start_date: date
    end_date: date
    initial_capital: float = 1_000_000.0
    max_positions: int = 10
    risk_per_trade_pct: float = 2.0
    use_trailing_stop: bool = False


@router.post("/run")
async def run_backtest(req: BacktestRequest):
    config = BacktestConfig(
        strategy_names=req.strategy_names,
        symbols=req.symbols,
        start_date=req.start_date,
        end_date=req.end_date,
        initial_capital=req.initial_capital,
        max_positions=req.max_positions,
        risk_per_trade_pct=req.risk_per_trade_pct,
        use_trailing_stop=req.use_trailing_stop,
    )
    runner = BacktestRunner(config)
    result = await runner.run()

    return {
        "metrics": result.metrics,
        "monthly_returns": result.monthly_returns,
        "strategy_breakdown": result.strategy_breakdown,
        "equity_curve": result.equity_curve,
        "trade_count": len(result.trades),
        "trades": [t.to_dict() for t in result.trades[:500]],  # cap for API response
    }


@router.get("/results")
async def list_saved_results(limit: int = 20):
    from sqlalchemy import select
    from indian_swing.database.connection import get_session
    from indian_swing.database.models import BacktestResult

    async with get_session() as session:
        q = select(BacktestResult).order_by(BacktestResult.created_at.desc()).limit(limit)
        result = await session.execute(q)
        rows = result.scalars().all()

    return [
        {
            "id": r.id,
            "strategy_name": r.strategy_name,
            "universe": r.universe,
            "start_date": str(r.start_date),
            "end_date": str(r.end_date),
            "cagr": r.cagr,
            "sharpe_ratio": r.sharpe_ratio,
            "max_drawdown_pct": r.max_drawdown_pct,
            "win_rate": r.win_rate,
            "total_trades": r.total_trades,
            "created_at": str(r.created_at),
        }
        for r in rows
    ]
