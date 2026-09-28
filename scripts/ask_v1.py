"""Milestone A: the simplest possible thing that works.

One-shot prompt -> Claude writes a SQL query -> we run it -> print the
result. No tool use, no retries: if the SQL is wrong, this just fails. That
limitation is the motivation for Milestone B (src/agent.py).

Usage: python scripts/ask_v1.py "how many aces did Djokovic hit in 2023?"
"""

import os
import re
import sys

import anthropic
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.context import build_context_text
from src.db import get_connection, run_query
from src.schema import build_schema_text

MODEL = "claude-haiku-4-5-20251001"

SYSTEM_TEMPLATE = """You are a tennis stats analyst. You answer questions by writing a single \
DuckDB SQL query against the tables described below.

Respond with ONLY the SQL query -- no explanation, no markdown code fences, no trailing \
semicolon commentary. Just the raw SQL.

# Schema
{schema}

# Notes
{context}
"""


def generate_sql(client: anthropic.Anthropic, question: str, schema: str, context: str) -> str:
    system = SYSTEM_TEMPLATE.format(schema=schema, context=context or "(none yet)")
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": question}],
    )
    sql = "".join(b.text for b in response.content if b.type == "text").strip()
    # Strip markdown fences in case the model adds them anyway.
    sql = re.sub(r"^```(sql)?\s*|\s*```$", "", sql, flags=re.IGNORECASE).strip()
    return sql


def main():
    if len(sys.argv) < 2:
        print('Usage: python scripts/ask_v1.py "your question"')
        sys.exit(1)
    question = sys.argv[1]

    load_dotenv()
    client = anthropic.Anthropic()
    con = get_connection()

    schema = build_schema_text(con)
    context = build_context_text()

    sql = generate_sql(client, question, schema, context)
    print(f"--- SQL ---\n{sql}\n")

    df, truncated = run_query(con, sql)
    print(f"--- RESULT ({len(df)} rows{' truncated' if truncated else ''}) ---")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
