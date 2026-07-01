"""
Volume Breakout Strategy.

Setup: Price breaks above a 20-day resistance level (highest high)
with significant volume surge (2x+ average), indicating institutional accumulation.

Entry: New 20-day high close with volume > 2x average.
Stop: Below breakout candle low or previous resistance as support.
Target: 1.5x and 2.5x the breakout move.
"""
from __future__ import annotations

from datetime import date

import pandas as pd

from indian_swing.core.types import RiskLevel, SignalDirection, SignalQuality, Symbol
from indian_swing.indicators.momentum import RSI
from indian_swing.indicators.trend import EMA
from indian_swing.indicators.volatility import ATR
from indian_swing.indicators.volume import MFI, OBV, VolumeSMA
from indian_swing.strategies.base import BaseStrategy, StrategySignal


class VolumeBreakout(BaseStrategy):
    name = "VolumeBreakout"
    description = (
        "Price breaks above a 20-day resistance zone with 2x+ volume surge. "
        "Indicates institutional accumulation and strong bullish conviction."
    )
    required_lookback = 60

    def generate_signals(
        self, symbol: Symbol, df: pd.DataFrame, as_of_date: date | None = None
    ) -> list[StrategySignal]:
        if not self.validate_df(df):
            return []

        vol_sma = VolumeSMA().compute(df, period=20)
        atr = ATR().compute(df, period=14)
        ema200 = EMA().compute(df, period=200)
        rsi = RSI().compute(df, period=14)
        mfi = MFI().compute(df, period=14)

        last = df.iloc[-1]
        close = last["close"]
        volume = last["volume"]
        high = last["high"]
        low = last["low"]

        # Resistance = highest high of previous 20 bars (excluding today)
        resistance_window = df["high"].iloc[-21:-1]
        resistance = resistance_window.max()
        prev_close = df["close"].iloc[-2]

        last_atr = atr.iloc[-1]
        last_vol_sma = vol_sma.iloc[-1]
        last_ema200 = ema200.iloc[-1]
        last_rsi = rsi.iloc[-1]
        last_mfi = mfi.iloc[-1]

        # ── Core conditions ──────────────────────────────────────────────────
        breakout = prev_close <= resistance and close > resistance
        volume_surge = volume > 2.0 * last_vol_sma
        above_200 = close > last_ema200
        rsi_bullish = 40 < last_rsi < 80
        mfi_positive = last_mfi > 50

        if not (breakout and volume_surge):
            return []

        entry = close
        stop = max(low - 0.2 * last_atr, resistance * 0.97)
        risk = entry - stop
        if risk <= 0 or risk / entry > 0.08:
            return []

        target_1 = entry + 1.5 * risk
        target_2 = entry + 2.5 * risk

        # ── Scoring ───────────────────────────────────────────────────────────
        score = 0.55
        vol_ratio = volume / last_vol_sma
        if vol_ratio >= 3.0:
            score += 0.15
        elif vol_ratio >= 2.0:
            score += 0.10
        if above_200:
            score += 0.10
        if rsi_bullish:
            score += 0.05
        if mfi_positive:
            score += 0.05
        score = min(round(score, 2), 1.0)

        quality = SignalQuality.STRONG if score >= 0.75 else (
            SignalQuality.MODERATE if score >= 0.55 else SignalQuality.WEAK
        )
        risk_level = RiskLevel.MEDIUM if risk / entry < 0.05 else RiskLevel.HIGH

        reasons = [
            f"Price broke above 20-day resistance (₹{resistance:.2f}) with decisive close.",
            f"Volume ({volume:,.0f}) is {vol_ratio:.1f}x the 20-day average — strong institutional conviction.",
        ]
        if above_200:
            reasons.append(f"Long-term trend is bullish — price above 200 EMA (₹{last_ema200:.2f}).")
        if mfi_positive:
            reasons.append(f"Money Flow Index at {last_mfi:.1f} — buying pressure confirmed.")

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
                holding_days=12,
                reasons=reasons,
                metadata={
                    "resistance": round(resistance, 2),
                    "volume_ratio": round(vol_ratio, 2),
                    "rsi": round(last_rsi, 2),
                    "mfi": round(last_mfi, 2),
                    "atr": round(last_atr, 2),
                },
            )
        ]
