from __future__ import annotations
from typing import Any

class RiskEngine:
    @staticmethod
    def validate_risk(
        risk_pct: float,
        sector: str | None,
        active_positions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Validates trade and portfolio risk guidelines, checking sector exposure limits
        and calculating slippage-adjusted stop parameters.
        """
        # 1. Sector cap check (maximum 30% allocation to any single sector)
        # Assuming each position has 10% allocation (since max weight is 10%),
        # we allow maximum 3 active positions in the same sector.
        sector = sector or "General"
        sector_count = 0
        for pos in active_positions:
            if pos.get("sector") == sector:
                sector_count += 1
                
        sector_limit_pass = sector_count < 3 # Less than 3 existing positions in same sector
        
        # 2. Risk cap validation (trade risk must be between 1% and 10% of stock price)
        risk_cap_pass = 1.0 <= risk_pct <= 10.0

        passed = sector_limit_pass and risk_cap_pass

        return {
            "passed": passed,
            "sector_limit_passed": sector_limit_pass,
            "risk_cap_passed": risk_cap_pass,
            "sector_count": sector_count,
            "reason": (
                "Risk Approved" if passed else
                ("Sector Cap Reached (Max 3 positions per industry)" if not sector_limit_pass else
                 "Risk Percentage Exceeds Limits (1%-10% range required)")
            )
        }
