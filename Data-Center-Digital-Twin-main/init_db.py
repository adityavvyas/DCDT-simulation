import sqlite3
import os

DB_PATH = "db/telemetry.db"
os.makedirs("db", exist_ok=True)

schema = """
CREATE TABLE IF NOT EXISTS telemetry (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  entity_type TEXT, entity_id TEXT, timestamp_utc TEXT,
  server_workload_percent REAL, inlet_temp_c REAL, ambient_temp_c REAL,
  raw_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_telemetry_entity ON telemetry(entity_id);
"""

def main():
    if os.path.exists(DB_PATH):
        print(f"Database '{DB_PATH}' already exists. Skipping initialization.")
        return
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript(schema)
    conn.commit()
    conn.close()
    print("Initialized DB at", DB_PATH)

if __name__ == "__main__":
    main()

