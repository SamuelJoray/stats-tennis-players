"""Serializes the DuckDB schema into a compact text block for the LLM prompt.

LLMs don't know your database schema out of the box -- this is the
"grounding" step: turn `DESCRIBE` + a few sample values into text the model
can read alongside the user's question.
"""

import duckdb

from src.tables import TABLES

# Columns worth showing sample values for -- low-cardinality codes that are
# meaningless from the name alone (e.g. Svr=1/2, tour='M'/'W').
SAMPLE_VALUE_COLUMNS = {"tour", "Svr", "Ret", "row", "set", "TbSet", "TB?"}

MAX_SAMPLE_VALUES = 8


def build_schema_text(con: duckdb.DuckDBPyConnection) -> str:
    sections = []
    for table_name in TABLES:
        columns = con.execute(f"DESCRIBE {table_name}").fetchall()
        lines = [f"TABLE {table_name}"]
        for col_name, col_type, *_ in columns:
            line = f"  - {col_name} ({col_type})"
            if col_name in SAMPLE_VALUE_COLUMNS:
                samples = con.execute(
                    f'SELECT DISTINCT "{col_name}" FROM {table_name} '
                    f'WHERE "{col_name}" IS NOT NULL LIMIT {MAX_SAMPLE_VALUES}'
                ).fetchall()
                values = ", ".join(repr(s[0]) for s in samples)
                line += f" e.g. {values}"
            lines.append(line)
        sections.append("\n".join(lines))
    return "\n\n".join(sections)


if __name__ == "__main__":
    con = duckdb.connect("tennis.duckdb", read_only=True)
    print(build_schema_text(con))
