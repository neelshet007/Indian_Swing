from __future__ import annotations
from typing import Any

class ScoringEngine:
    @staticmethod
    def calculate_overall_score(
        stage_confidence: float,
        vcp_score: float,
        breakout_details: dict[str, Any],
        rs_score: float,
        market_regime_health: float
    ) -> dict[str, Any]:
        """
        Computes a unified, fully explainable institutional score (0-100)
        based on multi-factor momentum indicators.
        """
        # Weighting factors:
        # 25% Stage 2 Confidence
        # 25% VCP Score
        # 20% Breakout Candle Quality
        # 15% Relative Strength Score
        # 15% Market Regime Health
        
        # Calculate breakout candle quality sub-score (0-100)
        close_pos = breakout_details.get("close_position_pct", 100.0)
        atr_exp = breakout_details.get("atr_expansion_ratio", 1.0)
        breakout_score = (close_pos * 0.7) + (min(2.0, atr_exp) / 2.0 * 30.0)
        breakout_score = max(0.0, min(100.0, breakout_score))
        
        # Relative Strength sub-score (cap at 100, normalized)
        rs_sub = min(100.0, max(0.0, rs_score * 2.0)) 
        
        score = (
            (stage_confidence * 0.25) +
            (vcp_score * 0.25) +
            (breakout_score * 0.20) +
            (rs_sub * 0.15) +
            (market_regime_health * 0.15)
        )
        
        overall_score = round(max(0.0, min(100.0, score)), 2)

        return {
            "score": overall_score,
            "components": {
                "stage_quality": round(stage_confidence, 2),
                "vcp_quality": round(vcp_score, 2),
                "breakout_quality": round(breakout_score, 2),
                "relative_strength": round(rs_sub, 2),
                "market_regime": round(market_regime_health, 2)
            }
        }
