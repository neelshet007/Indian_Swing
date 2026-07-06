import pandas as pd
import numpy as np
from indian_swing.database.connection import get_sync_session
from indian_swing.database.models import OHLCV, Stock
from indian_swing.indicators.calculator import IndicatorCalculator
from indian_swing.strategies.institutional_vcp import InstitutionalVCP

def check_rules():
    strategy = InstitutionalVCP()
    rule_counts = {
        "total": 0,
        "enough_history": 0,
        "rule_1_liquidity": 0,
        "rule_2_minervini": 0,
        "rule_3_vcp": 0,
        "rule_4_breakout": 0,
        "rule_5_risk": 0
    }
    
    failed_details = {
        "rule_1": 0,
        "rule_2": 0,
        "rule_3": 0,
        "rule_4": 0,
        "rule_5": 0
    }

    with get_sync_session() as session:
        stocks = session.query(Stock).filter(Stock.is_active == True).all()
        rule_counts["total"] = len(stocks)
        print(f"Total active stocks found: {len(stocks)}", flush=True)
        
        for idx, stock in enumerate(stocks):
            if idx % 50 == 0:
                print(f"Processing stock {idx}/{len(stocks)}: {stock.symbol}", flush=True)
            history = session.query(OHLCV).filter(OHLCV.stock_id == stock.id, OHLCV.timeframe == "1d").order_by(OHLCV.date.asc()).all()
            if not history or len(history) < 325:
                continue
            rule_counts["enough_history"] += 1
            
            df = pd.DataFrame([{
                "date": h.date,
                "open": h.open,
                "high": h.high,
                "low": h.low,
                "close": h.close,
                "volume": h.volume
            } for h in history])
            
            df = IndicatorCalculator.add_daily_indicators(df)
            last_row = df.iloc[-1]
            
            # RULE 1: Liquidity
            passed_r1 = True
            if 'vol_50' in last_row and not pd.isna(last_row['vol_50']):
                if last_row['vol_50'] * last_row['close'] < 10_000_000:
                    passed_r1 = False
            
            if not passed_r1:
                failed_details["rule_1"] += 1
                continue
            rule_counts["rule_1_liquidity"] += 1
            
            # RULE 2: Minervini Moving Average Trend
            passed_r2 = False
            try:
                cond1 = last_row['close'] > last_row['sma_150'] and last_row['close'] > last_row['sma_200']
                cond2 = last_row['sma_150'] > last_row['sma_200']
                
                sma200_20d_ago = df.iloc[-21]['sma_200']
                cond3 = last_row['sma_200'] > sma200_20d_ago
                
                cond4 = last_row['sma_50'] > last_row['sma_150'] and last_row['sma_50'] > last_row['sma_200']
                cond5 = last_row['close'] > last_row['sma_50']
                
                cond6 = last_row['close'] >= 1.30 * last_row['low_52w']
                cond7 = last_row['close'] >= 0.75 * last_row['high_52w']
                
                passed_r2 = cond1 and cond2 and cond3 and cond4 and cond5 and cond6 and cond7
            except KeyError:
                pass
                
            if not passed_r2:
                failed_details["rule_2"] += 1
                continue
            rule_counts["rule_2_minervini"] += 1
            
            # RULE 3: VCP Contraction
            recent_vol_avg = df.iloc[-5:]['volume'].mean()
            passed_r3_vol = recent_vol_avg <= last_row['vol_50']
            
            recent_range = df.iloc[-5:]['high'].max() - df.iloc[-5:]['low'].min()
            passed_r3_range = recent_range <= 3 * last_row['atr_14']
            
            passed_r3 = passed_r3_vol and passed_r3_range
            
            if not passed_r3:
                failed_details["rule_3"] += 1
                continue
            rule_counts["rule_3_vcp"] += 1
            
            # RULE 4: Breakout Confirmation
            recent_high = df.iloc[-20:-1]['high'].max()
            is_breakout = last_row['close'] > recent_high
            is_high_volume = last_row['volume'] > 1.5 * last_row['vol_50']
            
            passed_r4 = is_breakout and is_high_volume
            
            if not passed_r4:
                print(f"Stock {stock.symbol} failed Rule 4: passed_r3=True, is_breakout={is_breakout} (close={last_row['close']:.2f}, 20d_high={recent_high:.2f}), is_high_volume={is_high_volume} (volume={last_row['volume']:.2f}, 1.5*vol_50={1.5*last_row['vol_50']:.2f})", flush=True)
                failed_details["rule_4"] += 1
                continue
            rule_counts["rule_4_breakout"] += 1
            
            # RULE 5: Risk
            atr = last_row['atr_14'] if not pd.isna(last_row['atr_14']) else last_row['close'] * 0.05
            stop_loss = last_row['close'] - (2.5 * atr)
            risk_pct = (last_row['close'] - stop_loss) / last_row['close']
            passed_r5 = risk_pct <= 0.15
            
            if not passed_r5:
                failed_details["rule_5"] += 1
                continue
            rule_counts["rule_5_risk"] += 1
 
    print("Rule execution statistics:", flush=True)
    for k, v in rule_counts.items():
        print(f"  {k}: {v}", flush=True)
    print("Failed at stages:", flush=True)
    for k, v in failed_details.items():
        print(f"  {k}: {v}", flush=True)
 
if __name__ == "__main__":
    check_rules()
