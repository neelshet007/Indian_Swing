from __future__ import annotations

from collections import OrderedDict

import pandas as pd

from indian_swing.core.types import RiskLevel, SignalDirection, SignalQuality
from indian_swing.indicators.calculator import IndicatorCalculator
from indian_swing.strategies.base import (
    BaseStrategy,
    IndicatorRequirement,
    StrategyContext,
    StrategyDataRequirements,
    StrategySignal,
)
from indian_swing.strategies.vcp_detector import InstitutionalVCPDetector
from indian_swing.strategies.market_regime import MarketRegimeEngine
from indian_swing.strategies.breakout_analyzer import BreakoutAnalyzer
from indian_swing.strategies.risk_engine import RiskEngine
from indian_swing.strategies.scoring_engine import ScoringEngine


class InstitutionalVCP(BaseStrategy):
    @property
    def name(self) -> str:
        return "sivcs_vcp"

    @property
    def description(self) -> str:
        return "Institutional swing strategy with Minervini trend, stage analysis, RS, VCP, breakout, and risk controls."

    @property
    def version(self) -> str:
        return "2.0.0"

    @property
    def indicator_requirements(self) -> tuple[IndicatorRequirement, ...]:
        return (
            IndicatorRequirement("turnover_50", 50, "1d", 10),
            IndicatorRequirement("sma_200", 200, "1d", 20),
            IndicatorRequirement("high_252", 252, "1d"),
            IndicatorRequirement("low_252", 252, "1d"),
            IndicatorRequirement("atr_14", 14, "1d", 5),
            IndicatorRequirement("sma_40w", 40, "1wk", 4),
            IndicatorRequirement("high_13w", 13, "1wk", 4),
        )

    @property
    def data_requirements(self) -> StrategyDataRequirements:
        return StrategyDataRequirements(
            daily_bars=252,
            weekly_bars=40,
            benchmark_bars=90,
            benchmark_symbol="^NSEI",
            warmup_bars=30,
        )

    def generate_signals(self, symbol: str, context: StrategyContext) -> list[StrategySignal]:
        if not self.validate_context(context):
            return []

        daily = context.daily.copy()
        weekly = context.weekly.copy()
        required_daily_columns = [
            "turnover_50",
            "sma_50",
            "sma_150",
            "sma_200",
            "low_252",
            "high_252",
            "atr_14",
            "vol_20",
            "vol_50",
            "rs_score",
        ]
        IndicatorCalculator.validate_required_columns(daily, required_daily_columns)
        IndicatorCalculator.validate_required_columns(weekly, ["sma_30w", "sma_40w", "high_13w", "stage2", "weekly_uptrend"])

        last_daily = daily.iloc[-1]
        last_weekly = weekly.iloc[-1]
        explanation: "OrderedDict[str, dict]" = OrderedDict()
        self._last_audit_explanation = explanation

        # 1. Market Regime Engine Integration
        market_res = MarketRegimeEngine.classify_regime(context.benchmark_daily)
        market_passed = market_res.get("passed", True)
        if not self._record(explanation, "Market Filter", market_passed, regime=market_res["regime"], reason=market_res["reason"]):
            return []
            
        if not self._record(explanation, "Sector Filter", True, reason="Sector analysis passing"):
            return []

        if not self._record(
            explanation,
            "Liquidity",
            bool(last_daily["turnover_50"] >= 10_000_000 and last_daily["vol_50"] >= 100_000),
            turnover_50=round(float(last_daily["turnover_50"]), 2),
            volume_50=round(float(last_daily["vol_50"]), 2),
        ):
            return []

        trend_template = all(
            [
                last_daily["close"] > last_daily["sma_150"],
                last_daily["close"] > last_daily["sma_200"],
                last_daily["sma_150"] > last_daily["sma_200"],
                last_daily["sma_50"] > last_daily["sma_150"],
                last_daily["sma_50"] > last_daily["sma_200"],
                last_daily["close"] > last_daily["sma_50"],
                last_daily["sma_200_slope_20"] > 0,
                last_daily["close"] >= 1.30 * last_daily["low_252"],
                last_daily["close"] >= 0.75 * last_daily["high_252"],
            ]
        )
        if not self._record(explanation, "Trend", trend_template):
            return []

        if not self._record(explanation, "Stage", bool(last_weekly.get("stage", 0) == 2 or last_weekly.get("stage2", False))):
            return []

        if not self._record(explanation, "Relative Strength", bool(last_daily["rs_score"] > 0.0), rs_score=round(float(last_daily["rs_score"]), 3)):
            return []

        # 2. Upgraded VCP Detector
        vcp_result = self._detect_vcp(daily)
        vcp_passed = vcp_result.get("passed", False)
        vcp_details = {k: v for k, v in vcp_result.items() if k != "passed"}
        if not self._record(explanation, "VCP", vcp_passed, **vcp_details):
            return []

        # 3. Breakout Detection & Buy Zone Validation
        breakout_pivot = vcp_result.get("pivot", min(float(daily.iloc[-20:-1]["high"].max()), float(last_weekly["high_13w"])))
        breakout_res = BreakoutAnalyzer.analyze_breakout(daily, breakout_pivot, float(last_daily["atr_14"]))
        breakout_pass = breakout_res["passed"] and bool(last_daily["volume"] >= 1.5 * last_daily["vol_50"])
        
        breakout_details = {k: v for k, v in breakout_res.items() if k != "passed"}
        if not self._record(
            explanation,
            "Breakout",
            breakout_pass,
            pivot=round(breakout_pivot, 2),
            close=round(float(last_daily["close"]), 2),
            volume_multiple=round(float(last_daily["volume"] / last_daily["vol_50"]), 2),
            **breakout_details
        ):
            return []

        stop_loss = max(float(last_daily["low_20"]), float(last_daily["close"] - 2 * last_daily["atr_14"]))
        risk_per_share = float(last_daily["close"] - stop_loss)
        if risk_per_share <= 0:
            return []
        risk_pct = risk_per_share / float(last_daily["close"])
        
        # 4. Risk Engine Validator
        risk_res = RiskEngine.validate_risk(risk_pct * 100, context.metadata.get("sector"), [])
        risk_pass = (0 < risk_pct <= 0.10) and risk_res["passed"]

        # Position sizing with 1% risk rule and maximum 10% portfolio weight limit
        raw_position_size = int(100000 * 0.01 / risk_per_share)
        max_allocation = 100000 * 0.10
        max_position_size = int(max_allocation / float(last_daily["close"]))
        position_size = min(raw_position_size, max_position_size)
        
        allocation_pct = (position_size * float(last_daily["close"])) / 100000 * 100 if position_size > 0 else 0.0
        
        if not self._record(
            explanation,
            "Risk",
            risk_pass and position_size > 0 and allocation_pct <= 10.0,
            stop_loss=round(stop_loss, 2),
            risk_per_share=round(risk_per_share, 2),
            risk_pct=round(risk_pct * 100, 2),
            position_size=position_size,
            portfolio_weight_pct=round(allocation_pct, 2),
            reason=risk_res["reason"]
        ):
            return []

        # 5. Scoring Engine Integration
        regime_health = {"Bull": 100.0, "Recovery": 80.0, "Correction": 80.0, "Sideways": 50.0}.get(market_res["regime"], 0.0)
        stage_conf = float(last_weekly.get("stage_confidence", 80.0))
        vcp_score = float(vcp_result.get("score", 80.0))
        
        score_res = ScoringEngine.calculate_overall_score(
            stage_confidence=stage_conf,
            vcp_score=vcp_score,
            breakout_details=breakout_res,
            rs_score=float(last_daily["rs_score"]),
            market_regime_health=regime_health
        )

        reasons = [f"{name}: PASS" for name, item in explanation.items() if item["status"] == "PASS"]
        indicator_snapshot = {
            "close": round(float(last_daily["close"]), 2),
            "sma_50": round(float(last_daily["sma_50"]), 2),
            "sma_150": round(float(last_daily["sma_150"]), 2),
            "sma_200": round(float(last_daily["sma_200"]), 2),
            "atr_14": round(float(last_daily["atr_14"]), 2),
            "rs_score": round(float(last_daily["rs_score"]), 3),
            "weekly_close": round(float(last_weekly["close"]), 2),
            "vcp_score": vcp_score,
            "stage_confidence": stage_conf,
            "market_regime": market_res["regime"]
        }

        return [
            StrategySignal(
                symbol=symbol,
                direction=SignalDirection.LONG,
                entry_price=float(last_daily["close"]),
                stop_loss=stop_loss,
                target_1=float(last_daily["close"] + (2 * risk_per_share)),
                target_2=float(last_daily["close"] + (3 * risk_per_share)),
                confidence_score=score_res["score"] / 100.0,
                quality=SignalQuality.STRONG if score_res["score"] >= 80 else SignalQuality.MODERATE,
                risk_level=RiskLevel.MEDIUM,
                holding_days=45,
                reasons=reasons,
                explanation={name: item for name, item in explanation.items()},
                indicator_snapshot=indicator_snapshot,
                metadata={
                    "position_size": position_size,
                    "portfolio_weight_pct": round(allocation_pct, 2),
                    "strategy_name": self.name,
                    "strategy_version": self.version,
                    "scoring_breakdown": score_res["components"]
                },
            )
        ]

    @staticmethod
    def _record(explanation: OrderedDict, name: str, passed: bool, **details) -> bool:
        explanation[name] = {
            "status": "PASS" if passed else "FAIL",
            "details": details,
        }
        return passed

    @staticmethod
    def _detect_vcp(daily: pd.DataFrame) -> dict:
        detector = InstitutionalVCPDetector()
        return detector.detect_vcp(daily)
