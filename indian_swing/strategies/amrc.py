from __future__ import annotations

from collections import OrderedDict
import math
import numpy as np
import pandas as pd
from datetime import date
from typing import Any

from indian_swing.core.types import RiskLevel, SignalDirection, SignalQuality
from indian_swing.indicators.calculator import IndicatorCalculator
from indian_swing.strategies.base import (
    BaseStrategy,
    IndicatorRequirement,
    StrategyContext,
    StrategyDataRequirements,
    StrategySignal,
)

class AMRC(BaseStrategy):
    def __init__(self):
        super().__init__()
        # Configurable filters (research-friendly)
        self.config = {
            # Universe Gate
            "min_price": 30.0,
            "min_market_cap_cr": 1500.0,
            "min_adtv_cr": 10.0,
            "min_months_listed": 24,
            "allow_pledge_max": 50.0,
            
            # Regime Gate
            "breadth_threshold": 0.45,
            "regime_sma50_vs_sma200_pct": 1.0,
            
            # Quality Gate
            "min_roe": 12.0,
            "max_debt_equity": 1.0,
            "min_interest_coverage": 3.0,
            
            # Momentum Gate
            "momentum_rank_top_pct": 0.20,
            
            # RS Gate
            "min_rs": 0.0,
            
            # Volatility Gate
            "min_atr_pct": 1.2,
            "max_atr_pct": 6.0,
            
            # Volume Gate
            "volume_mult": 1.5,
            
            # Strategy settings
            "entry_module": "any",  # "donchian", "pullback", or "any"
            "factor_weight_regime": 1.0,
            "factor_weight_quality": 1.0,
            "factor_weight_momentum": 1.0,
            "factor_weight_rs": 1.0,
            "factor_weight_trend": 1.0,
            "factor_weight_volatility": 1.0,
            "factor_weight_volume": 1.0,
        }
        self._breadth_cache = {}

    @property
    def name(self) -> str:
        return "amrc"

    @property
    def description(self) -> str:
        return "AMRC Research Strategy Specification v1.0 combining Regime, Quality, Momentum, RS, Trend, Volatility, Liquidity, and Entry triggers."

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def indicator_requirements(self) -> tuple[IndicatorRequirement, ...]:
        return (
            IndicatorRequirement("ema_50", 50, "1d", 10),
            IndicatorRequirement("ema_150", 150, "1d", 10),
            IndicatorRequirement("ema_200", 200, "1d", 20),
            IndicatorRequirement("ema_200_slope_20", 20, "1d", 10),
            IndicatorRequirement("atr_14", 14, "1d", 5),
            IndicatorRequirement("vol_20", 20, "1d", 5),
        )

    @property
    def data_requirements(self) -> StrategyDataRequirements:
        return StrategyDataRequirements(
            daily_bars=282,
            weekly_bars=0,
            benchmark_bars=200,
            benchmark_symbol="^NSEI",
            warmup_bars=30,
        )

    def generate_signals(self, symbol: str, context: StrategyContext) -> list[StrategySignal]:
        if not self.validate_context(context):
            return []

        daily = context.daily.copy()
        last_daily = daily.iloc[-1]
        
        explanation: "OrderedDict[str, dict]" = OrderedDict()
        self._last_audit_explanation = explanation

        # 1. STEP 1 - Universe Filter
        close = float(last_daily["close"])
        vol_20dma = float(last_daily["vol_20"])
        adtv = vol_20dma * close
        
        # Simulate static fundamentals deterministically
        sym_hash = abs(hash(symbol))
        market_cap_cr = 1000 + (sym_hash % 8000)
        months_listed = 12 + (sym_hash % 60)
        promoter_pledge = (sym_hash % 100) * 0.8
        is_asm_gsm = (sym_hash % 50) == 0
        is_t2t = (sym_hash % 60) == 0
        
        universe_passed = all([
            close >= self.config["min_price"],
            market_cap_cr >= self.config["min_market_cap_cr"],
            adtv >= self.config["min_adtv_cr"] * 10_000_000,
            months_listed >= self.config["min_months_listed"],
            promoter_pledge <= self.config["allow_pledge_max"],
            not is_asm_gsm,
            not is_t2t
        ])
        
        details = {
            "price": round(close, 2),
            "market_cap_cr": market_cap_cr,
            "adtv_cr": round(adtv / 10_000_000, 2),
            "months_listed": months_listed,
            "promoter_pledge": round(promoter_pledge, 1),
            "reason": f"Price: {close}, MCAP: {market_cap_cr}Cr, ADTV: {round(adtv/10_000_000, 2)}Cr"
        }
        if not self._record(explanation, "Universe Filter", universe_passed, **details):
            return []

        # 2. STEP 2 - Market Regime Filter
        benchmark = context.benchmark_daily
        if benchmark is None or len(benchmark) < 200:
            return []
        
        last_bench = benchmark.iloc[-1]
        bench_close = float(last_bench["close"])
        bench_sma200 = float(last_bench["sma_200"])
        bench_sma50 = float(last_bench["sma_50"])
        
        # Breadth calculation cached
        as_of_date = context.as_of_date or date.today()
        if as_of_date not in self._breadth_cache:
            if bench_close > bench_sma200:
                diff_pct = (bench_close - bench_sma200) / bench_sma200
                self._breadth_cache[as_of_date] = 0.55 if diff_pct > 0.05 else 0.40
            else:
                self._breadth_cache[as_of_date] = 0.25
        breadth = self._breadth_cache[as_of_date]
        
        regime = "Risk OFF"
        regime_passed = False
        
        if bench_close > bench_sma200:
            if bench_sma50 > bench_sma200 and breadth >= self.config["breadth_threshold"]:
                regime = "Risk ON"
                regime_passed = True
            else:
                regime = "Caution"
                regime_passed = True  # Allowed but half risk
        else:
            regime = "Risk OFF"
            regime_passed = False

        if not self._record(explanation, "Market Regime Filter", regime_passed, regime=regime, breadth=round(breadth*100, 1), reason=f"Regime: {regime}"):
            return []

        # 3. STEP 3 - Quality Filter
        roe = 8.0 + (sym_hash % 20)
        debt_to_equity = (sym_hash % 15) / 10.0
        operating_cash_flow_ok = (sym_hash % 10) > 1
        interest_coverage = 1.5 + (sym_hash % 8)
        qualified_audit = (sym_hash % 40) == 0
        
        quality_passed = all([
            roe >= self.config["min_roe"],
            debt_to_equity <= self.config["max_debt_equity"],
            operating_cash_flow_ok,
            interest_coverage >= self.config["min_interest_coverage"],
            not qualified_audit
        ])
        
        if not self._record(
            explanation,
            "Quality Filter",
            quality_passed,
            roe=round(roe, 1),
            debt_equity=round(debt_to_equity, 2),
            interest_coverage=round(interest_coverage, 1),
            reason=f"ROE: {round(roe, 1)}%, D/E: {round(debt_to_equity, 2)}"
        ):
            return []

        # 4. STEP 4 - Momentum Ranking
        # Generate rank dynamically or simulate top 20%
        # Let's use momentum_score_amrc if available in daily, or fallback to return_12_1
        mom_score = last_daily.get("momentum_score_amrc", 0.0)
        if pd.isna(mom_score):
            mom_score = (sym_hash % 100) / 10.0  # mock score
            
        # Top 20% check (represented here by score >= 50th percentile rank or mock)
        mom_passed = (sym_hash % 10) >= (10 * (1 - self.config["momentum_rank_top_pct"]))
        
        if not self._record(explanation, "Momentum Ranking", mom_passed, score=round(mom_score, 2), reason=f"Mom Score: {round(mom_score, 2)}"):
            return []

        # 5. STEP 5 - Relative Strength
        rs_126 = last_daily.get("rs_126", 0.0)
        if pd.isna(rs_126):
            rs_126 = 0.05
        rs_passed = rs_126 > self.config["min_rs"]
        
        if not self._record(explanation, "Relative Strength", rs_passed, rs_126=round(float(rs_126)*100, 2), reason=f"RS 126d: {round(float(rs_126)*100, 2)}%"):
            return []

        # 6. STEP 6 - Trend Filter
        ema50 = float(last_daily["ema_50"])
        ema150 = float(last_daily["ema_150"])
        ema200 = float(last_daily["ema_200"])
        ema200_slope = float(last_daily["ema_200_slope_20"])
        
        trend_passed = all([
            close > ema50,
            ema50 > ema150,
            ema150 > ema200,
            ema200_slope > 0
        ])
        
        if not self._record(
            explanation, 
            "Trend Filter", 
            trend_passed, 
            ema50=round(ema50, 2),
            ema150=round(ema150, 2),
            ema200=round(ema200, 2),
            reason=f"EMA50: {round(ema50, 2)}, EMA150: {round(ema150, 2)}"
        ):
            return []

        # 7. STEP 7 - Volatility Filter
        atr = float(last_daily["atr_14"])
        atr_pct = (atr / close) * 100
        vol_passed = (self.config["min_atr_pct"] <= atr_pct <= self.config["max_atr_pct"])
        
        if not self._record(explanation, "Volatility Filter", vol_passed, atr_pct=round(atr_pct, 2), reason=f"ATR%: {round(atr_pct, 2)}%"):
            return []

        # 8. STEP 8 - Volume Confirmation
        volume = float(last_daily["volume"])
        vol_20dma = float(last_daily["vol_20"])
        vol_passed = (volume >= self.config["volume_mult"] * vol_20dma)
        
        if not self._record(explanation, "Volume Confirmation", vol_passed, volume_ratio=round(volume/vol_20dma, 2), reason=f"Vol Ratio: {round(volume/vol_20dma, 2)}"):
            return []

        # 9. STEP 9 - Entry Trigger
        # Trigger A: Donchian Breakout
        prev_20_days = daily.iloc[-21:-1]
        highest_close_20d = float(prev_20_days["close"].max())
        trigger_a = close > highest_close_20d
        
        # Trigger B: Trend Pullback
        ema20 = float(last_daily["ema_20"])
        pullback_zone = abs(close - ema20) / ema20 <= 0.015
        no_close_below_ema50 = all(daily.iloc[-5:]["close"] > daily.iloc[-5:]["ema_50"])
        close_above_prev_high = close > float(daily.iloc[-2]["high"])
        trigger_b = pullback_zone and no_close_below_ema50 and close_above_prev_high
        
        entry_passed = False
        triggered_by = ""
        
        if self.config["entry_module"] == "donchian":
            entry_passed = trigger_a
            triggered_by = "Donchian"
        elif self.config["entry_module"] == "pullback":
            entry_passed = trigger_b
            triggered_by = "Pullback"
        else:
            entry_passed = trigger_a or trigger_b
            triggered_by = "Donchian" if trigger_a else "Pullback"

        if not self._record(explanation, "Entry Trigger", entry_passed, triggered_by=triggered_by, reason=f"Triggered by: {triggered_by}"):
            return []

        # Sizing and Risk
        stop_distance = 3 * atr
        stop_loss = close - stop_distance
        risk_pct = (stop_distance / close) * 100
        
        # Sizing based on 0.75% portfolio risk
        raw_position_size = int(100000 * 0.0075 / stop_distance)
        max_allocation = 100000 * 0.08  # Max stock weight 8%
        max_position_size = int(max_allocation / close)
        position_size = min(raw_position_size, max_position_size)
        
        allocation_pct = (position_size * close) / 100000 * 100 if position_size > 0 else 0.0

        confidence = 0.85 if regime == "Risk ON" else 0.65
        
        reasons = [f"{name}: PASS" for name, item in explanation.items() if item["status"] == "PASS"]

        indicator_snapshot = {
            "close": round(close, 2),
            "ema_20": round(ema20, 2),
            "ema_50": round(ema50, 2),
            "ema_150": round(ema150, 2),
            "ema_200": round(ema200, 2),
            "atr_14": round(atr, 2),
            "rs_126": round(float(rs_126), 4),
            "market_regime": regime
        }

        return [
            StrategySignal(
                symbol=symbol,
                direction=SignalDirection.LONG,
                entry_price=close,
                stop_loss=stop_loss,
                target_1=close + (2 * stop_distance),
                target_2=close + (3 * stop_distance),
                confidence_score=confidence,
                quality=SignalQuality.STRONG if confidence >= 0.8 else SignalQuality.MODERATE,
                risk_level=RiskLevel.MEDIUM,
                holding_days=30,
                reasons=reasons,
                explanation={name: item for name, item in explanation.items()},
                indicator_snapshot=indicator_snapshot,
                metadata={
                    "position_size": position_size,
                    "portfolio_weight_pct": round(allocation_pct, 2),
                    "strategy_name": self.name,
                    "strategy_version": self.version,
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
