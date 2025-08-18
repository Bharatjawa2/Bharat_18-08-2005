import sqlite3, os, pandas as pd

DATA_DIR = "data"
DB_PATH = "data.db"

def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS polls (
        store_id TEXT,
        timestamp_utc TEXT,
        status TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS business_hours (
        store_id TEXT,
        dayOfWeek INTEGER,
        start_time_local TEXT,
        end_time_local TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS timezones (
        store_id TEXT,
        timezone_str TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        report_id TEXT PRIMARY KEY,
        status TEXT,
        csv_path TEXT,
        created_at TEXT
    )""")
    conn.commit()

    def table_empty(name):
        cur.execute(f"SELECT COUNT(1) FROM {name}")
        return cur.fetchone()[0] == 0

    polls_csv = os.path.join(DATA_DIR, "store_status.csv")
    bh_csv = os.path.join(DATA_DIR, "menu_hours.csv")
    tz_csv = os.path.join(DATA_DIR, "timezones.csv")

    if table_empty("polls") and os.path.exists(polls_csv):
        for chunk in pd.read_csv(polls_csv, chunksize=50_000):
            chunk.to_sql("polls", conn, if_exists="append", index=False, method="multi", chunksize=250)
    if table_empty("business_hours") and os.path.exists(bh_csv):
        pd.read_csv(bh_csv).to_sql("business_hours", conn, if_exists="append", index=False, method="multi", chunksize=500)
    if table_empty("timezones") and os.path.exists(tz_csv):
        pd.read_csv(tz_csv).to_sql("timezones", conn, if_exists="append", index=False, method="multi", chunksize=500)

    conn.close()
