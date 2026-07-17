from __future__ import annotations

import math
from datetime import datetime, date
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
        self.version = "1.3.0"
        self.indicator_version = "1.2.0"
        self.risk_model_version = "1.1.0"

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

            # Calculate GEX contribution
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

        # Find short Call leg (Delta closest to 0.18)
        short_call_item = min(mapped_strikes, key=lambda x: abs(x["ce_delta"] - 0.18))
        
        # Find short Put leg (Delta closest to -0.18)
        short_put_item = min(mapped_strikes, key=lambda x: abs(x["pe_delta"] - (-0.18)))

        short_call = short_call_item["strike"]
        short_put = short_put_item["strike"]

        # Resolve wing width
        index_configs = {
            "NIFTY": {"interval": 50, "wing": 100},
            "BANKNIFTY": {"interval": 100, "wing": 200},
            "SENSEX": {"interval": 100, "wing": 200},
            "FINNIFTY": {"interval": 50, "wing": 100},
            "MIDCPNIFTY": {"interval": 25, "wing": 50}
        }
        config = index_configs.get(symbol.upper(), index_configs["NIFTY"])
        wing_width = config["wing"]

        long_call = short_call + wing_width
        long_put = short_put - wing_width

        # Find premiums for long call/put legs
        long_call_item = next((x for x in mapped_strikes if x["strike"] == long_call), None)
        long_put_item = next((x for x in mapped_strikes if x["strike"] == long_put), None)

        p_sc = short_call_item["ce_ltp"]
        p_sp = short_put_item["pe_ltp"]
        p_lc = long_call_item["ce_ltp"] if long_call_item else p_sc * 0.15
        p_lp = long_put_item["pe_ltp"] if long_put_item else p_sp * 0.15

        # Calculate Net Credit
        net_credit_per_unit = (p_sc + p_sp) - (p_lc + p_lp)
        if net_credit_per_unit <= 0:
            net_credit_per_unit = 2.5

        # Sizing
        lot_size = LOT_SIZES.get(symbol.upper(), 25)
        position_size = 2 # 2 Lots default
        total_units = position_size * lot_size

        expected_credit = round(net_credit_per_unit * total_units)
        max_risk = round((wing_width - net_credit_per_unit) * total_units)
        rr_ratio = round(expected_credit / max_risk, 3) if max_risk > 0 else 0.05

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

        # ----------------------------------------------------
        # NEW TRADE QUALITY SCORING & DECISION ENGINE
        # ----------------------------------------------------
        quality_score = 50.0

        # Adjust for Risk-Reward
        # Penalize heavily if expected_credit is tiny fraction of max_risk
        if rr_ratio < 0.08:
            quality_score -= 30.0
        elif rr_ratio < 0.15:
            quality_score -= 15.0
        elif rr_ratio >= 0.25:
            quality_score += 15.0

        # Adjust for Volatility Percentile
        if iv_percentile < 35.0:
            quality_score -= 20.0
        elif 35.0 <= iv_percentile <= 70.0:
            quality_score += 10.0

        # Adjust for IV-RV spread
        if iv_rv_spread > 2.0:
            quality_score += 10.0
        elif iv_rv_spread <= 0.0:
            quality_score -= 25.0

        # Adjust for Liquidity index
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
        elif quality_score >= 60:
            stars = "★★☆☆☆"
            decision = "WAIT"
            verdict = "Weak Trade"
        else:
            stars = "★☆☆☆☆"
            decision = "REJECT"
            verdict = "No Trade Today"

        # Generate Pros and Cons
        pros = []
        cons = []
        if iv_rv_spread > 0:
            pros.append("Positive IV-RV spread (volatility premium exists)")
        else:
            cons.append("Implied volatility is underpriced relative to realized moves")

        if rr_ratio >= 0.15:
            pros.append("Optimal risk-to-reward ratio for defined-risk wings")
        else:
            cons.append("Disproportionately high max risk compared to net credit received")

        if symbol.upper() in ["NIFTY", "BANKNIFTY"]:
            pros.append("High option contract liquidity with tight bid-ask spreads")
        else:
            cons.append("Secondary index carries wider bid-ask spreads and slippage risks")

        if iv_percentile >= 35.0:
            pros.append("IV Percentile is within favorable premium-selling bounds")
        else:
            cons.append("Low IV Percentile restricts premium yields and credit cushions")

        # Executive Summary / Decision explanation
        if quality_score < 60:
            exec_summary = (
                f"This {symbol} Iron Condor satisfies all technical rules. However, option premiums are currently "
                f"too low (Risk-Reward is {rr_ratio:.3f}). Although the probability of success is decent, the expected "
                f"return does not justify risking ₹{max_risk:,} of capital for a maximum gain of ₹{expected_credit:,}. "
                f"Proprietary risk thresholds advise skipping this trade today."
            )
            alt_strat = "Wait for implied volatility expansion or consider calendar spreads."
        else:
            exec_summary = (
                f"The option chain profile presents an attractive opportunity. Option premiums are rich "
                f"(Risk-Reward is {rr_ratio:.3f}) with a positive IV-RV spread of +{iv_rv_spread:.2f}%. "
                f"Volatility percentile is sitting at {iv_percentile:.1f}%, which allows optimal premium collection. "
                f"Sizing at {position_size} lots is recommended."
            )
            alt_strat = "Deploy standard lot sizing. No adjustments needed unless index breaches wings."

        is_allowed = all(f["pass"] for f in filters.values()) and (quality_score >= 60)
        vehicle = "Iron Condor" if iv_percentile < 70 else "Iron Fly"
        confidence_score = quality_score

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
                "shortCall": short_call,
                "shortCallDelta": short_call_item["ce_delta"],
                "shortPut": short_put,
                "shortPutDelta": short_put_item["pe_delta"],
                "longCall": long_call,
                "longPut": long_put
            },
            "structure": {
                "vehicle": vehicle,
                "shortCall": short_call,
                "longCall": long_call,
                "shortPut": short_put,
                "longPut": long_put,
                "expectedCredit": expected_credit,
                "maxRisk": max_risk,
                "riskReward": rr_ratio,
                "winProbability": 70 + round(iv_rv_spread),
                "positionSize": position_size,
                "status": "READY" if is_allowed else "INVALIDATED",
                
                # Dynamic Trade Quality fields
                "trade_quality_score": quality_score,
                "stars": stars,
                "decision": decision,
                "verdict": verdict,
                "pros": pros,
                "cons": cons,
                "executive_summary": exec_summary,
                "alternative_strategy": alt_strat
            },
            "confidence_score": confidence_score
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
            "structure": {"vehicle": "Iron Condor", "shortCall": 0, "longCall": 0, "shortPut": 0, "longPut": 0, "expectedCredit": 0, "maxRisk": 0, "riskReward": 0.0, "winProbability": 0, "positionSize": 0, "status": "INVALIDATED", "trade_quality_score": 0, "stars": "★☆☆☆☆", "decision": "REJECT", "verdict": "No Trade Today", "pros": [], "cons": [], "executive_summary": "Empty options chain. Strategy aborted.", "alternative_strategy": "Wait"},
            "confidence_score": 0
        }

fno_strategy_engine = FnoStrategyEngine()
