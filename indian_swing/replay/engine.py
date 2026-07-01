"""
Replay Engine — sync DB version.
"""
from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import date
from typing import Any

import pandas as pd

from indian_swing.core.exceptions import ReplayError, ReplaySessionNotFoundError
from indian_swing.core.logging_setup import get_logger
from indian_swing.database.connection import get_sync_session
from indian_swing.database.models import Stock
from indian_swing.database.repositories.ohlcv_repo import OHLCVRepository
from indian_swing.strategies.registry import strategy_registry

logger = get_logger(__name__)


@dataclass
class ReplayState:
    session_id: str
    symbol: str
    strategy_name: str
    current_index: int
    total_candles: int
    current_date: date
    candles: list
    indicators: dict[str, Any]
    signal: dict | None
    open_trade: dict | None
    pnl: float
    cumulative_pnl: float
    drawdown: float
    mfe: float
    mae: float
    is_complete: bool

    @property
    def progress_pct(self) -> float:
        return round(self.current_index / max(self.total_candles - 1, 1) * 100, 1)


class ReplaySession:
    def __init__(self, session_id: str, symbol: str, strategy_name: str, df: pd.DataFrame) -> None:
        self.session_id = session_id
        self.symbol = symbol
        self.strategy_name = strategy_name
        self._df = df
        self._index = 0
        self._cumulative_pnl = 0.0
        self._peak_equity = 0.0
        self._strategy = strategy_registry.get(strategy_name)

    @property
    def is_complete(self) -> bool:
        return self._index >= len(self._df) - 1

    def current_state(self) -> ReplayState:
        visible = self._df.iloc[: self._index + 1]
        last = visible.iloc[-1]
        indicators = self._compute_indicators(visible)

        signal_dict = None
        try:
            sigs = self._strategy.generate_signals(self.symbol, visible)
            if sigs:
                s = sigs[0]
                signal_dict = {
                    "entry": s.entry_price, "stop": s.stop_loss,
                    "target_1": s.target_1, "target_2": s.target_2,
                    "confidence": s.confidence_score, "quality": s.quality.value,
                    "reasons": s.reasons, "risk_reward": s.risk_reward,
                }
        except Exception:
            pass

        candles = [
            {"date": str(idx.date()), "open": round(float(row["open"]), 2),
             "high": round(float(row["high"]), 2), "low": round(float(row["low"]), 2),
             "close": round(float(row["close"]), 2), "volume": int(row["volume"])}
            for idx, row in visible.iloc[-100:].iterrows()
        ]

        return ReplayState(
            session_id=self.session_id, symbol=self.symbol, strategy_name=self.strategy_name,
            current_index=self._index, total_candles=len(self._df),
            current_date=visible.index[-1].date(),
            candles=candles, indicators=indicators, signal=signal_dict,
            open_trade=None, pnl=0.0, cumulative_pnl=self._cumulative_pnl,
            drawdown=0.0, mfe=0.0, mae=0.0, is_complete=self.is_complete,
        )

    def step_forward(self, steps: int = 1) -> ReplayState:
        self._index = min(self._index + steps, len(self._df) - 1)
        return self.current_state()

    def step_backward(self, steps: int = 1) -> ReplayState:
        self._index = max(self._index - steps, 0)
        return self.current_state()

    def jump_to_date(self, target: date) -> ReplayState:
        dates = [d.date() for d in self._df.index]
        self._index = next((i for i, d in enumerate(dates) if d >= target), len(self._df) - 1)
        return self.current_state()

    def restart(self) -> ReplayState:
        self._index = 0
        self._cumulative_pnl = 0.0
        self._peak_equity = 0.0
        return self.current_state()

    def _compute_indicators(self, df: pd.DataFrame) -> dict:
        from indian_swing.indicators.trend import SMA
        from indian_swing.indicators.momentum import RSI
        from indian_swing.indicators.volatility import ATR
        result: dict = {}
        try:
            result["sma50"] = round(float(SMA().compute(df, period=50).iloc[-1]), 2)
            if len(df) >= 150:
                result["sma150"] = round(float(SMA().compute(df, period=150).iloc[-1]), 2)
            if len(df) >= 200:
                result["sma200"] = round(float(SMA().compute(df, period=200).iloc[-1]), 2)
            result["rsi"] = round(float(RSI().compute(df).iloc[-1]), 2)
            result["atr"] = round(float(ATR().compute(df).iloc[-1]), 2)
        except Exception:
            pass
        return result


class ReplayEngine:
    def __init__(self) -> None:
        self._sessions: dict[str, ReplaySession] = {}

    async def create_session(self, symbol: str, strategy_name: str, start_date: date, end_date: date) -> str:
        session_id = str(uuid.uuid4())
        loop = asyncio.get_event_loop()

        def _load():
            with get_sync_session() as session:
                from sqlalchemy import select
                stock = session.execute(select(Stock).where(Stock.symbol == symbol)).scalar_one_or_none()
                if stock is None:
                    raise ReplayError(f"Stock {symbol} not found.")
                repo = OHLCVRepository(session)
                return repo.to_dataframe(stock.id, start_date, end_date)

        df = await loop.run_in_executor(None, _load)
        if df.empty:
            raise ReplayError(f"No data for {symbol} between {start_date} and {end_date}.")

        strategy_registry.discover()
        replay_session = ReplaySession(session_id, symbol, strategy_name, df)
        self._sessions[session_id] = replay_session
        return session_id

    def get_session(self, session_id: str) -> ReplaySession:
        if session_id not in self._sessions:
            raise ReplaySessionNotFoundError(f"Replay session {session_id!r} not found.")
        return self._sessions[session_id]

    def destroy_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)


replay_engine = ReplayEngine()
