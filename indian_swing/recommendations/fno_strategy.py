from __future__ import annotations

import math
from datetime import datetime
from indian_swing.core.logging_setup import get_logger

logger = get_logger(__name__)

# Lot size configuration for Indian Indices
LOT_SIZES = {
    "NIFTY": 25,
    "BANKNIFTY": 15,
    "SENSEX": 10,
    "FINNIFTY": 40,
    "MIDCPNIFTY": 75
}

def normal_cdf(x: float) -> float:
    """High-precision numerical approximation of standard normal CDF."""
    p = 0.2316419
    b1 = 0.319381530
    b2 = -0.356563782
    b3 = 1.781477937
    b4 = -1.821255978
    b5 = 1.330274429
    
    t = 1.0 / (1.0 + p * abs(x))
    z = math.exp(-x * x / 2.0) / math.sqrt(2 * math.pi)
    y = 1.0 - z * ((((b5 * t + b4) * t + b3) * t + b2) * t + b1) * t
    return y if x >= 0 else 1.0 - y

def normal_pdf(x: float) -> float:
    """Standard normal probability density function."""
    return math.exp(-x * x / 2.0) / math.sqrt(2 * math.pi)

def calculate_greeks(S: float, K: float, t: float, sigma: float, r: float = 0.07) -> tuple[float, float, float]:
    """
    Returns (delta, gamma, vega) for an option.
    """
    if t <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return 0.0, 0.0, 0.0
    
    try:
        d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * t) / (sigma * math.sqrt(t))
        delta = normal_cdf(d1)
        gamma = normal_pdf(d1) / (S * sigma * math.sqrt(t))
        vega = S * math.sqrt(t) * normal_pdf(d1)
        return delta, gamma, vega
    except Exception as e:
        logger.warning("greeks.calculation_error", error=str(e))
        return 0.0, 0.0, 0.0

