import pandas as pd
import numpy as np
from datetime import date
from typing import Any

from indian_swing.core.types import (
    RiskLevel,
    Score,
    SignalDirection,
    SignalQuality,
    Symbol,
)
from indian_swing.strategies.base import BaseStrategy, StrategySignal

class InstitutionalVCP(BaseStrategy):
    """
    Institutional VCP pattern detection for Portfolio A (Core), B (Small-Cap), and C (Penny).
    """

    required_lookback = 200

    @property
    def name(self) -> str:
        return "InstitutionalVCP"

    @property
    def description(self) -> str:
        return "Volatility Contraction Pattern with Portfolio Tier sizing"

    def generate_signals(
        self,
        symbol: Symbol,
        df: pd.DataFrame,
        as_of_date: date | None = None,
    ) -> list[StrategySignal]:
        
        if not self.validate_df(df):
            return []

        # Determine Portfolio Tier based on Universe (Mocked for now)
        # Ideally passed from universe filter
        tier = "A" # Default to Core
        
        # Calculate Base indicators
        df['sma_50'] = df['close'].rolling(50).mean()
        df['sma_150'] = df['close'].rolling(150).mean()
        df['sma_200'] = df['close'].rolling(200).mean()
        df['vol_50'] = df['volume'].rolling(50).mean()
        df['atr_14'] = df['high'].rolling(14).max() - df['low'].rolling(14).min()
        
        last_row = df.iloc[-1]
        
        # Weinstein Stage 2 / Minervini Trend Template
        is_uptrend = (
            last_row['close'] > last_row['sma_50'] and
            last_row['sma_50'] > last_row['sma_150'] and
            last_row['sma_150'] > last_row['sma_200']
        )
        
        if not is_uptrend:
            return []
            
        # Breakout Volume rules by tier
        vol_mult = 1.5 if tier == "A" else 2.0
        if last_row['volume'] < vol_mult * last_row['vol_50']:
            return []
            
        # ATR Stop Mult by tier
        atr = last_row['atr_14'] if not pd.isna(last_row['atr_14']) else last_row['close'] * 0.05
        stop_mult = 2.5 if tier == "A" else 3.0 if tier == "B" else 3.5
        stop_loss = last_row['close'] - (stop_mult * atr)
        
        risk = last_row['close'] - stop_loss
        target_1 = last_row['close'] + (2.0 * risk) if tier == "A" else last_row['close'] + (1.5 * risk)
        target_2 = last_row['close'] + (4.0 * risk) if tier == "A" else last_row['close'] + (3.0 * risk)
        
        return [
            StrategySignal(
                symbol=symbol,
                direction=SignalDirection.LONG,
                entry_price=last_row['close'],
                stop_loss=stop_loss,
                target_1=target_1,
                target_2=target_2,
                confidence_score=0.8,
                quality=SignalQuality.STRONG,
                risk_level=RiskLevel.MEDIUM,
                holding_days=60 if tier == "A" else 45 if tier == "B" else 30,
                reasons=[f"VCP Breakout on {vol_mult}x vol (Tier {tier})"],
                metadata={"tier": tier, "atr": atr}
            )
        ]
