import pandas as pd
import numpy as np
from indian_swing.database.connection import get_sync_session
from indian_swing.database.models import OHLCV, Stock
from indian_swing.indicators.calculator import IndicatorCalculator
from indian_swing.strategies.institutional_vcp import InstitutionalVCP
import datetime

def verify_stock(stock_id, verify_date):
    with get_sync_session() as session:
        stock = session.query(Stock).filter(Stock.id == stock_id).one()
        print(f"Verifying stock: {stock.symbol} (ID: {stock_id}) as of {verify_date}")
        
        history = session.query(OHLCV).filter(OHLCV.stock_id == stock_id, OHLCV.timeframe == "1d").order_by(OHLCV.date.asc()).all()
        df = pd.DataFrame([{
            "date": h.date,
            "open": h.open,
            "high": h.high,
            "low": h.low,
            "close": h.close,
            "volume": h.volume
        } for h in history])
        
        # Filter up to verify_date
        df['date_dt'] = pd.to_datetime(df['date']).dt.date
        df_filtered = df[df['date_dt'] <= verify_date].copy()
        
        df_with_ind = IndicatorCalculator.add_daily_indicators(df_filtered)
        last_row = df_with_ind.iloc[-1]
        
        print("\n--- Calculations (Formula Verification) ---")
        print(f"Date: {last_row['date']}")
        print(f"Open: {last_row['open']:.2f}")
        print(f"High: {last_row['high']:.2f}")
        print(f"Low: {last_row['low']:.2f}")
        print(f"Close: {last_row['close']:.2f}")
        print(f"Volume: {last_row['volume']:.0f}")
        
        print(f"SMA 50: {last_row['sma_50']:.2f}" if 'sma_50' in last_row else "SMA 50: N/A")
        print(f"SMA 150: {last_row['sma_150']:.2f}" if 'sma_150' in last_row else "SMA 150: N/A")
        print(f"SMA 200: {last_row['sma_200']:.2f}" if 'sma_200' in last_row else "SMA 200: N/A")
        print(f"EMA 20: {last_row['ema_20']:.2f}" if 'ema_20' in last_row else "EMA 20: N/A")
        print(f"Volume 50 Avg: {last_row['vol_50']:.0f}" if 'vol_50' in last_row else "Volume 50 Avg: N/A")
        print(f"ATR 14: {last_row['atr_14']:.2f}" if 'atr_14' in last_row else "ATR 14: N/A")
        print(f"52W High: {last_row['high_52w']:.2f}" if 'high_52w' in last_row else "52W High: N/A")
        print(f"52W Low: {last_row['low_52w']:.2f}" if 'low_52w' in last_row else "52W Low: N/A")
        
        print("\n--- Strategy Rules Verification ---")
        
        # Rule 1: Liquidity
        liq_val = last_row['vol_50'] * last_row['close']
        passed_r1 = liq_val >= 10_000_000
        print(f"Rule 1 (Liquidity): {'PASS' if passed_r1 else 'FAIL'} (vol_50 * close = {liq_val:.2f})")
        
        # Rule 2: Minervini
        cond1 = last_row['close'] > last_row['sma_150'] and last_row['close'] > last_row['sma_200']
        cond2 = last_row['sma_150'] > last_row['sma_200']
        sma200_20d_ago = df_with_ind.iloc[-21]['sma_200']
        cond3 = last_row['sma_200'] > sma200_20d_ago
        cond4 = last_row['sma_50'] > last_row['sma_150'] and last_row['sma_50'] > last_row['sma_200']
        cond5 = last_row['close'] > last_row['sma_50']
        cond6 = last_row['close'] >= 1.30 * last_row['low_52w']
        cond7 = last_row['close'] >= 0.75 * last_row['high_52w']
        passed_r2 = cond1 and cond2 and cond3 and cond4 and cond5 and cond6 and cond7
        
        print(f"Rule 2 (Minervini Trend): {'PASS' if passed_r2 else 'FAIL'}")
        print(f"  - Close > SMA150 & Close > SMA200: {cond1} (close={last_row['close']:.2f}, sma150={last_row['sma_150']:.2f}, sma200={last_row['sma_200']:.2f})")
        print(f"  - SMA150 > SMA200: {cond2} (sma150={last_row['sma_150']:.2f}, sma200={last_row['sma_200']:.2f})")
        print(f"  - SMA200 Trending Up (20d ago): {cond3} (curr={last_row['sma_200']:.2f}, 20d_ago={sma200_20d_ago:.2f})")
        print(f"  - SMA50 > SMA150 & SMA50 > SMA200: {cond4} (sma50={last_row['sma_50']:.2f}, sma150={last_row['sma_150']:.2f}, sma200={last_row['sma_200']:.2f})")
        print(f"  - Close > SMA50: {cond5} (close={last_row['close']:.2f}, sma50={last_row['sma_50']:.2f})")
        print(f"  - Close >= 1.30 * 52W Low: {cond6} (close={last_row['close']:.2f}, 1.30*low_52w={1.30 * last_row['low_52w']:.2f})")
        print(f"  - Close >= 0.75 * 52W High: {cond7} (close={last_row['close']:.2f}, 0.75*high_52w={0.75 * last_row['high_52w']:.2f})")
        
        # Rule 3: VCP
        recent_vol_avg = df_with_ind.iloc[-5:]['volume'].mean()
        passed_r3_vol = recent_vol_avg <= last_row['vol_50']
        recent_range = df_with_ind.iloc[-5:]['high'].max() - df_with_ind.iloc[-5:]['low'].min()
        passed_r3_range = recent_range <= 3 * last_row['atr_14']
        passed_r3 = passed_r3_vol and passed_r3_range
        print(f"Rule 3 (VCP): {'PASS' if passed_r3 else 'FAIL'}")
        print(f"  - Recent volume avg <= Vol50: {passed_r3_vol} (avg={recent_vol_avg:.0f}, vol_50={last_row['vol_50']:.0f})")
        print(f"  - Recent range <= 3*ATR14: {passed_r3_range} (range={recent_range:.2f}, 3*atr_14={3 * last_row['atr_14']:.2f})")
        
        # Rule 4: Breakout
        recent_high = df_with_ind.iloc[-20:-1]['high'].max()
        is_breakout = last_row['close'] > recent_high
        is_high_volume = last_row['volume'] > 1.5 * last_row['vol_50']
        passed_r4 = is_breakout and is_high_volume
        print(f"Rule 4 (Breakout): {'PASS' if passed_r4 else 'FAIL'}")
        print(f"  - Close > 20d High: {is_breakout} (close={last_row['close']:.2f}, 20d_high={recent_high:.2f})")
        print(f"  - Volume > 1.5*Vol50: {is_high_volume} (volume={last_row['volume']:.0f}, 1.5*vol_50={1.5 * last_row['vol_50']:.0f})")
        
        # Rule 5: Risk
        atr = last_row['atr_14'] if not pd.isna(last_row['atr_14']) else last_row['close'] * 0.05
        stop_loss = last_row['close'] - (2.5 * atr)
        risk_pct = (last_row['close'] - stop_loss) / last_row['close']
        passed_r5 = risk_pct <= 0.15
        print(f"Rule 5 (Risk): {'PASS' if passed_r5 else 'FAIL'} (risk_pct={risk_pct*100:.2f}%)")
        
        strategy = InstitutionalVCP()
        sigs = strategy.generate_signals(stock.symbol, df_with_ind)
        print("\nStrategy generated signals:", len(sigs))
        for sig in sigs:
            print(f"  - Direction: {sig.direction}, Entry: {sig.entry_price:.2f}, Stop: {sig.stop_loss:.2f}, T1: {sig.target_1:.2f}, T2: {sig.target_2:.2f}, Reasons: {sig.reasons}")

if __name__ == "__main__":
    verify_stock(171, datetime.date(2026, 7, 6))
    print("\n" + "="*50 + "\n")
    verify_stock(488, datetime.date(2026, 6, 25))
