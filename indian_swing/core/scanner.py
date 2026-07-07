import pandas as pd
from typing import List, Optional, Callable, Dict, Any
from datetime import date

from indian_swing.core.logging_setup import get_logger
from indian_swing.database.connection import get_sync_session
from indian_swing.database.repositories.market_data import MarketDataRepository
from indian_swing.data.universe import UniverseLoader
from indian_swing.data.fetcher import DataFetcher
from indian_swing.data.aggregator import DataAggregator
from indian_swing.indicators.calculator import IndicatorCalculator
from indian_swing.strategies.institutional_vcp import InstitutionalVCP
from indian_swing.strategies.base import StrategySignal
from indian_swing.core.lookback_engine import DynamicLookbackEngine

logger = get_logger(__name__)

class SIVCSScanner:
    def __init__(self):
        self.strategy = InstitutionalVCP()
        self.fetcher = DataFetcher()

    def run_scan(self, progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None, as_of_date: Optional[date] = None) -> List[StrategySignal]:
        logger.info(f"Starting SIVCS Institutional Scan (as of date: {as_of_date or 'today'})")
        all_signals = []
        
        with get_sync_session() as session:
            repo = MarketDataRepository(session)
            
            # Step 1: Load Universe
            logger.info("Step 1: Loading Universe...")
            universe_loader = UniverseLoader(session)
            try:
                universe_loader.load_universe()
            except Exception as e:
                logger.error(f"Failed to load universe: {e}")
                
            active_stocks = repo.get_active_stocks()
            logger.info(f"Loaded {len(active_stocks)} active stocks.")
            
            # Calculate dynamic lookback once before scanning
            required_lookback_days = DynamicLookbackEngine.get_required_lookback(self.strategy)
            
            # Fail Fast Validation
            if not isinstance(required_lookback_days, int) or required_lookback_days <= 0:
                error_msg = f"Lookback Engine failed to determine a valid historical period. Got: {required_lookback_days}"
                logger.error(error_msg)
                raise ValueError(error_msg)
                
            total_stocks = len(active_stocks)
            completed_count = 0
            failed_count = 0
            
            def emit_progress(symbol: str, stage: str):
                if progress_callback:
                    progress_callback({
                        "total_stocks": total_stocks,
                        "completed": completed_count,
                        "failed": failed_count,
                        "remaining": total_stocks - completed_count - failed_count,
                        "current_symbol": symbol,
                        "current_stage": stage
                    })
            
            for i, stock in enumerate(active_stocks):
                logger.info(f"[{i+1}/{total_stocks}] Scanning {stock.symbol}")
                try:
                    emit_progress(stock.symbol, "Verifying Data")
                    # Step 2: Verify Historical Data & Missing Data Check
                    earliest_date = repo.get_earliest_ohlcv_date(stock.stock_uuid, "1d")
                    latest_date = repo.get_latest_ohlcv_date(stock.stock_uuid, "1d")
                    
                    emit_progress(stock.symbol, "Downloading Delta")
                    # Step 3 & 4: Fetch missing Data
                    delta_df = self.fetcher.fetch_missing_data(
                        symbol=stock.symbol, 
                        earliest_db_date=earliest_date,
                        latest_db_date=latest_date, 
                        required_lookback_days=required_lookback_days
                    )
                    
                    # Step 5: Database Update
                    if not delta_df.empty:
                        logger.info(f"  Downloaded {len(delta_df)} missing daily candles.")
                        records = []
                        for _, row in delta_df.iterrows():
                            records.append({
                                "stock_uuid": stock.stock_uuid,
                                "date": row['date'],
                                "timeframe": "1d",
                                "open": row['open'],
                                "high": row['high'],
                                "low": row['low'],
                                "close": row['close'],
                                "volume": row['volume'],
                                "is_adjusted": True
                            })
                        repo.bulk_insert_ohlcv(records)
                    
                    # Fetch Full History from DB for processing
                    history = repo.get_ohlcv_data(stock.stock_uuid, "1d")
                    if not history:
                        logger.warning(f"  No history found in DB for {stock.symbol}, skipping.")
                        continue
                        
                    # Build DataFrame
                    df = pd.DataFrame([{
                        "date": h.date,
                        "open": h.open,
                        "high": h.high,
                        "low": h.low,
                        "close": h.close,
                        "volume": h.volume
                    } for h in history])
                    
                    if as_of_date:
                        # Ensure we convert dates to datetime.date objects for robust comparison
                        import datetime as dt_module
                        df['date_dt'] = pd.to_datetime(df['date']).dt.date
                        df = df[df['date_dt'] <= as_of_date].drop(columns=['date_dt'])
                    
                    if len(df) < required_lookback_days:
                        logger.warning(f"  Insufficient history ({len(df)} bars), requires {required_lookback_days}. Skipping.")
                        continue

                    emit_progress(stock.symbol, "Aggregating Weekly")
                    # Step 6: Build Weekly/Monthly Data and store in DB
                    if not delta_df.empty:
                        weekly_df = DataAggregator.aggregate_weekly(df)
                        weekly_records = []
                        for _, row in weekly_df.iterrows():
                             weekly_records.append({
                                "stock_uuid": stock.stock_uuid,
                                "date": row['date'],
                                "timeframe": "1W",
                                "open": row['open'],
                                "high": row['high'],
                                "low": row['low'],
                                "close": row['close'],
                                "volume": row['volume'],
                                "is_adjusted": True
                            })
                        repo.bulk_insert_ohlcv(weekly_records)
                        
                        monthly_df = DataAggregator.aggregate_monthly(df)
                        monthly_records = []
                        for _, row in monthly_df.iterrows():
                             monthly_records.append({
                                "stock_uuid": stock.stock_uuid,
                                "date": row['date'],
                                "timeframe": "1M",
                                "open": row['open'],
                                "high": row['high'],
                                "low": row['low'],
                                "close": row['close'],
                                "volume": row['volume'],
                                "is_adjusted": True
                            })
                        repo.bulk_insert_ohlcv(monthly_records)
                        
                    emit_progress(stock.symbol, "Calculating Indicators")
                    # Step 7: Indicator Calculation (Calculate once, reuse)
                    df_with_indicators = IndicatorCalculator.add_daily_indicators(df)
                    
                    emit_progress(stock.symbol, "Evaluating Strategy")
                    # Step 9: Scan Every Stock (Apply Strategy Rules)
                    signals = self.strategy.generate_signals(stock.symbol, df_with_indicators)
                    
                    if signals:
                        for s in signals:
                            logger.info(f"  >>> BUY SIGNAL: {s.symbol} at {s.entry_price:.2f} (Stop: {s.stop_loss:.2f})")
                            logger.info(f"      Reasons: {', '.join(s.reasons)}")
                            all_signals.append(s)
                            
                    completed_count += 1
                    emit_progress(stock.symbol, "Completed")
                            
                except Exception as e:
                     logger.error(f"  Error processing {stock.symbol}: {e}")
                     failed_count += 1
                     emit_progress(stock.symbol, "Failed")
                     continue # Continue to next stock on failure

        logger.info(f"Scan complete. Generated {len(all_signals)} valid setups.")
        return all_signals

if __name__ == "__main__":
    scanner = SIVCSScanner()
    scanner.run_scan()
