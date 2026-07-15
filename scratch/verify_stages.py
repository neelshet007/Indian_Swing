import asyncio
import pandas as pd
import numpy as np
from datetime import date, timedelta
from indian_swing.database.connection import get_sync_session
from indian_swing.database.models import Stock
from indian_swing.database.repositories.ohlcv_repo import OHLCVRepository
from indian_swing.database.repositories.stock_repo import StockRepository
from indian_swing.core.lookback_engine import DynamicLookbackEngine
from indian_swing.strategies.institutional_vcp import InstitutionalVCP
from indian_swing.recommendations.validator import RecommendationValidator
from indian_swing.strategies.base import StrategyContext
from indian_swing.indicators.calculator import IndicatorCalculator
from indian_swing.config.settings import settings

async def diagnose_stock(symbol: str):
    print(f"=== DIAGNOSING STOCK: {symbol} ===")
    
    strategy = InstitutionalVCP()
    lookback = DynamicLookbackEngine.get_required_lookback(strategy)
    scan_date = date(2026, 7, 15)
    
    with get_sync_session() as session:
        stock_repo = StockRepository(session)
        stock = stock_repo.get_by_symbol(symbol)
        if not stock:
            print(f"Error: Stock {symbol} not found in DB.")
            return
            
        print(f"Stock identity: UUID={stock.stock_uuid}, symbol={stock.symbol}, exchange={stock.exchange}")
        
        # Step 3: Verify Historical Data
        repo = OHLCVRepository(session)
        start = scan_date - timedelta(days=int(lookback * 1.8))
        
        # Database History
        db_daily = repo.to_dataframe(stock.stock_uuid, start, scan_date, "1d")
        
        print(f"Required History (Lookback): {lookback} bars")
        print(f"Database History Count (Daily): {len(db_daily)}")
        print(f"Downloaded History (Latest daily date in DB): {db_daily.index[-1].date() if not db_daily.empty else 'None'}")
        
        history_complete = len(db_daily) >= lookback
        print(f"History Complete: {'YES' if history_complete else 'NO'}")
        
        if db_daily.empty:
            print("No daily history, skipping indicator calculation.")
            return
            
        # Step 4: Verify Indicator Engine
        benchmark = stock_repo.get_by_symbol(
            settings.scanner.benchmark_symbol,
            exchange=settings.scanner.benchmark_exchange,
        )
        benchmark_daily = None
        if benchmark:
            benchmark_daily = repo.to_dataframe(benchmark.stock_uuid, start, scan_date, "1d")
            print(f"Benchmark History Count: {len(benchmark_daily) if benchmark_daily is not None else 0}")
            
        bundle = IndicatorCalculator.build(db_daily, benchmark_daily if benchmark_daily is not None and not benchmark_daily.empty else None)
        df_indicators = bundle.daily
        weekly_indicators = bundle.weekly
        
        last_row = df_indicators.iloc[-1]
        last_weekly = weekly_indicators.iloc[-1]
        
        print("\n--- Calculated Indicators for Last Row ---")
        indicators_to_check = [
            "sma_50", "sma_150", "sma_200", "atr_14", "rs_score", 
            "vol_50", "high_252", "low_252"
        ]
        for ind in indicators_to_check:
            val = last_row.get(ind, np.nan)
            print(f"{ind}: {val} (NaN: {pd.isna(val)})")
            
        print("30 Week SMA (Weekly):", last_weekly.get("sma_30w", np.nan))
        
        # Step 5: Verify Strategy Execution
        print("\n--- Strategy Rules Evaluation ---")
        explanation = {}
        
        # Rule 1: Liquidity
        passed_liq = bool(last_row["turnover_50"] >= 10_000_000 and last_row["vol_50"] >= 100_000)
        print(f"Liquidity: {'PASS' if passed_liq else 'FAIL'} (turnover_50={last_row.get('turnover_50')}, vol_50={last_row.get('vol_50')})")
        explanation["Liquidity"] = {"status": "PASS" if passed_liq else "FAIL"}
        
        # Rule 2: Trend
        trend_template = all(
            [
                last_row["close"] > last_row["sma_150"],
                last_row["close"] > last_row["sma_200"],
                last_row["sma_150"] > last_row["sma_200"],
                last_row["sma_50"] > last_row["sma_150"],
                last_row["sma_50"] > last_row["sma_200"],
                last_row["close"] > last_row["sma_50"],
                last_row["sma_200_slope_20"] > 0,
                last_row["close"] >= 1.30 * last_row["low_252"],
                last_row["close"] >= 0.75 * last_row["high_252"],
            ]
        )
        print(f"Trend: {'PASS' if trend_template else 'FAIL'}")
        explanation["Trend"] = {"status": "PASS" if trend_template else "FAIL"}
        
        # Rule 3: Stage
        passed_stage = bool(last_weekly.get("stage", 0) == 2 or last_weekly.get("stage2", False))
        print(f"Stage: {'PASS' if passed_stage else 'FAIL'} (stage={last_weekly.get('stage')}, stage2={last_weekly.get('stage2')})")
        explanation["Stage"] = {"status": "PASS" if passed_stage else "FAIL"}
        
        # Rule 4: Relative Strength
        passed_rs = bool(last_row["rs_score"] > 0.0)
        print(f"Relative Strength: {'PASS' if passed_rs else 'FAIL'} (rs_score={last_row.get('rs_score')})")
        explanation["Relative Strength"] = {"status": "PASS" if passed_rs else "FAIL"}
        
        # Rule 5: VCP
        vcp_result = strategy._detect_vcp(df_indicators)
        vcp_passed = vcp_result.get("passed", False)
        print(f"VCP: {'PASS' if vcp_passed else 'FAIL'} (result={vcp_result})")
        explanation["VCP"] = {"status": "PASS" if vcp_passed else "FAIL"}
        
        # Rule 6: Breakout
        breakout_pivot = vcp_result.get("pivot", min(float(df_indicators.iloc[-20:-1]["high"].max()), float(last_weekly["high_13w"])))
        breakout_pass = bool(last_row["close"] > breakout_pivot and last_row["volume"] >= 1.5 * last_row["vol_50"])
        print(f"Breakout: {'PASS' if breakout_pass else 'FAIL'} (pivot={breakout_pivot}, close={last_row['close']}, volume={last_row['volume']}, vol_50={last_row['vol_50']})")
        explanation["Breakout"] = {"status": "PASS" if breakout_pass else "FAIL"}
        
        # Rule 7: Risk
        stop_loss = max(float(last_row["low_20"]), float(last_row["close"] - 2 * last_row["atr_14"]))
        risk_per_share = float(last_row["close"] - stop_loss)
        risk_pct = risk_per_share / float(last_row["close"]) if last_row["close"] > 0 else 0
        risk_pass = 0 < risk_pct <= 0.10
        position_size = int(100000 * 0.01 / risk_per_share) if risk_per_share > 0 else 0
        allocation_pct = (position_size * float(last_row["close"])) / 100000 * 100 if position_size > 0 else 0.0
        passed_risk = risk_pass and position_size > 0 and allocation_pct <= 10.0
        print(f"Risk: {'PASS' if passed_risk else 'FAIL'} (stop_loss={stop_loss}, risk_pct={risk_pct*100:.2f}%, allocation_pct={allocation_pct:.2f}%)")
        explanation["Risk"] = {"status": "PASS" if passed_risk else "FAIL"}
        
        # Strategy generate_signals execution
        context = StrategyContext(
            symbol=stock.symbol,
            exchange=stock.exchange,
            daily=df_indicators,
            weekly=weekly_indicators,
            benchmark_daily=benchmark_daily,
            as_of_date=scan_date
        )
        signals = strategy.generate_signals(stock.symbol, context)
        print(f"Signals generated by strategy: {len(signals)}")
        if signals:
            print("Signal entry:", signals[0].entry_price, "Stop:", signals[0].stop_loss)
            
        # Step 8 & 9: Validator
        validator = RecommendationValidator()
        # We need validation run if we have signals, but let's mock one if we don't to see validator behavior
        if signals:
            validation = validator.validate(
                stock=stock,
                context=context,
                signal=signals[0],
                existing_signal_keys=set(),
                latest_daily_date=str(scan_date)
            )
            print(f"Validator Result: valid={validation.valid}, reason={validation.reason}")
        else:
            print("No signal to validate. Checking why:")
            # Print the first failed rule
            rules_in_order = ["Liquidity", "Trend", "Stage", "Relative Strength", "VCP", "Breakout", "Risk"]
            for r in rules_in_order:
                if explanation[r]["status"] == "FAIL":
                    print(f"First failed rule: {r}")
                    break

if __name__ == "__main__":
    asyncio.run(diagnose_stock("GAIL"))
