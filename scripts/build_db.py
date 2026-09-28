"""One-time ETL: load all Match Charting Project CSVs into tennis.duckdb.

Run with: python scripts/build_db.py
Re-run any time to rebuild from scratch (drops and recreates every table).
"""

import os
import sys

import duckdb

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tables import DATA_DIR, TABLES

DB_PATH = "tennis.duckdb"


def build():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    con = duckdb.connect(DB_PATH)

    for table_name, pattern in TABLES.items():
        m_glob = os.path.join(DATA_DIR, pattern.format(g="m")).replace("\\", "/")
        w_glob = os.path.join(DATA_DIR, pattern.format(g="w")).replace("\\", "/")

        read_opts = "union_by_name=true, null_padding=true"
        sql = f"""
            CREATE TABLE {table_name} AS
            SELECT *, 'M' AS tour FROM read_csv('{m_glob}', {read_opts})
            UNION ALL BY NAME
            SELECT *, 'W' AS tour FROM read_csv('{w_glob}', {read_opts})
        """
        con.execute(sql)
        count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"{table_name:24s} {count:>10,d} rows")

    con.close()
    print(f"\nBuilt {DB_PATH}")


if __name__ == "__main__":
    build()
