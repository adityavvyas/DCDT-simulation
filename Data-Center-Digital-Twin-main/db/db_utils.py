import sqlite3
from typing import List, Tuple

DEFAULT_DB = "db/telemetry.db"

COLUMNS = ["entity_id", "server_workload_percent", "inlet_temp_c", "ambient_temp_c"]
INSERT_SQL = "INSERT INTO telemetry (entity_id, server_workload_percent, inlet_temp_c, ambient_temp_c) VALUES (?, ?, ?, ?)"

def get_conn(db_path: str = DEFAULT_DB) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=15)
    conn.row_factory = sqlite3.Row
    return conn

def insert_telemetry_row(conn: sqlite3.Connection, row: Tuple) -> int:
    cur = conn.cursor()
    cur.execute(INSERT_SQL, row)
    conn.commit()
    return cur.lastrowid

def get_all_scenarios(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    """Fetches all initial payload data needed for the simulation."""
    cur = conn.cursor()
    sql = f"SELECT {', '.join(COLUMNS)} FROM telemetry ORDER BY entity_id, id"
    cur.execute(sql)
    return cur.fetchall()

