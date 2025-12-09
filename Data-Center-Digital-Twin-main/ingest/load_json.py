import os
import sys
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from db.db_utils import get_conn, insert_telemetry_row
from ingest.normalizer import normalize_doc, record_tuple_from_normalized

DB_PATH = "db/telemetry.db"
INPUT = "data/sample.json"

def main():
    if not os.path.exists(INPUT):
        print(f"Input JSON not found: {INPUT}")
        return

    with open(INPUT, "r") as f:
        data = json.load(f)

    docs = data if isinstance(data, list) else [data]
    conn = get_conn(DB_PATH)
    inserted = 0
    for doc in docs:
        try:
            normalized = normalize_doc(doc)
            row_tuple = record_tuple_from_normalized(normalized)
            insert_telemetry_row(conn, row_tuple)
            inserted += 1
        except Exception as e:
            print(f"Failed to insert record: {e}")
    conn.close()
    print(f"Inserted {inserted} records into {DB_PATH}")

if __name__ == "__main__":
    main()

