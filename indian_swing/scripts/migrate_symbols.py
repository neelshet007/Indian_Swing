import asyncio
from sqlalchemy import select
from indian_swing.database.connection import get_sync_session
from indian_swing.database.models import Stock

def run_migration():
    """
    Strips '.NS' from any existing stock symbols in the database
    to enforce the canonical symbol standard.
    """
    print("Starting Symbol Migration...")
    with get_sync_session() as session:
        stocks = session.execute(select(Stock)).scalars().all()
        updated_count = 0
        
        for stock in stocks:
            if stock.symbol.endswith(".NS"):
                old_symbol = stock.symbol
                new_symbol = old_symbol[:-3]
                
                # Check if the new symbol already exists to prevent integrity errors
                existing = session.execute(select(Stock).where(Stock.symbol == new_symbol)).scalar_one_or_none()
                if existing:
                    print(f"Conflict: Canonical symbol {new_symbol} already exists. Deleting duplicate {old_symbol}.")
                    session.delete(stock)
                else:
                    stock.symbol = new_symbol
                    updated_count += 1
                
        session.commit()
        print(f"Migration complete. Updated {updated_count} symbols.")

if __name__ == "__main__":
    run_migration()
