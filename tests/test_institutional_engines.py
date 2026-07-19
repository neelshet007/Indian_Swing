import pandas as pd
import numpy as np
import pytest
from datetime import date, timedelta
from indian_swing.strategies.market_regime import MarketRegimeEngine
from indian_swing.strategies.breakout_analyzer import BreakoutAnalyzer
from indian_swing.strategies.risk_engine import RiskEngine
from indian_swing.strategies.scoring_engine import ScoringEngine

def test_market_regime_classification():
    # 1. Null benchmark input
    res = MarketRegimeEngine.classify_regime(None)
    assert res["passed"] is True
    assert res["regime"] == "Bull"

    # 2. Mock Bull Market data
    dates = [date(2026, 1, 1) + timedelta(days=i) for i in range(250)]
    close_prices = [100.0 + i for i in range(250)]
    df = pd.DataFrame({
        "open": close_prices,
        "high": [c + 1.0 for c in close_prices],
        "low": [c - 1.0 for c in close_prices],
        "close": close_prices,
        "volume": [10000] * 250
    }, index=pd.DatetimeIndex(dates))
    
    res = MarketRegimeEngine.classify_regime(df)
    assert res["regime"] == "Bull"
    assert res["passed"] is True

def test_breakout_analyzer():
    # Mock daily dataframe
    df = pd.DataFrame({
        "open": [100.0, 102.0],
        "high": [105.0, 106.0],
        "low": [98.0, 101.0],
        "close": [102.0, 105.5],  # Closes near high
        "volume": [10000, 15000]
    }, index=pd.date_range("2026-01-01", periods=2))
    
    res = BreakoutAnalyzer.analyze_breakout(df, pivot_price=104.0, atr_14=2.0)
    assert res["close_position_pct"] > 65.0
    assert res["extension_pct"] <= 5.0

def test_risk_validator():
    # Sector limits
    res = RiskEngine.validate_risk(risk_pct=5.0, sector="IT", active_positions=[{"sector": "IT"}, {"sector": "IT"}])
    assert res["passed"] is True
    
    # 3 active positions already exists in same sector -> fails sector cap
    res = RiskEngine.validate_risk(risk_pct=5.0, sector="IT", active_positions=[{"sector": "IT"}, {"sector": "IT"}, {"sector": "IT"}])
    assert res["passed"] is False
    assert "Sector Cap Reached" in res["reason"]

def test_scoring_engine():
    res = ScoringEngine.calculate_overall_score(
        stage_confidence=80.0,
        vcp_score=90.0,
        breakout_details={"close_position_pct": 90.0, "atr_expansion_ratio": 1.5},
        rs_score=15.0,
        market_regime_health=100.0
    )
    assert 0.0 <= res["score"] <= 100.0
    assert "stage_quality" in res["components"]
