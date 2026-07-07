from indian_swing.database.connection import get_sync_session
from sqlalchemy import text

def check_pfc():
    with get_sync_session() as session:
        res = session.execute(text("SELECT id, symbol, name FROM sw_stocks WHERE symbol='PFC';"))
        print("PFC stock:", res.fetchall())
        
        # Let's also check if there are other signals in sw_signals
        res2 = session.execute(text("SELECT id, stock_id, entry_price, signal_date FROM sw_signals;"))
        print("All signals:")
        for r in res2.fetchall():
            s_symbol = session.execute(text(f"SELECT symbol FROM sw_stocks WHERE id={r[1]};")).scalar()
            print(f"Signal ID: {r[0]}, Stock ID: {r[1]} ({s_symbol}), Entry: {r[2]}, Date: {r[3]}")

if __name__ == "__main__":
    check_pfc()
