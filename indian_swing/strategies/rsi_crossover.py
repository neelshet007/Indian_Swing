"""
RSI Crossover Strategy.

Setup: RSI crosses above 30 (oversold exit) while price is above 200 EMA,
indicating a potential mean reversion in an uptrend.

Entry: RSI crosses above 30 on rising price.
Stop: Below recent 10-day swing low.
Target: 1.5R and 2.5R.
"""
from __future__ import annotations

from datetime import date

import pandas as pd

from indian_swing.core.types import RiskLevel, SignalDirection, SignalQuality, Symbol
from indian_swing.indicators.momentum import RSI
from indian_swing.indicators.trend import EMA
from indian_swing.indicators.volatility import ATR
from indian_swing.indicators.volume import VolumeSMA
from indian_swing.strategies.base import BaseStrategy, StrategySignal


class RSICrossover(BaseStrategy):
    name = "RSICrossover"
    description = (
        "RSI bounces from oversold (<30) territory in an uptrending stock (above 200 EMA). "
        "Mean reversion with trend filter."
    )
    required_lookback = 210

    def generate_signals(
        self, symbol: Symbol, df: pd.DataFrame, as_of_date: date | None = None
    ) -> list[StrategySignal]:
        if not self.validate_df(df):
            return []

        rsi = RSI().compute(df, period=14)
        ema200 = EMA().compute(df, period=200)
        ema50 = EMA().compute(df, period=50)
        atr = ATR().compute(df, period=14)
        vol_sma = VolumeSMA().compute(df, period=20)

        last = df.iloc[-1]
        close = last["close"]
        volume = last["volume"]

        rsi_now = rsi.iloc[-1]
        rsi_prev = rsi.iloc[-2]
        ema200_now = ema200.iloc[-1]
        ema50_now = ema50.iloc[-1]
        last_atr = atr.iloc[-1]
        last_vol_sma = vol_sma.iloc[-1]

        above_200 = close > ema200_now
        rsi_crossed_above_30 = rsi_prev < 30 and rsi_now >= 30
        rsi_not_overbought = rsi_now < 70
        above_50 = close > ema50_now
        volume_ok = volume >= 0.8 * last_vol_sma  # lower bar for mean reversion

        if not (rsi_crossed_above_30 and above_200):
            return []

        entry = close
        swing_low = df["low"].iloc[-10:].min()
        stop = min(swing_low * 0.995, entry - 1.2 * last_atr)
        risk = entry - stop
        if risk <= 0 or risk / entry > 0.07:
            return []

        target_1 = entry + 1.5 * risk
        target_2 = entry + 2.5 * risk

        score = 0.5
        if above_200:
            score += 0.15
        if above_50:
            score += 0.10
        if rsi_now < 35:
            score += 0.10
        if volume_ok:
            score += 0.10
        score = min(round(score, 2), 1.0)

        quality = SignalQuality.STRONG if score >= 0.75 else (
            SignalQuality.MODERATE if score >= 0.55 else SignalQuality.WEAK
        )
        risk_level = RiskLevel.LOW if risk / entry < 0.03 else (
            RiskLevel.MEDIUM if risk / entry < 0.05 else RiskLevel.HIGH
        )

        reasons = [
            f"RSI crossed above 30 from {rsi_prev:.1f} → {rsi_now:.1f} — oversold condition resolved.",
            f"Uptrend intact — price above 200 EMA (₹{ema200_now:.2f}).",
        ]
        if above_50:
            reasons.append(f"Short-term trend bullish — above 50 EMA (₹{ema50_now:.2f}).")

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
                holding_days=10,
                reasons=reasons,
                metadata={
                    "rsi": round(rsi_now, 2),
                    "rsi_prev": round(rsi_prev, 2),
                    "ema200": round(ema200_now, 2),
                    "ema50": round(ema50_now, 2),
                    "atr": round(last_atr, 2),
                },
            )
        ]
