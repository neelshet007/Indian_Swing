from __future__ import annotations
import pandas as pd
from typing import Any

class BreakoutAnalyzer:
    @staticmethod
    def analyze_breakout(daily_df: pd.DataFrame, pivot_price: float, atr_14: float) -> dict[str, Any]:
        """
        Analyzes the quality of a breakout candle, checks the closing position of the price
        within the daily candle range, measures gaps, and validates the buy zone proximity.
        """
        if daily_df.empty:
            return {"passed": False, "reason": "No daily data available"}

        last_row = daily_df.iloc[-1]
        close = float(last_row["close"])
        high = float(last_row["high"])
        low = float(last_row["low"])
        open_p = float(last_row["open"])
        
        # 1. Close Position within Candle (90% close near the top is best)
        # Close position = (Close - Low) / (High - Low)
        denom = high - low
        close_pos = (close - low) / denom if denom > 0 else 1.0
        close_position_pass = close_pos >= 0.45 # Must close in top 55% of the day's range

        # 2. Gap Size Analysis
        prev_close = float(daily_df["close"].iloc[-2]) if len(daily_df) >= 2 else open_p
        gap_pct = (open_p - prev_close) / prev_close * 100
        gap_limit_pass = gap_pct < 5.0 # Reject massive gap ups (danger of institutional dump)

        # 3. Buy Zone Extension (Close within 5% of Pivot breakout price)
        extension_pct = (close - pivot_price) / pivot_price * 100
        buy_zone_pass = extension_pct <= 5.0 # strictly buy within 5% buy zone limit

        # 4. Volatility / ATR Expansion
        candle_range = high - low
        atr_ratio = candle_range / atr_14 if atr_14 > 0 else 1.0
        atr_expansion_pass = atr_ratio >= 1.0 # breakout should show range expansion

        passed = close_position_pass and gap_limit_pass and buy_zone_pass

        return {
            "passed": passed,
            "buy_zone_passed": buy_zone_pass,
            "extension_pct": round(extension_pct, 2),
            "close_position_pct": round(close_pos * 100, 2),
            "gap_pct": round(gap_pct, 2),
            "atr_expansion_ratio": round(atr_ratio, 2),
            "reason": (
                "Optimal Buy Zone" if passed else
                ("Extended (>5% above Pivot)" if not buy_zone_pass else
                 ("Weak Close (not in top 35% of range)" if not close_position_pass else
                  "Gap Limit Exceeded"))
            )
        }
