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
from indian_swing.core.logging_setup import get_logger

logger = get_logger(__name__)

class InstitutionalVCP(BaseStrategy):
    """
    SIVCS institutional-grade strategy pipeline.
    Executes in a strict short-circuiting order from cheapest to most expensive filters.
    """

    @property
    def name(self) -> str:
        return "sivcs_vcp"

    @property
    def description(self) -> str:
        return "Institutional VCP with strict short-circuiting filter pipeline."

    def generate_signals(
        self,
        symbol: Symbol,
        df: pd.DataFrame,
        as_of_date: date | None = None,
    ) -> list[StrategySignal]:
        
        # We assume indicators are already calculated by the Engine/Scanner
        last_row = df.iloc[-1]
        
        reasons = []
        
        # RULE 1: Liquidity & Market Cap (Cheapest)
        # Assuming minimum 1cr volume (approx 1,00,00,000)
        # Using 50 day avg volume
        if 'vol_50' in last_row and not pd.isna(last_row['vol_50']):
            if last_row['vol_50'] * last_row['close'] < 10_000_000:
                # Fails liquidity
                return []
                
        # RULE 2: Minervini Moving Average Trend (Medium cost)
        # 1. Current Price > 150 SMA and 200 SMA
        # 2. 150 SMA > 200 SMA
        # 3. 200 SMA trending up for at least 1 month (20 days)
        # 4. 50 SMA > 150 SMA and 200 SMA
        # 5. Current Price > 50 SMA
        # 6. Current Price is at least 30% above 52-week low
        # 7. Current Price is within 25% of 52-week high
        
        try:
            cond1 = last_row['close'] > last_row['sma_150'] and last_row['close'] > last_row['sma_200']
            cond2 = last_row['sma_150'] > last_row['sma_200']
            
            sma200_20d_ago = df.iloc[-21]['sma_200']
            cond3 = last_row['sma_200'] > sma200_20d_ago
            
            cond4 = last_row['sma_50'] > last_row['sma_150'] and last_row['sma_50'] > last_row['sma_200']
            cond5 = last_row['close'] > last_row['sma_50']
            
            cond6 = last_row['close'] >= 1.30 * last_row['low_52w']
            cond7 = last_row['close'] >= 0.75 * last_row['high_52w']
            
            is_minervini_trend = cond1 and cond2 and cond3 and cond4 and cond5 and cond6 and cond7
            
            if not is_minervini_trend:
                return []
                
            reasons.append("Minervini Trend Template passed")
            
        except KeyError as e:
            logger.error(f"Missing indicator for {symbol}: {e}")
            return []
            
        # RULE 3: VCP Detection (More expensive)
        # Look for contraction in volatility over last few weeks. 
        # Simplified: recent daily range is smaller than average ATR, and volume is drying up
        
        recent_vol_avg = df.iloc[-5:]['volume'].mean()
        if recent_vol_avg > last_row['vol_50']:
             # Not contracting volume
             return []
             
        recent_range = df.iloc[-5:]['high'].max() - df.iloc[-5:]['low'].min()
        if recent_range > 3 * last_row['atr_14']:
            # Still too volatile
            return []
            
        reasons.append("VCP Volatility Contraction detected")
            
        # RULE 4: Breakout Confirmation (Trigger)
        # Price crossing above recent resistance on above average volume
        recent_high = df.iloc[-20:-1]['high'].max()
        is_breakout = last_row['close'] > recent_high
        is_high_volume = last_row['volume'] > 1.5 * last_row['vol_50']
        
        if not (is_breakout and is_high_volume):
             return []
             
        reasons.append(f"Breakout above {recent_high:.2f} on {last_row['volume']/last_row['vol_50']:.1f}x volume")

        # RISK VALIDATION & SIZING
        atr = last_row['atr_14'] if not pd.isna(last_row['atr_14']) else last_row['close'] * 0.05
        stop_mult = 2.5
        stop_loss = last_row['close'] - (stop_mult * atr)
        
        # Validate stop is not too wide
        risk_pct = (last_row['close'] - stop_loss) / last_row['close']
        if risk_pct > 0.15:
            # Stop too wide, reject
            return []
        
        risk = last_row['close'] - stop_loss
        target_1 = last_row['close'] + (2.0 * risk) 
        target_2 = last_row['close'] + (4.0 * risk) 
        
        return [
            StrategySignal(
                symbol=symbol,
                direction=SignalDirection.LONG,
                entry_price=last_row['close'],
                stop_loss=stop_loss,
                target_1=target_1,
                target_2=target_2,
                confidence_score=0.9,
                quality=SignalQuality.STRONG,
                risk_level=RiskLevel.MEDIUM,
                holding_days=45,
                reasons=reasons,
                metadata={"atr": atr}
            )
        ]
