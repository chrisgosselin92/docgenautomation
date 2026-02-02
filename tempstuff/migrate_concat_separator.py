# migrate_concat_separator.py
import sqlite3
from pathlib import Path

DB_PATH = Path("data/clients.db")
CONCAT_TABLE = "concat_variables"

def migrate_separator_column():
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Ensure the concat_variables table exists
    c.execute(f"""
        CREATE TABLE IF NOT EXISTS {CONCAT_TABLE} (
            var_name TEXT PRIMARY KEY,
            components TEXT,
            description TEXT,
            var_type TEXT,
            category TEXT
        )
    """)

    # Check existing columns
    c.execute(f"PRAGMA table_info({CONCAT_TABLE})")
    cols = [r[1] for r in c.fetchall()]

    if "separator" not in cols:
        print("Adding missing 'separator' column to concat_variables...")
        c.execute(f"ALTER TABLE {CONCAT_TABLE} ADD COLUMN separator TEXT DEFAULT ' '")
    else:
        print("'separator' column already exists, nothing to do.")

    conn.commit()
    conn.close()
    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate_separator_column()
