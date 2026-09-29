"""Variant A/B: the simplest possible pipeline -- one call to write SQL, run
it, one call to turn the result into an answer. No tool use, no retries: if
the SQL is wrong, this variant just fails. That's the point -- it's the
floor that 'with context' and 'multi_agent' are measured against.

`use_context` is the only difference between Variant A (no context) and
Variant B (with context) -- same code path, one flag, so the eval isolates
the effect of context specifically.
"""

import re

import anthropic

from src.context import build_context_text
from src.db import get_connection, run_query
from src.schema import build_schema_text
from src.variants.base import VariantResult

MODEL = "claude-haiku-4-5-20251001"

SQL_SYSTEM_TEMPLATE = """You are a tennis stats analyst. You answer questions by writing a single \
DuckDB SQL query against the tables described below.

Respond with ONLY the SQL query -- no explanation, no markdown code fences.

# Schema
{schema}

# Notes
{context}
"""

ANSWER_SYSTEM = """You are a tennis stats analyst. You were given a question, the SQL query \
used to answer it, and the query's result (or an error message if it failed). Give a short, \
direct natural-language answer citing the actual numbers. If the query errored, say so plainly."""


def _generate_sql(client: anthropic.Anthropic, question: str, schema: str, context: str) -> str:
    system_text = SQL_SYSTEM_TEMPLATE.format(schema=schema, context=context or "(none)")
    system = [{"type": "text", "text": system_text, "cache_control": {"type": "ephemeral"}}]
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": question}],
    )
    sql = "".join(b.text for b in response.content if b.type == "text").strip()
    sql = re.sub(r"^```(sql)?\s*|\s*```$", "", sql, flags=re.IGNORECASE).strip()
    tokens = response.usage.input_tokens + response.usage.output_tokens
    return sql, tokens


def _synthesize_answer(client: anthropic.Anthropic, question: str, sql: str, result_text: str) -> tuple:
    user_content = f"Question: {question}\n\nSQL:\n{sql}\n\nResult:\n{result_text}"
    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=ANSWER_SYSTEM,
        messages=[{"role": "user", "content": user_content}],
    )
    answer = "".join(b.text for b in response.content if b.type == "text")
    tokens = response.usage.input_tokens + response.usage.output_tokens
    return answer, tokens


def run_baseline(question: str, use_context: bool) -> VariantResult:
    client = anthropic.Anthropic()
    con = get_connection()

    schema = build_schema_text(con)
    context = build_context_text() if use_context else ""

    sql, sql_tokens = _generate_sql(client, question, schema, context)

    try:
        df, truncated = run_query(con, sql)
        result_text = df.to_csv(index=False)
        if truncated:
            result_text += f"\n(results truncated to {len(df)} rows)"
    except Exception as e:
        result_text = f"SQL error: {e}"

    answer, answer_tokens = _synthesize_answer(client, question, sql, result_text)

    return VariantResult(
        answer=answer,
        sql_log=[sql],
        num_llm_calls=2,
        total_tokens=sql_tokens + answer_tokens,
    )