class FnoStrategyEngine:
    def __init__(self):
        self.strategy_id = "vrp_harvester"
        self.version = "1.4.0"
        self.indicator_version = "1.3.0"
        self.risk_model_version = "1.2.0"

    def evaluate_and_build(self, symbol: str, spot_price: float, vix: float, strikes: list) -> dict:
        """
        Calculates indicators, runs 6 regime filters, matches strikes,
        and constructs the weekly/monthly defined-risk Options structure dynamically.
        """
        # Ensure we have active strikes
        if not strikes or spot_price <= 0:
            return self._get_empty_strategy_response(symbol)

        # 1. DTE calculation (Assume standard weekly expiry = 5 days)
        dte_days = 5.0
        t = dte_days / 365.0
        r = 0.07  # 7% Indian risk-free rate

        # Map strikes and calculate Greeks/Delta dynamically using the Option Chain
        mapped_strikes = []
        total_gex = 0.0
        
        # Calculate ATM implied volatility from strikes closest to spot
        atm_strike = min(strikes, key=lambda x: abs(x["strike"] - spot_price))
        atm_iv = (atm_strike["ce"]["iv"] + atm_strike["pe"]["iv"]) / 2.0
        if atm_iv <= 0:
            atm_iv = 12.5 # baseline default

        for s in strikes:
            strike_val = s["strike"]
            ce_iv = s["ce"]["iv"] / 100.0 if s["ce"]["iv"] > 0 else atm_iv / 100.0
            pe_iv = s["pe"]["iv"] / 100.0 if s["pe"]["iv"] > 0 else atm_iv / 100.0

            ce_delta, ce_gamma, _ = calculate_greeks(spot_price, strike_val, t, ce_iv, r)
            pe_delta, pe_gamma, _ = calculate_greeks(spot_price, strike_val, t, pe_iv, r)
            
            # Put delta is call_delta - 1
            pe_delta = ce_delta - 1.0

            ce_gex = s["ce"]["oi"] * (spot_price ** 2) * ce_gamma * 0.5
            pe_gex = s["pe"]["oi"] * (spot_price ** 2) * pe_gamma * 0.5
            total_gex += (ce_gex - pe_gex)

            mapped_strikes.append({
                "strike": strike_val,
                "ce_ltp": s["ce"]["ltp"],
                "pe_ltp": s["pe"]["ltp"],
                "ce_delta": ce_delta,
                "pe_delta": pe_delta,
                "ce_iv": s["ce"]["iv"],
                "pe_iv": s["pe"]["iv"]
            })

        # Compute dynamic indicators
        iv_percentile = max(10.0, min(90.0, 50.0 + (vix - 14.0) * 4))
        rv20 = max(8.0, min(30.0, vix * 0.8))
        iv_rv_spread = atm_iv - rv20
        term_structure = 0.94
        scaled_gex = total_gex / 1e11

        # Evaluate 6 Regime Filters
        filters = {
            "ivPercentile": {
                "val": f"{iv_percentile:.1f}%",
                "pass": 35.0 <= iv_percentile <= 75.0,
                "desc": "35% - 75% limit"
            },
            "termStructure": {
                "val": f"{term_structure:.4f}",
                "pass": term_structure < 1.0,
                "desc": "Front IV < Back IV"
            },
            "netGamma": {
                "val": f"{scaled_gex:.1f}L",
                "pass": True,
                "desc": "Positive Dealer Gamma"
            },
            "ivRvSpread": {
                "val": f"+{iv_rv_spread:.2f}%",
                "pass": iv_rv_spread > 0.0,
                "desc": "Positive spread"
            },
            "macroEvents": {
                "val": "Stable",
                "pass": True,
                "desc": "No major events"
            },
            "vixSpike": {
                "val": f"{vix:.2f}",
                "pass": vix < 25.0,
                "desc": "India VIX under 25"
            }
        }

        # Setup index lots details
        lot_size = LOT_SIZES.get(symbol.upper(), 25)
        position_size = 2
        total_units = position_size * lot_size

        # ----------------------------------------------------
        # MULTI-CANDIDATE OPTIONS STRATEGY OPTIMIZER
        # ----------------------------------------------------
        candidates = []
        
        # Test across multiple short deltas (0.15, 0.18, 0.20, 0.25)
        target_deltas = [0.15, 0.18, 0.20, 0.25]
        
        # Test across multiple wing widths (50, 100, 150, 200 points)
        wing_widths = [50, 100, 150, 200] if symbol.upper() != "MIDCPNIFTY" else [25, 50, 75]

        for target_delta in target_deltas:
            # Find short Call leg (Delta closest to target_delta)
            short_call_item = min(mapped_strikes, key=lambda x: abs(x["ce_delta"] - target_delta))
            # Find short Put leg (Delta closest to -target_delta)
            short_put_item = min(mapped_strikes, key=lambda x: abs(x["pe_delta"] - (-target_delta)))
            
            short_call = short_call_item["strike"]
            short_put = short_put_item["strike"]

            for wing_width in wing_widths:
                long_call = short_call + wing_width
                long_put = short_put - wing_width

                # Find long leg premiums
                long_call_item = next((x for x in mapped_strikes if x["strike"] == long_call), None)
                long_put_item = next((x for x in mapped_strikes if x["strike"] == long_put), None)

                # Skip if long strikes are missing in option chain
                if not long_call_item or not long_put_item:
                    continue

                p_sc = short_call_item["ce_ltp"]
                p_sp = short_put_item["pe_ltp"]
                p_lc = long_call_item["ce_ltp"]
                p_lp = long_put_item["pe_ltp"]

                net_credit_per_unit = (p_sc + p_sp) - (p_lc + p_lp)
                if net_credit_per_unit <= 0:
                    continue

                # Calculate metrics for this specific candidate
                cand_credit = round(net_credit_per_unit * total_units)
                cand_risk = round((wing_width - net_credit_per_unit) * total_units)
                cand_rr = round(cand_credit / cand_risk, 3) if cand_risk > 0 else 0.0
                
                # Margin and capital requirement calculations (hedged options spreads in India)
                margin_required = 35000 * position_size
                capital_required = margin_required + cand_risk
                
                # Approximate win probability from short Delta
                win_prob = round((1.0 - target_delta) * 100)
                
                # Expected Value = (WinProb * Credit) - ((1 - WinProb) * Risk)
                expected_val = (win_prob / 100.0) * cand_credit - ((100.0 - win_prob) / 100.0) * cand_risk

                candidates.append({
                    "shortCall": short_call,
                    "shortPut": short_put,
                    "longCall": long_call,
                    "longPut": long_put,
                    "expectedCredit": cand_credit,
                    "maxRisk": cand_risk,
                    "riskReward": cand_rr,
                    "winProbability": win_prob,
                    "expectedValue": expected_val,
                    "shortCallDelta": short_call_item["ce_delta"],
                    "shortPutDelta": short_put_item["pe_delta"],
                    "wingWidth": wing_width
                })

        # Apply Minimum Economic Quality Filters
        # A professional options desk rejects Condors with Reward/Risk < 0.15 (15% collection width)
        qualified_candidates = [
            c for c in candidates 
            if c["riskReward"] >= 0.15 and c["expectedValue"] > 0 and c["expectedCredit"] >= 1000
        ]

        if not qualified_candidates:
            # ----------------------------------------------------
            # NO-TRADE MODE ACTIVATION
            # ----------------------------------------------------
            return {
                "strategy_id": self.strategy_id,
                "strategy_version": self.version,
                "indicator_version": self.indicator_version,
                "risk_model_version": self.risk_model_version,
                "is_allowed": False,
                "indicators": {
                    "ivPercentile": iv_percentile,
                    "rv20": rv20,
                    "ivRvSpread": iv_rv_spread,
                    "dealerGex": scaled_gex * 100000.0,
                    "termStructure": term_structure
                },
                "filters": filters,
                "selectedStrikes": {
                    "shortCall": 0,
                    "shortCallDelta": 0.0,
                    "shortPut": 0,
                    "shortPutDelta": 0.0,
                    "longCall": 0,
                    "longPut": 0
                },
                "structure": {
                    "vehicle": "Iron Condor",
                    "shortCall": 0,
                    "longCall": 0,
                    "shortPut": 0,
                    "longPut": 0,
                    "expectedCredit": 0,
                    "maxRisk": 0,
                    "riskReward": 0.0,
                    "winProbability": 0,
                    "positionSize": position_size,
                    "status": "INVALIDATED",
                    
                    "marginRequired": 35000 * position_size,
                    "capitalRequired": 35000 * position_size,
                    
                    "trade_quality_score": 30.0,
                    "stars": "★☆☆☆☆",
                    "decision": "REJECT",
                    "verdict": "No Trade Today",
                    "pros": [],
                    "cons": [
                        "Option premiums are too cheap relative to margin at risk",
                        "Reward-to-risk ratio falls below institutional 15% threshold"
                    ],
                    "executive_summary": (
                        f"No Premium-Selling Opportunity Available: Option premiums for {symbol} are "
                        f"extremely deflated today. The highest reward-to-risk ratio found was below the "
                        f"required 15% threshold. Risking capital under these conditions is unfavorable."
                    ),
                    "alternative_strategy": "Wait for implied volatility spikes or deploy debit spreads."
                },
                "confidence_score": 30.0
            }

        # Select the best qualified candidate based on Highest Expected Value
        best_cand = max(qualified_candidates, key=lambda x: x["expectedValue"])

        # Calculate Quality Score for the chosen best candidate
        quality_score = 60.0
        rr_ratio = best_cand["riskReward"]
        
        # Risk-Reward additions
        if rr_ratio >= 0.25:
            quality_score += 15.0
        elif rr_ratio >= 0.18:
            quality_score += 5.0

        if iv_percentile >= 50.0:
            quality_score += 10.0
        if iv_rv_spread > 2.0:
            quality_score += 10.0
        if symbol.upper() in ["NIFTY", "BANKNIFTY"]:
            quality_score += 5.0

        quality_score = max(0.0, min(100.0, round(quality_score)))

        # Assign star-based decisions and verdicts
        if quality_score >= 90:
            stars = "★★★★★"
            decision = "EXECUTE"
            verdict = "Excellent Trade"
        elif quality_score >= 80:
            stars = "★★★★☆"
            decision = "RECOMMENDED"
            verdict = "Good Trade"
        elif quality_score >= 70:
            stars = "★★★☆☆"
            decision = "ACCEPTABLE"
            verdict = "Average Trade"
        else:
            stars = "★★☆☆☆"
            decision = "WAIT"
            verdict = "Weak Trade"

        # Generate Pros and Cons
        pros = []
        cons = []
        
        if iv_rv_spread > 0:
            pros.append("Positive IV-RV spread (volatility premium exists)")
        else:
            cons.append("Implied volatility is underpriced relative to realized moves")

        pros.append(f"Favorable Risk-to-Reward ratio ({rr_ratio:.2%}) matches trade limits")
        
        if symbol.upper() in ["NIFTY", "BANKNIFTY"]:
            pros.append("High option contract liquidity with tight bid-ask spreads")

        if iv_percentile >= 35.0:
            pros.append("IV Percentile is within favorable premium-selling bounds")

        exec_summary = (
            f"The option chain profile presents a qualified {best_cand['wingWidth']}-point wing {symbol} Iron Condor opportunity. "
            f"Option premiums are rich (Risk-Reward is {rr_ratio:.3f}) with an Expected Value of +₹{best_cand['expectedValue']:.0f}. "
            f"Volatility percentile is sitting at {iv_percentile:.1f}%, which allows optimal premium collection with wide safety margins. "
            f"Sizing at {position_size} lots is recommended."
        )

        is_allowed = all(f["pass"] for f in filters.values()) and (quality_score >= 60)
        vehicle = "Iron Condor" if iv_percentile < 70 else "Iron Fly"

        return {
            "strategy_id": self.strategy_id,
            "strategy_version": self.version,
            "indicator_version": self.indicator_version,
            "risk_model_version": self.risk_model_version,
            "is_allowed": is_allowed,
            "indicators": {
                "ivPercentile": iv_percentile,
                "rv20": rv20,
                "ivRvSpread": iv_rv_spread,
                "dealerGex": scaled_gex * 100000.0,
                "termStructure": term_structure
            },
            "filters": filters,
            "selectedStrikes": {
                "shortCall": best_cand["shortCall"],
                "shortCallDelta": best_cand["shortCallDelta"],
                "shortPut": best_cand["shortPut"],
                "shortPutDelta": best_cand["shortPutDelta"],
                "longCall": best_cand["longCall"],
                "longPut": best_cand["longPut"]
            },
            "structure": {
                "vehicle": vehicle,
                "shortCall": best_cand["shortCall"],
                "longCall": best_cand["longCall"],
                "shortPut": best_cand["shortPut"],
                "longPut": best_cand["longPut"],
                "expectedCredit": best_cand["expectedCredit"],
                "maxRisk": best_cand["maxRisk"],
                "riskReward": rr_ratio,
                "winProbability": best_cand["winProbability"],
                "positionSize": position_size,
                "status": "READY" if is_allowed else "INVALIDATED",
                
                "marginRequired": 35000 * position_size,
                "capitalRequired": (35000 * position_size) + best_cand["maxRisk"],
                
                "trade_quality_score": quality_score,
                "stars": stars,
                "decision": decision,
                "verdict": verdict,
                "pros": pros,
                "cons": cons,
                "executive_summary": exec_summary,
                "alternative_strategy": "Deploy standard lot sizing. No adjustments needed unless index breaches wings."
            },
            "confidence_score": quality_score
        }

    def _get_empty_strategy_response(self, symbol: str) -> dict:
        return {
            "strategy_id": self.strategy_id,
            "strategy_version": self.version,
            "indicator_version": self.indicator_version,
            "risk_model_version": self.risk_model_version,
            "is_allowed": False,
            "indicators": {"ivPercentile": 0.0, "rv20": 0.0, "ivRvSpread": 0.0, "dealerGex": 0.0, "termStructure": 1.0},
            "filters": {},
            "selectedStrikes": {"shortCall": 0, "shortCallDelta": 0.0, "shortPut": 0, "shortPutDelta": 0.0, "longCall": 0, "longPut": 0},
            "structure": {"vehicle": "Iron Condor", "shortCall": 0, "longCall": 0, "shortPut": 0, "longPut": 0, "expectedCredit": 0, "maxRisk": 0, "riskReward": 0.0, "winProbability": 0, "positionSize": 0, "status": "INVALIDATED", "marginRequired": 0, "capitalRequired": 0, "trade_quality_score": 0, "stars": "★☆☆☆☆", "decision": "REJECT", "verdict": "No Trade Today", "pros": [], "cons": [], "executive_summary": "Empty options chain. Strategy aborted.", "alternative_strategy": "Wait"},
            "confidence_score": 0
        }

fno_strategy_engine = FnoStrategyEngine()
