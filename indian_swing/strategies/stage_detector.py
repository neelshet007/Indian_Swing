from __future__ import annotations
import pandas as pd
import numpy as np

class InstitutionalStageDetector:
    @staticmethod
    def calculate_stages(df: pd.DataFrame) -> pd.DataFrame:
        """
        Enriches the weekly dataframe with institutional stage classifications,
        regression-based slopes, pivot analysis, extension warnings, and a Stage Confidence Score (0-100).
        """
        frame = df.copy()
        n = len(frame)
        if n < 40:
            frame["stage"] = 0
            frame["stage2"] = False
            frame["stage_confidence"] = 0.0
            frame["stage_classification"] = "Insufficient Data"
            frame["stage_details"] = "{}"
            frame["weekly_uptrend"] = False
            return frame

        ma_30 = frame["sma_30w"]
        ma_40 = frame["sma_40w"]

        # 1. Rolling Linear Regression Slope of 30W SMA over 6 weeks (to ensure trend persistence)
        # divisor for x = [0..5] regression slope is 105.0
        x = np.array([0, 1, 2, 3, 4, 5])
        sum_x = 15
        sum_x2 = 55
        divisor = 105.0

        y_rolls = [ma_30.shift(5 - i) for i in range(6)]
        sum_y = sum(y_rolls)
        sum_xy = sum(i * y_rolls[i] for i in range(6))
        ma_30_slope = (6 * sum_xy - sum_x * sum_y) / divisor

        # Fallback to simple shift diff if there are NaNs on early rows
        ma_30_slope = ma_30_slope.fillna(ma_30 - ma_30.shift(4))

        # 2. Moving Average separation metric
        separation = ((ma_30 - ma_40) / ma_40 * 100).fillna(0.0)

        # 3. Market Structure (Higher Highs / Higher Lows swing pivots on weekly candles)
        pivot_h = (frame["high"].shift(1) > frame["high"]) & (frame["high"].shift(1) > frame["high"].shift(2))
        pivot_l = (frame["low"].shift(1) < frame["low"]) & (frame["low"].shift(1) < frame["low"].shift(2))

        last_pivot_h = frame["high"].shift(1).where(pivot_h).ffill()
        last_pivot_l = frame["low"].shift(1).where(pivot_l).ffill()
        
        prior_pivot_h = last_pivot_h.shift(1).ffill()
        prior_pivot_l = last_pivot_l.shift(1).ffill()

        higher_highs = (last_pivot_h > prior_pivot_h).fillna(False)
        higher_lows = (last_pivot_l > prior_pivot_l).fillna(False)

        # 4. Proximity to 52-week High
        high_52w = frame["high"].rolling(52, min_periods=20).max()
        dist_from_high = ((high_52w - frame["close"]) / high_52w * 100).fillna(0.0)

        # 5. Extension Analysis (distance above the 30W SMA)
        extension = ((frame["close"] - ma_30) / ma_30 * 100).fillna(0.0)

        # 6. Basic stage definitions (Weinstein 1-4)
        stage_2_mask = (frame["close"] > ma_30) & (ma_30 > ma_40) & (ma_30_slope > 0)
        stage_4_mask = (frame["close"] < ma_30) & (ma_30 < ma_40) & (ma_30_slope < 0)

        frame["stage"] = 1  # Default to Stage 1 (Weinstein Basing)
        frame.loc[stage_2_mask, "stage"] = 2
        frame.loc[stage_4_mask, "stage"] = 4
        
        stage_3_mask = (~stage_2_mask) & (~stage_4_mask) & (ma_30_slope < 0)
        frame.loc[stage_3_mask, "stage"] = 3

        # 7. Stage Confidence Score (0-100)
        confidence = pd.Series(0.0, index=frame.index)
        
        # 30% - MA Slope consistency & acceleration
        slope_pos = ma_30_slope > 0
        slope_accel = ma_30_slope > ma_30_slope.shift(1)
        confidence.loc[slope_pos] += 20.0
        confidence.loc[slope_pos & slope_accel] += 10.0
        
        # 25% - Higher Highs & Higher Lows
        confidence.loc[higher_highs] += 12.5
        confidence.loc[higher_lows] += 12.5
        
        # 25% - MA separation and alignment
        confidence.loc[ma_30 > ma_40] += 15.0
        confidence.loc[separation > 2.0] += 10.0
        
        # 20% - Proximity to 52-week High (Leadership check)
        confidence.loc[dist_from_high < 10.0] += 20.0
        confidence.loc[(dist_from_high >= 10.0) & (dist_from_high < 25.0)] += 10.0

        frame["stage_confidence"] = confidence.round(2)

        # 8. Stage Sub-Classifications
        classifications = pd.Series("Stage 1", index=frame.index)
        classifications.loc[stage_4_mask] = "Stage 4"
        classifications.loc[stage_3_mask] = "Stage 3"
        
        # Consecutive weeks in Stage 2
        s2_consec = stage_2_mask.groupby((~stage_2_mask).cumsum()).cumsum()
        
        is_early = stage_2_mask & (s2_consec <= 8)
        is_developing = stage_2_mask & (s2_consec > 8) & (s2_consec <= 24)
        is_mature = stage_2_mask & (s2_consec > 24)
        is_late = stage_2_mask & ((extension > 15.0) | (dist_from_high > 25.0))
        
        classifications.loc[is_early] = "Early Stage 2"
        classifications.loc[is_developing] = "Developing Stage 2"
        classifications.loc[is_mature] = "Mature Stage 2"
        classifications.loc[is_late] = "Late Stage 2"
        
        frame["stage_classification"] = classifications
        frame["stage2"] = stage_2_mask
        frame["weekly_uptrend"] = ma_30_slope > 0

        # Construct explanations
        explanations = []
        for idx, row in frame.iterrows():
            c_close = float(row["close"])
            c_ma30 = float(row["sma_30w"])
            c_ma40 = float(row["sma_40w"])
            c_slope = float(ma_30_slope.loc[idx])
            c_ext = float(extension.loc[idx])
            c_dist = float(dist_from_high.loc[idx])
            
            checks = {
                "Price Above 30W SMA": "PASS" if c_close > c_ma30 else "FAIL",
                "30W SMA Above 40W SMA": "PASS" if c_ma30 > c_ma40 else "FAIL",
                "Rising 30W SMA Slope": "PASS" if c_slope > 0 else "FAIL",
                "Uptrend Classification": row["stage_classification"],
                "Extension Pct": round(c_ext, 2),
                "Dist From 52W High": round(c_dist, 2)
            }
            explanations.append(str(checks))
            
        frame["stage_details"] = explanations
        return frame
