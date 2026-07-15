from indian_swing.database.connection import get_engine
from sqlalchemy import inspect

def add_column():
    engine = get_engine()
    inspector = inspect(engine)
    for col in inspector.get_columns('sw_ohlcv'):
        print(f"sw_ohlcv column: {col['name']} - Type: {col['type']}")
    for col in inspector.get_columns('sw_stocks'):
        print(f"sw_stocks column: {col['name']} - Type: {col['type']}")

if __name__ == "__main__":
    add_column()
