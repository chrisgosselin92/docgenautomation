# check_db.py
import sqlite3
from pathlib import Path

DB_PATH = Path("data/clients.db")

print("=" * 60)
print("DATABASE DIAGNOSTIC CHECK")
print("=" * 60)

if not DB_PATH.exists():
    print(f"❌ ERROR: Database file does not exist at {DB_PATH}")
    exit(1)

print(f"✓ Database file found: {DB_PATH}")
print()

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Check if opposing_counsel table exists
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='opposing_counsel'")
table_exists = c.fetchone()

if not table_exists:
    print("❌ ERROR: 'opposing_counsel' table does NOT exist!")
    print("\nAvailable tables:")
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    for row in c.fetchall():
        print(f"  - {row[0]}")
    conn.close()
    exit(1)

print("✓ 'opposing_counsel' table exists")
print()

# Check table schema
print("Table schema:")
c.execute("PRAGMA table_info(opposing_counsel)")
columns = c.fetchall()
for col in columns:
    print(f"  {col[1]} ({col[2]})")
print()

# Count records
c.execute("SELECT COUNT(*) FROM opposing_counsel")
count = c.fetchone()[0]
print(f"Total attorney records: {count}")
print()

if count == 0:
    print("⚠️  WARNING: No attorneys in database!")
else:
    print("Attorney records:")
    print("-" * 60)
    c.execute("SELECT id, first_name, last_name, firm_name, email FROM opposing_counsel")
    for row in c.fetchall():
        print(f"  ID: {row[0]}")
        print(f"  Name: {row[1]} {row[2]}")
        print(f"  Firm: {row[3] or '(none)'}")
        print(f"  Email: {row[4] or '(none)'}")
        print("-" * 60)

# Check if any clients have assigned attorneys
print("\nClient attorney assignments:")
c.execute("SELECT COUNT(*) FROM clients WHERE opposing_counsel_id IS NOT NULL")
assigned_count = c.fetchone()[0]
print(f"Clients with assigned attorneys: {assigned_count}")

if assigned_count > 0:
    c.execute("SELECT id, opposing_counsel_id FROM clients WHERE opposing_counsel_id IS NOT NULL")
    print("\nAssigned clients:")
    for row in c.fetchall():
        print(f"  Client ID {row[0]} → Attorney ID {row[1]}")

conn.close()

print()
print("=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)