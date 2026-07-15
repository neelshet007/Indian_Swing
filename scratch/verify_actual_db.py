import asyncio
from sqlalchemy import inspect, text
from indian_swing.database.connection import get_engine, init_db
from indian_swing.database.models import Base

async def verify():
    # First, print configuration and check connection
    engine = get_engine()
    print("Database URL:", engine.url)
    
    # Try connecting
    try:
        with engine.connect() as conn:
            print("Successfully connected to the database.")
            # Get list of tables
            inspector = inspect(engine)
            db_tables = inspector.get_table_names()
            print("Tables in Database:", db_tables)
            
            # Check model tables
            model_tables = Base.metadata.tables.keys()
            print("Tables in SQLAlchemy Models:", list(model_tables))
            
            for table_name in model_tables:
                print(f"\n--- Checking Table: {table_name} ---")
                if table_name not in db_tables:
                    print(f"ERROR: Table {table_name} does not exist in the database!")
                    continue
                
                # Check columns in DB
                db_cols = {col['name']: col for col in inspector.get_columns(table_name)}
                model_cols = Base.metadata.tables[table_name].columns
                
                print(f"Database columns: {list(db_cols.keys())}")
                print(f"Model columns: {list(model_cols.keys())}")
                
                # Compare columns
                for col_name, model_col in model_cols.items():
                    if col_name not in db_cols:
                        print(f"  [MISMATCH] Column '{col_name}' exists in MODEL but NOT in DATABASE.")
                    else:
                        db_col = db_cols[col_name]
                        # Check types roughly
                        print(f"  Column '{col_name}': Model={model_col.type}, DB={db_col['type']}, Nullable: Model={model_col.nullable}, DB={db_col['nullable']}")
                
                for col_name in db_cols:
                    if col_name not in model_cols:
                        print(f"  [MISMATCH] Column '{col_name}' exists in DATABASE but NOT in MODEL (Obsolete column).")
                        
                # Check foreign keys
                fks = inspector.get_foreign_keys(table_name)
                print(f"Foreign Keys: {fks}")
                
                # Check unique constraints/indexes
                indexes = inspector.get_indexes(table_name)
                print(f"Indexes: {indexes}")
                
    except Exception as e:
        print("Error connecting or inspecting:", e)

if __name__ == "__main__":
    asyncio.run(verify())
