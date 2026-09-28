"""Variant C: Planner -> SQL agent -> Verifier.

- Planner (text-only): sketches a plan for how to answer the question,
  without writing SQL itself.
- SQL agent: reuses the self-correcting tool-use loop from src/agent.py
  (TennisAgent) to actually write and run SQL, given the plan as guidance.
- Verifier (text-only): reviews the SQL agent's answer and SQL log, and can
  send it back for exactly one revision if something looks wrong.
"""

import anthropic

from src.agent import TennisAgent
from src.context import build_context_text
from src.db import get_connection
from src.schema import build_schema_text
from src.variants.base import VariantResult

MODEL = "claude-haiku-4-5-20251001"

PLANNER_SYSTEM = """You are a query planning assistant for a tennis stats database. Given a \
question and the schema below, write a short (3-6 step) natural-language plan for how to \
answer it with SQL: which table(s) to use, what to filter/join on, what to count or aggregate, \
and any pitfalls to watch for (e.g. per-set vs. total rows, tour filtering). Do NOT write SQL \
yourself -- just the plan.

# Schema
{schema}

# Notes
{context}
"""

VERIFIER_SYSTEM = """You are a verifier checking another analyst's work on a tennis stats \
question. You'll be given the question, the SQL query they ran, and the answer they produced. \
Check for logical problems: wrong filters, double-counting (e.g. summing per-set rows plus a \
Total row), ignoring the tour column when it matters, misreading the question, etc.

If the answer looks correct, respond with exactly:
APPROVE: <the answer, possibly cleaned up>

If you find a real problem, respond with exactly:
REVISE: <specific, actionable feedback for what to fix>
"""


def _call_planner(client: anthropic.Anthropic, question: str, schema: str, context: str) -> tuple:
    system = PLANNER_SYSTEM.format(schema=schema, context=context or "(none)")
    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": question}],
    )
    plan = "".join(b.text for b in response.content if b.type == "text")
    tokens = response.usage.input_tokens + response.usage.output_tokens
    return plan, tokens


def _call_verifier(client: anthropic.Anthropic, question: str, sql_log: list, answer: str) -> tuple:
    sql_text = "\n---\n".join(sql_log)
    user_content = f"Question: {question}\n\nSQL run:\n{sql_text}\n\nAnswer given:\n{answer}"
    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=VERIFIER_SYSTEM,
        messages=[{"role": "user", "content": user_content}],
    )
    verdict = "".join(b.text for b in response.content if b.type == "text")
    tokens = response.usage.input_tokens + response.usage.output_tokens
    return verdict, tokens


def run_multi_agent(question: str) -> VariantResult:
    client = anthropic.Anthropic()
    con = get_connection()
    schema = build_schema_text(con)
    context = build_context_text()

    sql_log = []
    num_llm_calls = 0
    total_tokens = 0

    plan, tokens = _call_planner(client, question, schema, context)
    num_llm_calls += 1
    total_tokens += tokens

    sql_agent = TennisAgent(use_context=True)
    result = sql_agent.ask(f"{question}\n\nA colleague suggested this plan:\n{plan}")
    sql_log += result["sql_log"]
    num_llm_calls += result["num_llm_calls"]
    total_tokens += result["total_tokens"]
    answer = result["answer"]

    verdict, tokens = _call_verifier(client, question, sql_log, answer)
    num_llm_calls += 1
    total_tokens += tokens

    if verdict.strip().startswith("REVISE:"):
        feedback = verdict.split("REVISE:", 1)[1].strip()
        retry = sql_agent.ask(
            f"{question}\n\nYour previous answer was: {answer}\n\n"
            f"A reviewer found this problem: {feedback}\n\nPlease address it and give a final answer."
        )
        sql_log += retry["sql_log"]
        num_llm_calls += retry["num_llm_calls"]
        total_tokens += retry["total_tokens"]
        answer = retry["answer"]
    elif verdict.strip().startswith("APPROVE:"):
        answer = verdict.split("APPROVE:", 1)[1].strip()

    return VariantResult(
        answer=answer,
        sql_log=sql_log,
        num_llm_calls=num_llm_calls,
        total_tokens=total_tokens,
    )
