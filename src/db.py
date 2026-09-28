"""Read-only access to tennis.duckdb.

Opening with read_only=True is a structural guarantee against mutation --
no query the LLM writes, however malformed, can ever alter the data. That's
a stronger guarantee than trying to regex-filter for "SELECT only".
"""

import duckdb

DB_PATH = "tennis.duckdb"
MAX_ROWS = 200


def get_connection() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(DB_PATH, read_only=True)


def run_query(con: duckdb.DuckDBPyConnection, sql: str):
    """Executes SQL and returns (dataframe, truncated: bool)."""
    if not sql or not sql.strip():
        raise ValueError("empty SQL query")
    result = con.execute(sql)
    if result is None:
        raise ValueError(f"query produced no result (is it a real SELECT?): {sql!r}")
    df = result.df()
    truncated = len(df) > MAX_ROWS
    if truncated:
        df = df.head(MAX_ROWS)
    return df, truncated
