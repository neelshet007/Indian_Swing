import yfinance as yf
import pandas as pd
from datetime import date, timedelta
from typing import List, Tuple
import time

from indian_swing.core.logging_setup import get_logger
from indian_swing.core.symbols import SymbolManager, YahooAdapter

logger = get_logger(__name__)

class DataFetcher:
    def __init__(self, retries: int = 3, backoff_factor: float = 0.5):
        self.retries = retries
        self.backoff_factor = backoff_factor

    def fetch_missing_data(self, symbol: str, earliest_db_date: date | None, latest_db_date: date | None, required_lookback_days: int) -> pd.DataFrame:
        """
        Fetches ONLY missing daily data from Yahoo Finance.
        Handles provider-specific suffix formats via SymbolManager.
        """
        try:
            yf_symbol = SymbolManager.get_provider_symbol(symbol, YahooAdapter())
        except ValueError as e:
            logger.error(f"Symbol formatting error for {symbol}: {e}")
            return pd.DataFrame()
        
        today = date.today()
        target_start_date = today - timedelta(days=int(required_lookback_days * 1.5))
        
        ranges_to_fetch = []
        if not earliest_db_date:
            ranges_to_fetch.append((target_start_date, today + timedelta(days=1)))
        else:
            if earliest_db_date > target_start_date:
                ranges_to_fetch.append((target_start_date, earliest_db_date))
            if latest_db_date and latest_db_date < today - timedelta(days=1):
                ranges_to_fetch.append((latest_db_date + timedelta(days=1), today + timedelta(days=1)))

        dfs = []
        for start_date, end_date in ranges_to_fetch:
            for attempt in range(self.retries):
                try:
                    ticker = yf.Ticker(yf_symbol)
                    df = ticker.history(start=start_date, end=end_date, auto_adjust=True)
                    if not df.empty:
                        # Clean up DataFrame
                        df.reset_index(inplace=True)
                        if df['Date'].dt.tz is not None:
                            df['Date'] = df['Date'].dt.tz_localize(None)
                        df.rename(columns={
                            "Date": "date", "Open": "open", "High": "high",
                            "Low": "low", "Close": "close", "Volume": "volume"
                        }, inplace=True)
                        df['date'] = df['date'].dt.date
                        df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
                        df.dropna(inplace=True)
                        df.drop_duplicates(subset=['date'], inplace=True)
                        dfs.append(df)
                    break
                except Exception as e:
                    err_msg = str(e).lower()
                    if "possibly delisted" in err_msg or "no timezone found" in err_msg:
                        logger.error(f"Yahoo API rejects symbol {yf_symbol} (likely delisted or invalid).")
                        break
                    logger.warning(f"Failed fetching {yf_symbol} attempt {attempt+1}/{self.retries}: {e}")
                    if attempt == self.retries - 1:
                        logger.error(f"Completely failed fetching {yf_symbol}")
                    time.sleep(self.backoff_factor * (2 ** attempt))
                    
        if not dfs:
            return pd.DataFrame()
            
        combined_df = pd.concat(dfs).sort_values('date').drop_duplicates(subset=['date'])
        return combined_df
