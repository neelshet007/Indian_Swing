"""
EMA Breakout Strategy.

Setup: Price breaks above a falling/flat 50 EMA with volume confirmation,
while sitting above the 200 EMA (long-term trend filter).

Entry: Close above 50 EMA with volume > 1.5x 20-day average.
Stop: Below recent swing low or 1.5x ATR from entry.
Target: 2R and 3R levels.
"""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from indian_swing.core.types import RiskLevel, SignalDirection, SignalQuality, Symbol
from indian_swing.indicators.momentum import RSI
from indian_swing.indicators.trend import EMA
from indian_swing.indicators.volatility import ATR
from indian_swing.indicators.volume import VolumeSMA
from indian_swing.strategies.base import BaseStrategy, StrategySignal


class EMABreakout(BaseStrategy):
    name = "EMABreakout"
    description = (
        "Price breaks above the 50 EMA with volume confirmation while above the 200 EMA. "
        "Classic trend-following breakout setup."
    )
    required_lookback = 210

    def generate_signals(
        self,
        symbol: Symbol,
        df: pd.DataFrame,
        as_of_date: date | None = None,
    ) -> list[StrategySignal]:
        if not self.validate_df(df):
            return []

        ema20 = EMA().compute(df, period=20)
        ema50 = EMA().compute(df, period=50)
        ema200 = EMA().compute(df, period=200)
        atr = ATR().compute(df, period=14)
        vol_sma = VolumeSMA().compute(df, period=20)
        rsi = RSI().compute(df, period=14)

        last = df.iloc[-1]
        prev = df.iloc[-2]

        close = last["close"]
        volume = last["volume"]
        last_atr = atr.iloc[-1]
        last_ema50 = ema50.iloc[-1]
        last_ema200 = ema200.iloc[-1]
        last_vol_sma = vol_sma.iloc[-1]
        last_rsi = rsi.iloc[-1]
        prev_close = prev["close"]
        prev_ema50 = ema50.iloc[-2]

        # ── Core conditions ──────────────────────────────────────────────────
        above_200 = close > last_ema200
        crossed_50_up = prev_close < prev_ema50 and close > last_ema50
        volume_surge = volume > 1.5 * last_vol_sma
        rsi_not_overbought = last_rsi < 75
        ema50_not_falling = ema50.iloc[-1] >= ema50.iloc[-5]

        conditions_met = sum([above_200, crossed_50_up, volume_surge, rsi_not_overbought, ema50_not_falling])

        if conditions_met < 3:
            return []

        if not (crossed_50_up and above_200):
            return []

        # ── Trade setup ───────────────────────────────────────────────────────
        entry = close
        swing_low = df["low"].iloc[-10:].min()
        stop = min(swing_low, entry - 1.5 * last_atr)
        risk = entry - stop
        target_1 = entry + 2 * risk
        target_2 = entry + 3 * risk

        if risk <= 0 or risk / entry > 0.08:
            return []

        # ── Confidence scoring ────────────────────────────────────────────────
        score = 0.5
        if volume_surge:
            score += 0.15
        if ema50_not_falling:
            score += 0.10
        if rsi_not_overbought:
            score += 0.10
        if 40 < last_rsi < 65:
            score += 0.05
        if last_ema50 > last_ema200:
            score += 0.10

        score = min(round(score, 2), 1.0)
        quality = SignalQuality.STRONG if score >= 0.75 else (
            SignalQuality.MODERATE if score >= 0.55 else SignalQuality.WEAK
        )
        risk_level = RiskLevel.LOW if risk / entry < 0.03 else (
            RiskLevel.MEDIUM if risk / entry < 0.05 else RiskLevel.HIGH
        )

        reasons = []
        reasons.append(f"Price crossed above 50 EMA (₹{last_ema50:.2f}) from below.")
        if above_200:
            reasons.append(f"Trend is bullish — price above 200 EMA (₹{last_ema200:.2f}).")
        if volume_surge:
            reasons.append(f"Volume ({volume:,.0f}) is {volume / last_vol_sma:.1f}x above 20-day average — institutional participation.")
        if rsi_not_overbought:
            reasons.append(f"RSI at {last_rsi:.1f} — momentum is building, not yet overbought.")

        return [
            StrategySignal(
                symbol=symbol,
                direction=SignalDirection.LONG,
                entry_price=round(entry, 2),
                stop_loss=round(stop, 2),
                target_1=round(target_1, 2),
                target_2=round(target_2, 2),
                confidence_score=score,
                quality=quality,
                risk_level=risk_level,
                holding_days=15,
                reasons=reasons,
                metadata={
                    "ema20": round(ema20.iloc[-1], 2),
                    "ema50": round(last_ema50, 2),
                    "ema200": round(last_ema200, 2),
                    "atr": round(last_atr, 2),
                    "rsi": round(last_rsi, 2),
                    "volume_ratio": round(volume / last_vol_sma, 2),
                },
            )
        ]
