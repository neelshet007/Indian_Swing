import pandas as pd
import numpy as np

class IndicatorCalculator:
    @staticmethod
    def add_daily_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Adds standard daily indicators to a daily OHLCV dataframe."""
        if df.empty or len(df) < 200:
            return df
            
        df = df.copy()
        
        # Moving Averages
        df['sma_50'] = df['close'].rolling(50).mean()
        df['sma_150'] = df['close'].rolling(150).mean()
        df['sma_200'] = df['close'].rolling(200).mean()
        df['ema_20'] = df['close'].ewm(span=20, adjust=False).mean()
        
        # Volume
        df['vol_50'] = df['volume'].rolling(50).mean()
        
        # ATR (14)
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['atr_14'] = true_range.rolling(14).mean()
        
        # 52-week High/Low (approx 250 trading days)
        df['high_52w'] = df['high'].rolling(250).max()
        df['low_52w'] = df['low'].rolling(250).min()
        
        return df

    @staticmethod
    def add_weekly_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Adds standard weekly indicators to a weekly OHLCV dataframe."""
        if df.empty or len(df) < 30:
            return df
            
        df = df.copy()
        
        # 30-Week SMA (approx 150 day)
        df['sma_30w'] = df['close'].rolling(30).mean()
        
        # 40-Week SMA (approx 200 day)
        df['sma_40w'] = df['close'].rolling(40).mean()
        
        # 10-Week SMA (approx 50 day)
        df['sma_10w'] = df['close'].rolling(10).mean()
        
        return df
