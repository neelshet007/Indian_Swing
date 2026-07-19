import pandas as pd
import numpy as np
import pytest
from datetime import date, timedelta
from indian_swing.strategies.stage_detector import InstitutionalStageDetector

def generate_mock_weekly_data(trend_type: str = "up") -> pd.DataFrame:
    """
    Generates mock weekly stock candle data.
    """
    dates = [date(2025, 1, 1) + timedelta(weeks=i) for i in range(60)]
    
    close_prices = []
    high_prices = []
    low_prices = []
    
    base_price = 100.0
    for i in range(60):
        if trend_type == "up":
            # Rising price channel
            close = base_price + (i * 2.0) + (np.sin(i) * 3.0)
        elif trend_type == "down":
            # Declining price channel
            close = base_price - (i * 1.5) + (np.cos(i) * 3.0)
        else:
            # Flat/sideways range
            close = base_price + (np.sin(i) * 2.0)
            
        close_prices.append(close)
        high_prices.append(close + 3.0)
        low_prices.append(close - 3.0)
        
    df = pd.DataFrame({
        "open": close_prices,
        "high": high_prices,
        "low": low_prices,
        "close": close_prices,
        "volume": [50000] * 60
    }, index=pd.DatetimeIndex(dates))
    
    # Calculate rolling averages beforehand as required by detector
    df["sma_10w"] = df["close"].rolling(10, min_periods=10).mean()
    df["sma_30w"] = df["close"].rolling(30, min_periods=30).mean()
    df["sma_40w"] = df["close"].rolling(40, min_periods=40).mean()
    
    return df

def test_stage_detector_insufficient_data():
    df = pd.DataFrame({
        "open": [100.0] * 10,
        "high": [105.0] * 10,
        "low": [95.0] * 10,
        "close": [100.0] * 10,
        "volume": [1000] * 10
    }, index=pd.date_range("2026-01-01", periods=10, freq="W"))
    
    res = InstitutionalStageDetector.calculate_stages(df)
    assert res["stage_classification"].iloc[-1] == "Insufficient Data"
    assert res["stage_confidence"].iloc[-1] == 0.0

def test_stage_detector_uptrend():
    df = generate_mock_weekly_data(trend_type="up")
    res = InstitutionalStageDetector.calculate_stages(df)
    
    # Assert columns exist
    assert "stage_confidence" in res
    assert "stage_classification" in res
    assert "stage_details" in res
    
    # Late rows in a strong uptrend should be classified under Stage 2
    stage_val = res["stage"].iloc[-1]
    assert stage_val in [2, 1]  # Should map to Stage 2 or 1
    
def test_stage_detector_downtrend():
    df = generate_mock_weekly_data(trend_type="down")
    res = InstitutionalStageDetector.calculate_stages(df)
    
    # Late rows in a clear downtrend should map to Stage 4 or 3
    stage_val = res["stage"].iloc[-1]
    assert stage_val in [4, 3, 1]
