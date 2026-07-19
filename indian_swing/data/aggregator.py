import pandas as pd
from typing import List, Dict

class DataAggregator:
    @staticmethod
    def aggregate_weekly(daily_df: pd.DataFrame) -> pd.DataFrame:
        """
        Converts daily OHLCV DataFrame to Weekly.
        """
        if daily_df.empty:
            return pd.DataFrame()
            
        df = daily_df.copy()
        # Convert date to datetime if it's not already
        if not pd.api.types.is_datetime64_any_dtype(df['date']):
             df['date'] = pd.to_datetime(df['date'])
             
        df.set_index('date', inplace=True)
        
        # 'W-FRI' ensures week ends on Friday
        agg_dict = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }
        
        weekly_df = df.resample('W-FRI').agg(agg_dict)
        weekly_df.dropna(inplace=True)
        weekly_df.reset_index(inplace=True)
        weekly_df['date'] = weekly_df['date'].dt.date
        weekly_df['timeframe'] = '1W'
        
        return weekly_df

    @staticmethod
    def aggregate_monthly(daily_df: pd.DataFrame) -> pd.DataFrame:
        """
        Converts daily OHLCV DataFrame to Monthly.
        """
        if daily_df.empty:
            return pd.DataFrame()
            
        df = daily_df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df['date']):
             df['date'] = pd.to_datetime(df['date'])
             
        df.set_index('date', inplace=True)
        
        agg_dict = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }
        
        monthly_df = df.resample('ME').agg(agg_dict)
        monthly_df.dropna(inplace=True)
        monthly_df.reset_index(inplace=True)
        monthly_df['date'] = monthly_df['date'].dt.date
        monthly_df['timeframe'] = '1M'
        
        return monthly_df
