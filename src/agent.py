"""Milestone B: an agentic tool-use loop instead of one-shot SQL generation.

Instead of asking Claude to output SQL blind, we give it a `run_sql` tool.
Claude can call it, see the actual result (or error) come back, and decide
whether to try again or answer. This is the function/tool-calling pattern
(sometimes called ReAct: reason, act, observe, repeat) -- it's what lets the
agent self-correct on a bad column name or a typo instead of just failing.
"""

import os

import anthropic

from src.context import build_context_text
from src.db import get_connection, run_query
from src.schema import build_schema_text

MODEL = "claude-haiku-4-5-20251001"
MAX_TOOL_CALLS = 5

SYSTEM_TEMPLATE = """You are a tennis stats analyst assistant. You answer questions about \
professional tennis matches by writing and running DuckDB SQL queries via the `run_sql` tool \
against the tables described below.

Guidelines:
- Write one query at a time, look at the result, and adjust if it errors or looks wrong.
- The `tour` column ('M' or 'W') distinguishes men's and women's matches -- filter on it \
when the question implies one tour, and include it in results when comparing.
- Many -stats- tables have per-set rows plus a 'Total'/'total' row (in a `set` or `row` \
column) -- make sure you aren't double-counting when a question wants match totals.
- When you have enough information, give a clear, concise natural-language final answer \
citing the actual numbers you found. Do not just dump a table.

# Schema
{schema}

# Notes
{context}
"""

RUN_SQL_TOOL = {
    "name": "run_sql",
    "description": "Execute a read-only DuckDB SQL query against the tennis database and return the results.",
    "input_schema": {
        "type": "object",
        "properties": {
            "sql": {"type": "string", "description": "The SQL query to run."},
        },
        "required": ["sql"],
    },
}


class TennisAgent:
    def __init__(self, use_context: bool = True):
        self.client = anthropic.Anthropic()
        self.con = get_connection()
        schema = build_schema_text(self.con)
        context = build_context_text() if use_context else ""
        self.system = SYSTEM_TEMPLATE.format(schema=schema, context=context or "(none yet)")

    def _execute_tool(self, sql: str):
        try:
            df, truncated = run_query(self.con, sql)
            text = df.to_csv(index=False)
            if truncated:
                text += f"\n(results truncated to {len(df)} rows)"
            return text, False
        except Exception as e:
            return f"SQL error: {e}", True

    def ask(self, question: str, verbose: bool = False) -> dict:
        """Runs the tool-use loop.

        Returns {"answer": str, "sql_log": [str, ...], "num_llm_calls": int,
        "total_tokens": int}.
        """
        messages = [{"role": "user", "content": question}]
        sql_log = []
        num_llm_calls = 0
        total_tokens = 0

        for _ in range(MAX_TOOL_CALLS):
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=self.system,
                tools=[RUN_SQL_TOOL],
                messages=messages,
            )
            num_llm_calls += 1
            total_tokens += response.usage.input_tokens + response.usage.output_tokens

            messages.append({"role": "assistant", "content": response.content})

            tool_calls = [b for b in response.content if b.type == "tool_use"]
            if not tool_calls:
                final_text = "".join(b.text for b in response.content if b.type == "text")
                return {
                    "answer": final_text,
                    "sql_log": sql_log,
                    "num_llm_calls": num_llm_calls,
                    "total_tokens": total_tokens,
                }

            tool_results = []
            for call in tool_calls:
                sql = call.input["sql"]
                sql_log.append(sql)
                if verbose:
                    print(f"[run_sql] {sql}")
                result_text, is_error = self._execute_tool(sql)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": call.id,
                        "content": result_text,
                        "is_error": is_error,
                    }
                )
            messages.append({"role": "user", "content": tool_results})

        return {
            "answer": "I couldn't settle on a final answer within the tool-call budget.",
            "sql_log": sql_log,
            "num_llm_calls": num_llm_calls,
            "total_tokens": total_tokens,
        }
