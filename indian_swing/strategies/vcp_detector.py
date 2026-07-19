from __future__ import annotations
import pandas as pd
import numpy as np
from datetime import date, timedelta
from typing import Any

class InstitutionalVCPDetector:
    def __init__(self, min_score: float = 70.0) -> None:
        self.min_score = min_score

    def detect_vcp(self, daily: pd.DataFrame) -> dict[str, Any]:
        """
        Detects Volatility Contraction Pattern (VCP) using institutional-grade swing analysis,
        noise filtering, dynamic wave counts (2-5 waves), volume dry-up analysis, and quality scoring.
        """
        # Ensure we have enough daily data
        if len(daily) < 50:
            return {"passed": False, "reason": "Not enough data (minimum 50 daily bars required)", "score": 0.0}

        # 1. ATR Calculation for Noise Filtering
        tr = pd.concat([
            daily["high"] - daily["low"],
            (daily["high"] - daily["close"].shift(1)).abs(),
            (daily["low"] - daily["close"].shift(1)).abs()
        ], axis=1).max(axis=1)
        atr_14 = tr.rolling(14).mean().iloc[-1]
        if pd.isna(atr_14) or atr_14 <= 0:
            atr_14 = daily["close"].iloc[-1] * 0.02

        # 2. Adaptive Lookback (30 to 120 days)
        lookback = min(120, len(daily))
        window = daily.iloc[-lookback:].copy()

        # 3. Pivot Detection (5-bar local extrema: 2 before, 2 after)
        # Avoid look-ahead bias by excluding the absolute last two days from pivot center
        highs = []
        lows = []
        for i in range(2, len(window) - 2):
            val_h = window["high"].iloc[i]
            val_l = window["low"].iloc[i]
            
            is_high = (
                val_h > window["high"].iloc[i-1] and val_h > window["high"].iloc[i-2] and
                val_h > window["high"].iloc[i+1] and val_h > window["high"].iloc[i+2]
            )
            is_low = (
                val_l < window["low"].iloc[i-1] and val_l < window["low"].iloc[i-2] and
                val_l < window["low"].iloc[i+1] and val_l < window["low"].iloc[i+2]
            )
            
            idx_date = window.index[i]
            if is_high:
                highs.append({"price": float(val_h), "date": idx_date, "idx": i})
            if is_low:
                lows.append({"price": float(val_l), "date": idx_date, "idx": i})

        # ATR-based pivot filtering to eliminate small noise swings
        filtered_highs = []
        for h in highs:
            if not filtered_highs or abs(h["price"] - filtered_highs[-1]["price"]) >= 1.5 * atr_14:
                filtered_highs.append(h)

        filtered_lows = []
        for l in lows:
            if not filtered_lows or abs(l["price"] - filtered_lows[-1]["price"]) >= 1.5 * atr_14:
                filtered_lows.append(l)

        # Fallback to 3-bar pivots if 5-bar pivots are too strict (insufficient pivots found)
        if len(filtered_highs) < 2 or len(filtered_lows) < 2:
            highs = []
            lows = []
            for i in range(1, len(window) - 1):
                val_h = window["high"].iloc[i]
                val_l = window["low"].iloc[i]
                is_high = val_h > window["high"].iloc[i-1] and val_h > window["high"].iloc[i+1]
                is_low = val_l < window["low"].iloc[i-1] and val_l < window["low"].iloc[i+1]
                if is_high:
                    highs.append({"price": float(val_h), "date": window.index[i]})
                if is_low:
                    lows.append({"price": float(val_l), "date": window.index[i]})
            filtered_highs = highs
            filtered_lows = lows

        if len(filtered_highs) < 2 or len(filtered_lows) < 2:
            return {
                "passed": False,
                "reason": "Insufficient pivots",
                "score": 0.0,
                "pivot": float(window["high"].max())
            }

        # 4. Contractions Depth Calculation
        contractions = []
        recent_highs = filtered_highs[-5:]
        recent_lows = filtered_lows[-5:]
        
        for h, l in zip(recent_highs, recent_lows):
            depth = (h["price"] - l["price"]) / h["price"] * 100
            contractions.append(round(depth, 2))

        if len(contractions) < 2:
            return {
                "passed": False,
                "reason": "Fewer than 2 contractions identified",
                "score": 0.0,
                "pivot": float(window["high"].max())
            }

        # 5. Volatility Reduction (Tightening check)
        is_tightening = True
        for i in range(1, len(contractions)):
            if contractions[i] >= contractions[i-1]:
                is_tightening = False
                break

        # 6. Volume Dry-Up Analysis
        avg_vol = window["volume"].mean()
        recent_vol = window["volume"].iloc[-5:].mean()
        vol_ratio = recent_vol / avg_vol if avg_vol > 0 else 1.0
        volume_dry_up = vol_ratio < 0.8

        # Supply exhaustion check: volume declining during contractions
        mid_vol = window["volume"].iloc[-15:-5].mean()
        early_vol = window["volume"].iloc[-30:-15].mean()
        vol_is_declining = recent_vol < mid_vol or mid_vol < early_vol

        # 7. Base Quality Check (No heavy distribution days)
        down_days = window[window["close"] < window["open"]]
        large_down_threshold = avg_vol * 1.5
        distribution_count = len(down_days[down_days["volume"] > large_down_threshold]) if not down_days.empty else 0
        constructive_base = distribution_count <= 2

        # 8. Pivot Line Selection
        pivot = float(recent_highs[-1]["price"]) if recent_highs else float(window["high"].max())

        # 9. VCP Scoring Engine (0-100)
        score = 0.0
        # 30% - Tightening Progression
        if is_tightening:
            score += 30.0
        elif contractions[-1] < contractions[0]:
            score += 15.0  # partial credit

        # 30% - Final Contraction Tightness
        last_c = contractions[-1]
        if last_c < 5.0:
            score += 30.0
        elif last_c < 10.0:
            score += 20.0
        elif last_c < 15.0:
            score += 10.0

        # 20% - Volume Dry-Up Progression
        if volume_dry_up:
            score += 10.0
        if vol_is_declining:
            score += 10.0

        # 20% - Base Quality & Contraction Count
        if constructive_base:
            score += 10.0
        if len(contractions) >= 3:
            score += 10.0
        else:
            score += 5.0

        passed = (score >= self.min_score) and (last_c < 10.0)

        return {
            "passed": passed,
            "score": score,
            "contractions": contractions,
            "volume_dry_up_ratio": round(vol_ratio, 3),
            "pivot": pivot,
            "is_tightening": is_tightening,
            "constructive_base": constructive_base
        }
