from __future__ import annotations
import pandas as pd
import numpy as np

class MarketRegimeEngine:
    @staticmethod
    def classify_regime(benchmark_df: pd.DataFrame | None) -> dict[str, Any]:
        """
        Classifies the current market regime (Bull, Bear, Sideways, Correction, Recovery)
        based on the benchmark index (^NSEI) trend, moving averages, and volatility.
        """
        if benchmark_df is None or len(benchmark_df) < 200:
            return {
                "regime": "Bull", # Default fallback
                "passed": True,
                "reason": "Insufficient benchmark history; assuming favorable conditions",
                "volatility": "Low",
                "trend": "Up"
            }

        df = benchmark_df.copy().sort_index()
        
        # Calculate moving averages
        df["sma_50"] = df["close"].rolling(50, min_periods=50).mean()
        df["sma_200"] = df["close"].rolling(200, min_periods=200).mean()
        
        last = df.iloc[-1]
        close = float(last["close"])
        sma_50 = float(last["sma_50"])
        sma_200 = float(last["sma_200"])
        
        # Calculate slope of 200 DMA (over last 20 days)
        sma_200_prev = float(df["sma_200"].iloc[-21]) if len(df) >= 21 else sma_200
        slope_200 = sma_200 - sma_200_prev
        
        # Volatility check: rolling standard deviation of daily returns (20 days)
        df["returns"] = df["close"].pct_change()
        vol = df["returns"].rolling(20).std().iloc[-1] * np.sqrt(252) * 100 # annualized vol %
        vol_regime = "High" if vol > 22.0 else ("Low" if vol < 14.0 else "Medium")

        # Classify regime based on Weinstein / Minervini trend guidelines
        if close > sma_50 and sma_50 > sma_200 and slope_200 > 0:
            regime = "Bull"
            passed = True
            reason = "Market in a strong structural uptrend (Close > 50MA > 200MA)"
        elif close < sma_50 and close > sma_200 and slope_200 > 0:
            regime = "Correction"
            passed = True # Keep scans active on pullbacks to key support
            reason = "Short-term correction within a long-term bull market"
        elif close > sma_50 and close > sma_200 and slope_200 <= 0:
            regime = "Recovery"
            passed = True
            reason = "Uptrend emerging from consolidation/bear market base"
        elif close < sma_50 and close < sma_200:
            regime = "Bear"
            passed = False  # Avoid fresh breakouts in a clear bear market
            reason = "Structural bear market (Close < 50MA & 200MA)"
        else:
            regime = "Sideways"
            passed = True
            reason = "Market consolidating; trend lacks direction"

        # India VIX / High volatility cap (e.g. panic periods)
        if vol > 30.0:
            passed = False
            reason += " (PANIC VOLATILITY: Scans disabled due to high market risk)"

        return {
            "regime": regime,
            "passed": passed,
            "reason": reason,
            "volatility": vol_regime,
            "trend": "Up" if close > sma_200 else "Down"
        }
from typing import Any
