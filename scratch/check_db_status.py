import asyncio
from sqlalchemy import select, func
from indian_swing.database.connection import get_engine, get_sync_session
from indian_swing.database.models import Stock, OHLCV, ScanJob, Signal, Recommendation

async def check():
    with get_sync_session() as session:
        stocks_count = session.query(func.count(Stock.stock_uuid)).scalar()
        ohlcv_count = session.query(func.count(OHLCV.id)).scalar()
        jobs_count = session.query(func.count(ScanJob.scan_uuid)).scalar()
        signals_count = session.query(func.count(Signal.id)).scalar()
        recs_count = session.query(func.count(Recommendation.id)).scalar()
        
        print(f"Stocks count: {stocks_count}")
        print(f"OHLCV records count: {ohlcv_count}")
        print(f"Scan jobs count: {jobs_count}")
        print(f"Signals count: {signals_count}")
        print(f"Recommendations count: {recs_count}")
        
        # Check active stocks
        active_stocks = session.query(Stock).filter(Stock.is_active == True).limit(5).all()
        print("\nSome active stocks:")
        for s in active_stocks:
            print(f"- {s.symbol} ({s.name}), is_active={s.is_active}")
            
        # Check coverage
        if active_stocks:
            print("\nCoverage for some stocks:")
            for s in active_stocks:
                c_1d = session.query(func.count(OHLCV.id)).filter(OHLCV.stock_uuid == s.stock_uuid, OHLCV.timeframe == "1d").scalar()
                c_1w = session.query(func.count(OHLCV.id)).filter(OHLCV.stock_uuid == s.stock_uuid, OHLCV.timeframe == "1wk").scalar()
                c_1m = session.query(func.count(OHLCV.id)).filter(OHLCV.stock_uuid == s.stock_uuid, OHLCV.timeframe == "1mo").scalar()
                print(f"Stock {s.symbol}: 1d count = {c_1d}, 1wk count = {c_1w}, 1mo count = {c_1m}")

        # Check scan jobs
        jobs = session.query(ScanJob).order_by(ScanJob.created_at.desc()).limit(5).all()
        print("\nLast 5 Scan Jobs:")
        for j in jobs:
            print(f"- UUID={j.scan_uuid}, date={j.scan_date}, status={j.status}, total={j.total_stocks}, scanned={j.stocks_scanned}, signals={j.signals_generated}, recs={j.recommendations_created}, error={j.error}")

if __name__ == "__main__":
    asyncio.run(check())
