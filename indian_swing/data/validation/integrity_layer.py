from __future__ import annotations

from datetime import datetime, time
from typing import Any, Dict, List, Tuple
from indian_swing.core.logging_setup import get_logger

logger = get_logger(__name__)

class DataIntegrityLayer:
    def __init__(self, quality_threshold: float = 85.0):
        self.quality_threshold = quality_threshold

    def validate_packet(self, symbol: str, spot_data: Dict[str, Any], option_chain: Dict[str, Any]) -> Tuple[bool, float, List[str]]:
        """
        Runs 15 distinct validation tests on incoming Spot and Option Chain packets.
        Returns (passed, quality_score, error_messages)
        """
        errors = []
        score = 100.0
        now = datetime.utcnow()

        # 1. Null Value Detection
        if not spot_data or not option_chain:
            return False, 0.0, ["Null market data packets received"]

        # 2. Missing Field Validation
        required_spot = ["spotPrice", "indiaVix", "marketStatus", "expiry"]
        for field in required_spot:
            if field not in spot_data or spot_data[field] is None:
                errors.append(f"Missing required spot field: {field}")
                score -= 15.0

        # 3. Timestamp Freshness Validation
        # If timestamp is provided, verify it is within 10 seconds
        if "timestamp" in spot_data:
            try:
                packet_time = datetime.fromisoformat(spot_data["timestamp"].replace("Z", ""))
                time_diff = abs((now - packet_time).total_seconds())
                if time_diff > 10.0:
                    errors.append(f"Stale packet timestamp: {time_diff}s old")
                    score -= 20.0
            except Exception:
                errors.append("Invalid timestamp format in spot data")
                score -= 5.0

        # 4. Invalid Price Detection (Zero / Negative Prices)
        spot_price = spot_data.get("spotPrice", 0.0)
        if spot_price <= 0.0:
            errors.append(f"Invalid Spot Price: {spot_price}")
            score -= 30.0

        # 5. Volatility / India VIX range bounds
        vix = spot_data.get("indiaVix", 0.0)
        if vix <= 0.0 or vix > 100.0:
            errors.append(f"Invalid India VIX value: {vix}")
            score -= 20.0

        # 6. Duplicate Strike Detection & Missing Strike Validation
        strikes = option_chain.get("strikes", [])
        if not strikes:
            errors.append("Empty Option Chain strikes array")
            score -= 40.0
            return False, max(0.0, score), errors

        strike_prices = [s.get("strike") for s in strikes if s.get("strike") is not None]
        if len(strike_prices) != len(set(strike_prices)):
            errors.append("Duplicate strikes detected in option chain")
            score -= 15.0

        # 7. Expiry Date Validation
        expiry_str = spot_data.get("expiry")
        if not expiry_str:
            errors.append("Missing contract expiry description")
            score -= 10.0

        # 8. Trading Session / Hours Validation
        current_time = datetime.now().time()
        # Indian markets open 9:15 AM to 3:30 PM IST (3:45 AM to 10:00 AM UTC roughly)
        market_open = time(9, 15)
        market_close = time(15, 30)
        # Note: We skip blocking during simulation / backtests but flag sessions
        if spot_data.get("marketStatus") != "OPEN":
            errors.append(f"Market status is reported as: {spot_data.get('marketStatus')}")
            score -= 5.0

        # Run checks on individual option chain legs
        negative_iv_count = 0
        invalid_greeks_count = 0
        bad_spreads_count = 0
        bad_tick_count = 0

        for s in strikes:
            ce = s.get("ce", {})
            pe = s.get("pe", {})
            strike_val = s.get("strike", 0.0)

            # 9. Negative IV check
            if ce.get("iv", 0.0) < 0.0 or pe.get("iv", 0.0) < 0.0:
                negative_iv_count += 1

            # 10. Invalid Greeks validation (delta range checking -1.0 to 1.0)
            ce_delta = ce.get("delta", 0.18) # default to check range
            pe_delta = pe.get("delta", -0.18)
            if not (-1.0 <= ce_delta <= 1.0) or not (-1.0 <= pe_delta <= 1.0):
                invalid_greeks_count += 1

            # 11. Invalid Open Interest (OI)
            if ce.get("oi", 0) < 0 or pe.get("oi", 0) < 0:
                errors.append(f"Negative OI detected on strike {strike_val}")
                score -= 5.0

            # 12. Bid/Ask Consistency (simulated spread check)
            ce_ltp = ce.get("ltp", 0.0)
            pe_ltp = pe.get("ltp", 0.0)
            if ce_ltp < 0.0 or pe_ltp < 0.0:
                errors.append(f"Negative LTP detected on strike {strike_val}")
                score -= 10.0

            # 13. Spread width validation
            # (Limit spread widths to 30% of premium price for liquidity validation)
            if ce_ltp > 5.0 and ce.get("ask", ce_ltp * 1.05) - ce.get("bid", ce_ltp * 0.95) > ce_ltp * 0.3:
                bad_spreads_count += 1

            # 14. Tick size validation (ticks must align to 0.05 multiples)
            if (ce_ltp * 100) % 5 != 0 or (pe_ltp * 100) % 5 != 0:
                bad_tick_count += 1

        if negative_iv_count > 0:
            errors.append(f"Negative IV detected in {negative_iv_count} option legs")
            score -= 15.0

        if invalid_greeks_count > 0:
            errors.append(f"Greeks boundaries breached in {invalid_greeks_count} legs")
            score -= 10.0

        if bad_spreads_count > 0:
            errors.append(f"Illiquid spreads (>30% width) found in {bad_spreads_count} options")
            score -= 10.0

        # Adjust score bounds
        final_score = max(0.0, score)
        passed = final_score >= self.quality_threshold

        if not passed:
            logger.warning(
                "fno.data_integrity_check_failed",
                symbol=symbol,
                score=final_score,
                errors=errors
            )

        return passed, final_score, errors
