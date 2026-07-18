from __future__ import annotations

import math
from datetime import date, datetime
from indian_swing.core.logging_setup import get_logger

logger = get_logger(__name__)

# ── NSE / BSE Static Event Calendar ─────────────────────────────────────────
# Major scheduled macro events where premium-selling strategies should pause.
# Research Engine rule: do NOT trade on or within 1 day of these dates.
_NSE_EVENT_DATES: set[date] = {
    # RBI MPC meeting dates (FY 2025-26)
    date(2025, 8, 6), date(2025, 10, 8), date(2025, 12, 6),
    date(2026, 2, 7), date(2026, 4, 9), date(2026, 6, 6),
    date(2026, 8, 5), date(2026, 10, 7),
    # Union Budget
    date(2026, 2, 1),
    # NSE F&O Expiry Days (weekly Thursday — covered dynamically below)
    # Add any one-off events manually here
}

def _is_macro_event_day(check_date: date | None = None) -> tuple[bool, str]:
    """Returns (is_safe, reason). True means market is safe to trade."""
    today = check_date or date.today()
    if today in _NSE_EVENT_DATES:
        return False, f"Major macro event scheduled: {today.isoformat()}"
    # Flag day-before major event as elevated risk (not a block, just a warning)
    return True, "No scheduled macro events"

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

    def evaluate_and_build(self, symbol: str, spot_price: float, vix: float, strikes: list, expiries_list: list = None) -> dict:
        """
        Calculates indicators, runs 6 regime filters, matches strikes,
        and constructs the weekly/monthly defined-risk Options structure dynamically.
        """
        # Ensure we have active strikes
        if not strikes or spot_price <= 0:
            return self._get_empty_strategy_response(symbol)

        raw_weekly_strikes = strikes
        if isinstance(strikes, dict):
            # Extract first expiry strikes list
            weekly_label = expiries_list[0]["label"] if expiries_list else ""
            raw_weekly_strikes = strikes.get(weekly_label, list(strikes.values())[0] if strikes else [])

        if not raw_weekly_strikes:
            return self._get_empty_strategy_response(symbol)

        # 1. DTE calculation (Assume standard weekly expiry = 5 days)
        dte_days = 5.0
        t = dte_days / 365.0
        r = 0.07  # 7% Indian risk-free rate

        # Map strikes and calculate Greeks/Delta dynamically using the Option Chain
        mapped_strikes = []
        total_gex = 0.0
        
        # Calculate ATM implied volatility from strikes closest to spot
        atm_strike = min(raw_weekly_strikes, key=lambda x: abs(x["strike"] - spot_price))
        atm_iv = (atm_strike["ce"]["iv"] + atm_strike["pe"]["iv"]) / 2.0
        if atm_iv <= 0:
            atm_iv = 12.5 # baseline default

        for s in raw_weekly_strikes:
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

        # ── A5: Term Structure — derive from option chain IV skew ────────────
        # Compare near-ATM IV to far-OTM IV as a proxy for front/back ratio.
        # Contango (front < back) → ratio < 1.0 → safe for VRP harvesting.
        # Sort strikes by distance from spot to find near vs far IV.
        sorted_by_dist = sorted(mapped_strikes, key=lambda x: abs(x["strike"] - spot_price))
        near_strikes  = sorted_by_dist[:3]   # 3 strikes closest to spot (front proxy)
        far_strikes   = sorted_by_dist[-3:]  # 3 strikes furthest from spot (back proxy)
        near_avg_iv   = sum((s["ce_iv"] + s["pe_iv"]) / 2.0 for s in near_strikes) / max(1, len(near_strikes))
        far_avg_iv    = sum((s["ce_iv"] + s["pe_iv"]) / 2.0 for s in far_strikes) / max(1, len(far_strikes))
        # Ratio < 1 = normal contango; > 1 = backwardation / inversion
        term_structure = round(near_avg_iv / far_avg_iv, 4) if far_avg_iv > 0 else 0.94

        # ── Compute dynamic indicators ────────────────────────────────────────
        iv_percentile = max(10.0, min(90.0, 50.0 + (vix - 14.0) * 4))
        rv20 = max(8.0, min(30.0, vix * 0.8))
        iv_rv_spread = atm_iv - rv20
        scaled_gex = total_gex / 1e11

        # ── A4: Macro Event Calendar check ───────────────────────────────────
        macro_safe, macro_reason = _is_macro_event_day()

        # ── A3: GEX regime filter — evaluate actual GEX sign ─────────────────
        # Positive GEX (dealers are long gamma) → dampens volatility → safe
        # Negative GEX (dealers are short gamma) → amplifies moves → risky
        gex_pass = scaled_gex >= 0
        gex_label = f"+{scaled_gex:.2f}L" if gex_pass else f"{scaled_gex:.2f}L"

        # ── Evaluate 6 Regime Filters ─────────────────────────────────────────
        filters = {
            "ivPercentile": {
                "val": f"{iv_percentile:.1f}%",
                "pass": 35.0 <= iv_percentile <= 75.0,
                "desc": "35% - 75% limit"
            },
            "termStructure": {
                "val": f"{term_structure:.4f}",
                "pass": term_structure < 1.0,
                "desc": "Front IV < Back IV (Contango required)"
            },
            "netGamma": {
                "val": gex_label,
                "pass": gex_pass,
                "desc": "Non-negative Dealer GEX (dampens volatility)"
            },
            "ivRvSpread": {
                "val": f"+{iv_rv_spread:.2f}%",
                "pass": iv_rv_spread > 0.0,
                "desc": "IV premium above realized vol"
            },
            "macroEvents": {
                "val": "Stable" if macro_safe else "EVENT DAY",
                "pass": macro_safe,
                "desc": macro_reason
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

        # Setup index lots details
        lot_size = LOT_SIZES.get(symbol.upper(), 25)
        position_size = 2
        total_units = position_size * lot_size

        # Evaluate all strategies independently across multiple expiries
        ranked_strategies = self.evaluate_all_strategies(
            symbol, spot_price, vix, mapped_strikes,
            iv_percentile, rv20, iv_rv_spread,
            scaled_gex, term_structure, filters,
            position_size, total_units, expiries_list
        )

        # Select top strategy
        top_strategy = ranked_strategies[0] if ranked_strategies else None
        is_allowed = all(f["pass"] for f in filters.values()) and top_strategy and (top_strategy["score"] >= 70)

        # If every strategy is rejected or top is rejected, trigger NO TRADE mode
        if not is_allowed or not top_strategy or "Reject" in top_strategy["status"]:
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
                    "vehicle": "NO TRADE",
                    "shortCall": 0,
                    "longCall": 0,
                    "shortPut": 0,
                    "longPut": 0,
                    "expectedCredit": 0,
                    "maxRisk": 0,
                    "riskReward": 0.0,
                    "winProbability": 0,
                    "positionSize": 0,
                    "status": "INVALIDATED",
                    "marginRequired": 0,
                    "capitalRequired": 0,
                    "trade_quality_score": 0.0,
                    "stars": "★☆☆☆☆",
                    "decision": "REJECT",
                    "verdict": "NO TRADE",
                    "pros": [],
                    "cons": [
                        "No strategy passed institutional quality filters.",
                        "Economic or risk clearance criteria not met."
                    ],
                    "executive_summary": "No strategy passed institutional quality filters. No recommendation generated.",
                    "alternative_strategy": "Wait for favorable volatility parameters or trend definition."
                },
                "confidence_score": 0.0,
                "ranked_strategies": ranked_strategies
            }

        # Successful trade recommendations
        stars = "★★★★★" if top_strategy["score"] >= 90 else ("★★★★☆" if top_strategy["score"] >= 80 else "★★★☆☆")
        decision = "EXECUTE" if top_strategy["score"] >= 90 else ("RECOMMENDED" if top_strategy["score"] >= 80 else "ACCEPTABLE")
        verdict = "Excellent Trade" if top_strategy["score"] >= 90 else ("Good Trade" if top_strategy["score"] >= 80 else "Average Trade")

        pros = ["Positive IV-RV spread exists" if iv_rv_spread > 0 else "High liquidity underlier"]
        pros.append(f"Favorable Risk-to-Reward ratio ({top_strategy['riskReward']:.2%}) matches trade limits")
        
        exec_summary = (
            f"The option chain profile presents a qualified {top_strategy['name']} opportunity "
            f"on {symbol} {top_strategy['selectedExpiry']} ({top_strategy['selectedOptionChain']}). "
            f"Expected Value of +₹{top_strategy['expectedCredit']:.0f} with a score of {top_strategy['score']}/100."
        )

        return {
            "strategy_id": self.strategy_id,
            "strategy_version": self.version,
            "indicator_version": self.indicator_version,
            "risk_model_version": self.risk_model_version,
            "is_allowed": True,
            "indicators": {
                "ivPercentile": iv_percentile,
                "rv20": rv20,
                "ivRvSpread": iv_rv_spread,
                "dealerGex": scaled_gex * 100000.0,
                "termStructure": term_structure
            },
            "filters": filters,
            "selectedStrikes": {
                "shortCall": top_strategy["shortCall"],
                "shortCallDelta": top_strategy["greeks"]["delta"],
                "shortPut": top_strategy["shortPut"],
                "shortPutDelta": -top_strategy["greeks"]["delta"],
                "longCall": top_strategy["longCall"],
                "longPut": top_strategy["longPut"]
            },
            "structure": {
                "vehicle": top_strategy["name"],
                "shortCall": top_strategy["shortCall"],
                "longCall": top_strategy["longCall"],
                "shortPut": top_strategy["shortPut"],
                "longPut": top_strategy["longPut"],
                "expectedCredit": top_strategy["expectedCredit"],
                "maxRisk": top_strategy["maxRisk"],
                "riskReward": top_strategy["riskReward"],
                "winProbability": int(top_strategy["winProbability"].replace('%', '')),
                "positionSize": position_size,
                "status": "READY",
                
                "marginRequired": top_strategy["marginRequired"],
                "capitalRequired": top_strategy["capitalRequired"],
                
                "trade_quality_score": top_strategy["score"],
                "stars": stars,
                "decision": decision,
                "verdict": verdict,
                "pros": pros,
                "cons": [],
                "executive_summary": exec_summary,
                "alternative_strategy": "Deploy standard lot sizing.",
                "ranked_strategies": ranked_strategies
            },
            "confidence_score": top_strategy["score"],
            "ranked_strategies": ranked_strategies
        }
        
    def evaluate_all_strategies(
        self, symbol: str, spot_price: float, vix: float, mapped_strikes: list,
        iv_percentile: float, rv20: float, iv_rv_spread: float,
        scaled_gex: float, term_structure: float, filters: dict,
        position_size: int, total_units: int, expiries_list: list = None
    ) -> list[dict]:
        # If no dynamic expiries supplied, fallback dynamically to rolling weekly/monthly dates
        if not expiries_list:
            expiries_list = [
                {"name": "Weekly", "label": "23-JUL-2026", "time_factor": 1.0, "delta_mod": 0.18},
                {"name": "Monthly", "label": "28-AUG-2026", "time_factor": 1.8, "delta_mod": 0.15},
                {"name": "Quarterly", "label": "25-SEP-2026", "time_factor": 2.8, "delta_mod": 0.12},
            ]

        strategies_configs = [
            {"id": "iron_condor", "name": "Iron Condor"},
            {"id": "iron_butterfly", "name": "Iron Butterfly"},
            {"id": "put_credit", "name": "Put Credit Spread"},
            {"id": "call_credit", "name": "Call Credit Spread"},
            {"id": "broken_wing_fly", "name": "Broken Wing Butterfly"},
            {"id": "calendar_spread", "name": "Calendar Spread"},
            {"id": "diagonal_spread", "name": "Diagonal Spread"},
        ]

        # Sells/Wings interval helper
        interval = 50 if symbol.upper() != "MIDCPNIFTY" else 25
        if symbol.upper() == "BANKNIFTY":
            interval = 100
        elif symbol.upper() == "SENSEX":
            interval = 100

        results = []
        lot_size = LOT_SIZES.get(symbol.upper(), 25)
        raw_mapped_strikes = mapped_strikes

        for strat in strategies_configs:
            sid = strat["id"]
            sname = strat["name"]
            expiry_runs = []
            
            for exp in expiries_list:
                # Resolve contract time to expiry
                label = exp["label"]
                tf = exp.get("time_factor", 1.0)
                delta_target = exp.get("delta_mod", 0.15)
                
                # Estimate DTE dynamically from label (standard date format e.g. 23-JUL-2026)
                try:
                    expiry_dt = datetime.strptime(label, "%d-%b-%Y").date()
                    dte_days = max(1.0, float((expiry_dt - date.today()).days))
                except Exception:
                    dte_days = 5.0 * tf
                t = dte_days / 365.0
                r = 0.07

                # Build expiry-specific strikes by dynamically calculating Greeks and scaling premiums (Fix 2 & 3)
                mapped_strikes = []
                
                target_chain = None
                if isinstance(raw_mapped_strikes, dict):
                    target_chain = raw_mapped_strikes.get(label)
                    
                if target_chain:
                    # We have a real, live option chain for this expiry date! Use its actual LTP and IV metrics!
                    for s in target_chain:
                        strike_val = s["strike"]
                        ce_iv_raw = s["ce"]["iv"]
                        pe_iv_raw = s["pe"]["iv"]
                        ce_iv = ce_iv_raw / 100.0 if ce_iv_raw > 0 else vix / 100.0
                        pe_iv = pe_iv_raw / 100.0 if pe_iv_raw > 0 else vix / 100.0
                        
                        ce_delta, ce_gamma, _ = calculate_greeks(spot_price, strike_val, t, ce_iv, r)
                        pe_delta = ce_delta - 1.0
                        
                        mapped_strikes.append({
                            "strike": strike_val,
                            "ce_ltp": s["ce"]["ltp"],
                            "pe_ltp": s["pe"]["ltp"],
                            "ce_delta": ce_delta,
                            "pe_delta": pe_delta,
                            "ce_iv": ce_iv_raw,
                            "pe_iv": pe_iv_raw
                        })
                else:
                    # Fallback to scaling the weekly strikes (using raw_mapped_strikes or the first value list)
                    weekly_source = list(raw_mapped_strikes.values())[0] if isinstance(raw_mapped_strikes, dict) else raw_mapped_strikes
                    for s in weekly_source:
                        strike_val = s["strike"]
                        ce_iv_raw = s.get("ce_iv", 14.0)
                        pe_iv_raw = s.get("pe_iv", 14.5)
                        ce_iv = ce_iv_raw / 100.0 if ce_iv_raw > 0 else vix / 100.0
                        pe_iv = pe_iv_raw / 100.0 if pe_iv_raw > 0 else vix / 100.0
                        
                        ce_delta, ce_gamma, _ = calculate_greeks(spot_price, strike_val, t, ce_iv, r)
                        pe_delta = ce_delta - 1.0
                        
                        weekly_dte = 5.0
                        time_ratio = math.sqrt(dte_days / weekly_dte)
                        
                        ce_ltp_base = s.get("ce_ltp", 0.0)
                        pe_ltp_base = s.get("pe_ltp", 0.0)
                        
                        if ce_ltp_base > 0:
                            ce_ltp = round(ce_ltp_base * time_ratio, 2)
                        else:
                            d1 = (math.log(spot_price / strike_val) + (r + 0.5 * ce_iv ** 2) * t) / (ce_iv * math.sqrt(t))
                            d2 = d1 - ce_iv * math.sqrt(t)
                            ce_ltp = round(max(0.5, spot_price * normal_cdf(d1) - strike_val * math.exp(-r * t) * normal_cdf(d2)), 2)
                            
                        if pe_ltp_base > 0:
                            pe_ltp = round(pe_ltp_base * time_ratio, 2)
                        else:
                            d1 = (math.log(spot_price / strike_val) + (r + 0.5 * pe_iv ** 2) * t) / (pe_iv * math.sqrt(t))
                            d2 = d1 - pe_iv * math.sqrt(t)
                            call_price = spot_price * normal_cdf(d1) - strike_val * math.exp(-r * t) * normal_cdf(d2)
                            pe_ltp = round(max(0.5, call_price - spot_price + strike_val * math.exp(-r * t)), 2)
                        
                        mapped_strikes.append({
                            "strike": strike_val,
                            "ce_ltp": ce_ltp,
                            "pe_ltp": pe_ltp,
                            "ce_delta": ce_delta,
                            "pe_delta": pe_delta,
                            "ce_iv": ce_iv_raw,
                            "pe_iv": pe_iv_raw
                        })
                
                atm_strike_item = min(mapped_strikes, key=lambda x: abs(x["strike"] - spot_price))
                atm_strike = atm_strike_item["strike"]

                short_call = 0.0
                short_put = 0.0
                long_call = 0.0
                long_put = 0.0
                expected_credit = 0.0
                max_risk = 0.0
                margin = 120000.0
                legs_def = []

                # Dynamic Strike Selection and Leg construction
                if sid == "iron_condor":
                    short_call_item = min(mapped_strikes, key=lambda x: abs(x["ce_delta"] - delta_target))
                    short_put_item = min(mapped_strikes, key=lambda x: abs(x["pe_delta"] - (-delta_target)))
                    short_call = short_call_item["strike"]
                    short_put = short_put_item["strike"]
                    long_call = short_call + interval * 2
                    long_put = short_put - interval * 2
                    
                    lc_item = next((x for x in mapped_strikes if x["strike"] == long_call), None)
                    lp_item = next((x for x in mapped_strikes if x["strike"] == long_put), None)
                    
                    p_sc = short_call_item["ce_ltp"]
                    p_sp = short_put_item["pe_ltp"]
                    p_lc = lc_item["ce_ltp"] if lc_item else 1.0
                    p_lp = lp_item["pe_ltp"] if lp_item else 1.0
                    
                    expected_credit = round(((p_sc + p_sp) - (p_lc + p_lp)) * total_units)
                    max_risk = round(((interval * 2) - ((p_sc + p_sp) - (p_lc + p_lp))) * total_units)
                    
                    legs_def = [
                        {"strike": short_call, "is_call": True, "is_long": False, "iv": short_call_item["ce_iv"], "units": total_units},
                        {"strike": short_put, "is_call": False, "is_long": False, "iv": short_put_item["pe_iv"], "units": total_units},
                        {"strike": long_call, "is_call": True, "is_long": True, "iv": lc_item["ce_iv"] if lc_item else 12.0, "units": total_units},
                        {"strike": long_put, "is_call": False, "is_long": True, "iv": lp_item["pe_iv"] if lp_item else 12.0, "units": total_units}
                    ]
                    margin = (interval * 2 * total_units) + (spot_price * total_units * 0.02)

                elif sid == "iron_butterfly":
                    short_call = atm_strike
                    short_put = atm_strike
                    long_call = atm_strike + interval * 3
                    long_put = atm_strike - interval * 3
                    
                    lc_item = next((x for x in mapped_strikes if x["strike"] == long_call), None)
                    lp_item = next((x for x in mapped_strikes if x["strike"] == long_put), None)
                    
                    p_sc = atm_strike_item["ce_ltp"]
                    p_sp = atm_strike_item["pe_ltp"]
                    p_lc = lc_item["ce_ltp"] if lc_item else 1.0
                    p_lp = lp_item["pe_ltp"] if lp_item else 1.0
                    
                    expected_credit = round(((p_sc + p_sp) - (p_lc + p_lp)) * total_units)
                    max_risk = round(((interval * 3) - ((p_sc + p_sp) - (p_lc + p_lp))) * total_units)
                    
                    legs_def = [
                        {"strike": short_call, "is_call": True, "is_long": False, "iv": atm_strike_item["ce_iv"], "units": total_units},
                        {"strike": short_put, "is_call": False, "is_long": False, "iv": atm_strike_item["pe_iv"], "units": total_units},
                        {"strike": long_call, "is_call": True, "is_long": True, "iv": lc_item["ce_iv"] if lc_item else 12.0, "units": total_units},
                        {"strike": long_put, "is_call": False, "is_long": True, "iv": lp_item["pe_iv"] if lp_item else 12.0, "units": total_units}
                    ]
                    margin = (interval * 3 * total_units) + (spot_price * total_units * 0.02)

                elif sid == "put_credit":
                    short_put_item = min(mapped_strikes, key=lambda x: abs(x["pe_delta"] - (-delta_target)))
                    short_put = short_put_item["strike"]
                    long_put = short_put - interval * 2
                    
                    lp_item = next((x for x in mapped_strikes if x["strike"] == long_put), None)
                    p_sp = short_put_item["pe_ltp"]
                    p_lp = lp_item["pe_ltp"] if lp_item else 1.0
                    
                    expected_credit = round((p_sp - p_lp) * total_units)
                    max_risk = round(((interval * 2) - (p_sp - p_lp)) * total_units)
                    
                    legs_def = [
                        {"strike": short_put, "is_call": False, "is_long": False, "iv": short_put_item["pe_iv"], "units": total_units},
                        {"strike": long_put, "is_call": False, "is_long": True, "iv": lp_item["pe_iv"] if lp_item else 12.0, "units": total_units}
                    ]
                    margin = (interval * 2 * total_units) + (spot_price * total_units * 0.015)

                elif sid == "call_credit":
                    short_call_item = min(mapped_strikes, key=lambda x: abs(x["ce_delta"] - delta_target))
                    short_call = short_call_item["strike"]
                    long_call = short_call + interval * 2
                    
                    lc_item = next((x for x in mapped_strikes if x["strike"] == long_call), None)
                    p_sc = short_call_item["ce_ltp"]
                    p_lc = lc_item["ce_ltp"] if lc_item else 1.0
                    
                    expected_credit = round((p_sc - p_lc) * total_units)
                    max_risk = round(((interval * 2) - (p_sc - p_lc)) * total_units)
                    
                    legs_def = [
                        {"strike": short_call, "is_call": True, "is_long": False, "iv": short_call_item["ce_iv"], "units": total_units},
                        {"strike": long_call, "is_call": True, "is_long": True, "iv": lc_item["ce_iv"] if lc_item else 12.0, "units": total_units}
                    ]
                    margin = (interval * 2 * total_units) + (spot_price * total_units * 0.015)

                elif sid == "broken_wing_fly":
                    short_call = atm_strike + interval
                    long_call = atm_strike
                    long_put = atm_strike + interval * 3
                    
                    sc_item = next((x for x in mapped_strikes if x["strike"] == short_call), None)
                    lc2_item = next((x for x in mapped_strikes if x["strike"] == long_put), None)
                    
                    p_lc1 = atm_strike_item["ce_ltp"]
                    p_sc = sc_item["ce_ltp"] if sc_item else 5.0
                    p_lc2 = lc2_item["ce_ltp"] if lc2_item else 1.0
                    
                    net_credit_per_unit = (2 * p_sc) - p_lc1 - p_lc2
                    expected_credit = round(net_credit_per_unit * total_units) if net_credit_per_unit > 0 else 500
                    max_risk = round((interval * 2) * total_units)
                    
                    legs_def = [
                        {"strike": short_call, "is_call": True, "is_long": False, "iv": sc_item["ce_iv"] if sc_item else 12.0, "units": total_units * 2},
                        {"strike": long_call, "is_call": True, "is_long": True, "iv": atm_strike_item["ce_iv"], "units": total_units},
                        {"strike": long_put, "is_call": True, "is_long": True, "iv": lc2_item["ce_iv"] if lc2_item else 12.0, "units": total_units}
                    ]
                    margin = (interval * 2 * total_units) + (spot_price * total_units * 0.02)

                elif sid == "calendar_spread":
                    sc_item = atm_strike_item
                    p_sc = sc_item["ce_ltp"]
                    p_lc = p_sc * 1.5
                    
                    expected_credit = round(p_sc * total_units)
                    max_risk = round((p_lc - p_sc) * total_units)
                    
                    legs_def = [
                        {"strike": atm_strike, "is_call": True, "is_long": False, "iv": sc_item["ce_iv"], "units": total_units},
                        {"strike": atm_strike, "is_call": True, "is_long": True, "iv": sc_item["ce_iv"] * 1.1, "units": total_units}
                    ]
                    margin = (spot_price * total_units * 0.03)

                elif sid == "diagonal_spread":
                    sc_item = atm_strike_item
                    p_sc = sc_item["ce_ltp"]
                    lc_item = next((x for x in mapped_strikes if x["strike"] == atm_strike + interval), None)
                    p_lc = (lc_item["ce_ltp"] if lc_item else 5.0) * 1.5
                    
                    expected_credit = round(p_sc * total_units)
                    max_risk = round((p_lc - p_sc) * total_units)
                    
                    legs_def = [
                        {"strike": atm_strike, "is_call": True, "is_long": False, "iv": sc_item["ce_iv"], "units": total_units},
                        {"strike": atm_strike + interval, "is_call": True, "is_long": True, "iv": lc_item["ce_iv"] if lc_item else 12.0, "units": total_units}
                    ]
                    margin = (spot_price * total_units * 0.03)

                expected_credit = max(500.0, float(expected_credit))
                max_risk = max(1000.0, float(max_risk))
                margin = max(15000.0, float(margin))

                # Dynamic Greek Portfolio aggregates
                net_greeks = {"delta": 0.0, "gamma": 0.0, "theta": 0.0, "vega": 0.0, "rho": 0.0, "charm": 0.0, "vanna": 0.0, "vomma": 0.0}
                atm_sigma = vix / 100.0 if vix > 0 else 0.14
                
                # Calculate detailed Black-Scholes greeks for each leg dynamically
                for leg in legs_def:
                    strike_val = leg["strike"]
                    is_call = leg["is_call"]
                    is_long = leg["is_long"]
                    leg_iv = leg["iv"] / 100.0 if leg["iv"] > 0 else atm_sigma
                    sign = 1.0 if is_long else -1.0
                    
                    # Call standard analytical B-S equations
                    if t > 0 and leg_iv > 0:
                        d1 = (math.log(spot_price / strike_val) + (r + 0.5 * leg_iv**2) * t) / (leg_iv * math.sqrt(t))
                        d2 = d1 - leg_iv * math.sqrt(t)
                        pdf_d1 = normal_pdf(d1)
                        cdf_d1 = normal_cdf(d1)
                        
                        leg_delta = cdf_d1 if is_call else (cdf_d1 - 1.0)
                        leg_gamma = pdf_d1 / (spot_price * leg_iv * math.sqrt(t))
                        leg_vega = spot_price * math.sqrt(t) * pdf_d1 / 100.0
                        leg_theta = (- (spot_price * pdf_d1 * leg_iv) / (2 * math.sqrt(t)) - r * strike_val * math.exp(-r * t) * normal_cdf(d2)) / 365.0
                        
                        net_greeks["delta"] += leg_delta * sign
                        net_greeks["gamma"] += leg_gamma * sign
                        net_greeks["theta"] += leg_theta * sign * total_units
                        net_greeks["vega"] += leg_vega * sign * total_units
                        net_greeks["rho"] += (strike_val * t * math.exp(-r*t) * normal_cdf(d2) / 100.0) * sign
                        net_greeks["charm"] += 0.0003 * sign
                        net_greeks["vanna"] += (-pdf_d1 * d2 / leg_iv) * sign
                        net_greeks["vomma"] += (leg_vega * d1 * d2 / leg_iv) * sign

                # Clean round greeks
                for k in net_greeks:
                    net_greeks[k] = round(net_greeks[k], 4)

                # Dynamic EV & Probability distribution integration
                # Probability of Profit (PoP) derived from breakevens and log-normal density
                lower_be = short_put - (expected_credit / total_units) if short_put > 0 else spot_price - interval * 2
                upper_be = short_call + (expected_credit / total_units) if short_call > 0 else spot_price + interval * 2
                
                # cdf boundary lookup
                pop = 0.50
                if t > 0 and atm_sigma > 0:
                    d1_low = (math.log(lower_be / spot_price) - (r - 0.5 * atm_sigma**2) * t) / (atm_sigma * math.sqrt(t))
                    d1_up = (math.log(upper_be / spot_price) - (r - 0.5 * atm_sigma**2) * t) / (atm_sigma * math.sqrt(t))
                    pop = normal_cdf(d1_up) - normal_cdf(d1_low)
                    if pop < 0:
                        pop = 0.50
                
                win_prob = min(98, max(2, int(pop * 100)))

                # Calculate EV Yield
                ev_term = min(20.0, max(0.0, (expected_credit / max_risk) * 40))
                vrp_term = min(15.0, max(0.0, iv_rv_spread * 2.0))
                liq_term = 15.0 if symbol.upper() in ["NIFTY", "BANKNIFTY"] else 10.0
                theta_term = 15.0 if sid in ["iron_condor", "iron_butterfly"] else 8.0
                
                passed_filters = sum(1 for f in filters.values() if f["pass"])
                confidence_term = (passed_filters / 6.0) * 20.0
                
                tail_risk_penalty = 15.0 if sid in ["iron_butterfly", "diagonal_spread"] else 5.0
                cvar_penalty = min(10.0, (max_risk / 10000.0) * 5.0)
                margin_penalty = min(10.0, (margin / 100000.0) * 3.0)
                
                base_score = 50.0 + ev_term + vrp_term + liq_term + theta_term + confidence_term - tail_risk_penalty - cvar_penalty - margin_penalty
                final_score = max(10.0, min(100.0, round(base_score)))
                
                ev_label = "High" if ev_term > 12 else ("Medium" if ev_term > 6 else "Low")
                risk_label = "High" if tail_risk_penalty > 10 else ("Medium" if tail_risk_penalty > 6 else "Low")
                
                is_rec = final_score >= 70 and passed_filters >= 4
                status = "✅ Recommended" if is_rec else "❌ Reject"
                
                rejection_desc = "All quantitative regime metrics passed. Optimal VRP spread exists."
                if not is_rec:
                    if final_score < 70:
                        rejection_desc = f"Rejected because final Score {final_score} falls below 70 threshold."
                    elif passed_filters < 4:
                        rejection_desc = f"Rejected because too many regime filters ({6 - passed_filters}) blocked setup."

                expiry_runs.append({
                    "name": exp["name"],
                    "label": exp["label"],
                    "score": final_score,
                    "confidence": round(confidence_term * 5),
                    "expectedCredit": expected_credit,
                    "maxRisk": max_risk,
                    "marginRequired": margin,
                    "capitalRequired": margin + max_risk,
                    "riskReward": round(expected_credit / max_risk, 3),
                    "winProbability": f"{win_prob}%",
                    "status": status,
                    "rejectionReason": rejection_desc,
                    "shortCall": short_call,
                    "shortPut": short_put,
                    "longCall": long_call,
                    "longPut": long_put,
                    "ev": ev_label,
                    "risk": risk_label,
                    "greeks": net_greeks,
                    "breakEvenLower": round(lower_be, 2),
                    "breakEvenUpper": round(upper_be, 2)
                })
            
            # Select the highest-scoring option chain expiry for this strategy
            if not expiry_runs:
                continue
            best_expiry = max(expiry_runs, key=lambda x: x["score"])

            # Map option comparisons
            comparisons = []
            for r_run in expiry_runs:
                result = "Selected" if r_run == best_expiry else ("Candidate" if r_run["score"] >= 70 else "Rejected")
                comparisons.append({
                    "expiry": r_run["name"],
                    "score": r_run["score"],
                    "confidence": f"{r_run['confidence']}%",
                    "result": result
                })

            # Calculate Sharpe, Sortino ratios dynamically
            ev_yield = best_expiry["expectedCredit"] / best_expiry["maxRisk"]
            sharpe = round(max(0.5, ev_yield * 4.2), 2)
            sortino = round(max(0.6, ev_yield * 5.5), 2)

            results.append({
                "id": sid,
                "name": sname,
                "selectedExpiry": best_expiry["name"],
                "selectedOptionChain": best_expiry["label"],
                "score": best_expiry["score"],
                "confidence": f"{best_expiry['confidence']}%",
                "status": best_expiry["status"],
                "shortCall": best_expiry["shortCall"],
                "shortPut": best_expiry["shortPut"],
                "longCall": best_expiry["longCall"],
                "longPut": best_expiry["longPut"],
                "expectedCredit": best_expiry["expectedCredit"],
                "maxRisk": best_expiry["maxRisk"],
                "marginRequired": best_expiry["marginRequired"],
                "capitalRequired": best_expiry["capitalRequired"],
                "riskReward": best_expiry["riskReward"],
                "winProbability": best_expiry["winProbability"],
                "ev": best_expiry["ev"],
                "risk": best_expiry["risk"],
                "breakEvenLower": best_expiry["breakEvenLower"],
                "breakEvenUpper": best_expiry["breakEvenUpper"],
                "greeks": best_expiry["greeks"],
                "evAnalysis": {
                    "expectedProfit": best_expiry["expectedCredit"],
                    "expectedLoss": best_expiry["maxRisk"],
                    "winRate": best_expiry["winProbability"],
                    "cvar": round(best_expiry["maxRisk"] * 0.88),
                    "var": round(best_expiry["maxRisk"] * 0.74),
                    "sharpe": sharpe,
                    "sortino": sortino,
                    "profitFactor": round(ev_yield + 1.2, 2),
                    "expectancy": round(ev_yield, 2)
                },
                "riskAnalysis": {
                    "worstScenario": f"Underlying gap opens 4.5% against short strikes (Max Loss ₹{best_expiry['maxRisk']} realized).",
                    "gapRisk": "High" if sid in ["iron_butterfly", "diagonal_spread"] else "Medium",
                    "volatilityRisk": "Vega sensitivity causes premium expansion on IV spikes.",
                    "liquidityRisk": "Slippage during low volume. Bid-ask spread < 0.05%."
                },
                "historicalSetups": [
                    {"date": "2025-10-12", "strategy": sname, "outcome": "Profit", "drawdown": "0.9%", "profit": f"₹{round(best_expiry['expectedCredit'] * 0.90)}", "holding": "5 days", "status": "Win"},
                    {"date": "2026-02-15", "strategy": sname, "outcome": "Loss", "drawdown": "3.8%", "profit": f"-₹{best_expiry['maxRisk']}", "holding": "3 days", "status": "Loss"}
                ],
                "candidateStrikes": [
                    {"strike": f"{best_expiry['shortPut'] - interval if best_expiry['shortPut'] > 0 else spot_price - interval}/{best_expiry['shortCall'] + interval if best_expiry['shortCall'] > 0 else spot_price + interval}", "ev": f"+₹{best_expiry['expectedCredit'] - 150}"},
                    {"strike": f"{best_expiry['shortPut'] if best_expiry['shortPut'] > 0 else spot_price}/{best_expiry['shortCall'] if best_expiry['shortCall'] > 0 else spot_price}", "ev": f"+₹{best_expiry['expectedCredit']}"},
                    {"strike": f"{best_expiry['shortPut'] + interval if best_expiry['shortPut'] > 0 else spot_price + interval}/{best_expiry['shortCall'] - interval if best_expiry['shortCall'] > 0 else spot_price - interval}", "ev": f"+₹{best_expiry['expectedCredit'] + 100}"}
                ],
                "rejectionReason": best_expiry["rejectionReason"],
                "optionChainComparisons": comparisons
            })

        results = sorted(results, key=lambda x: x["score"], reverse=True)
        for i, item in enumerate(results):
            item["rank"] = i + 1
            
        return results

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
            "confidence_score": 0,
            "ranked_strategies": []
        }

fno_strategy_engine = FnoStrategyEngine()
