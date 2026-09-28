"""Runs all three variants (no_context, with_context, multi_agent) over
eval/questions.jsonl, grades each answer with a normalized substring match,
and writes eval/results.csv plus a summary table to the console.

Usage: python scripts/run_eval.py
"""

import csv
import json
import os
import re
import sys
import time

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.variants.multi_agent import run_multi_agent
from src.variants.one_shot import run_baseline

QUESTIONS_PATH = "eval/questions.jsonl"
RESULTS_PATH = "eval/results.csv"

VARIANTS = {
    "no_context": lambda q: run_baseline(q, use_context=False),
    "with_context": lambda q: run_baseline(q, use_context=True),
    "multi_agent": lambda q: run_multi_agent(q),
}


def load_questions():
    questions = []
    with open(QUESTIONS_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                questions.append(json.loads(line))
    return questions


def normalize(text: str) -> str:
    text = text.lower().replace(",", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def grade(expected: str, actual: str) -> bool:
    return normalize(expected) in normalize(actual)


def main():
    load_dotenv()
    questions = load_questions()

    rows = []
    for variant_name, run_fn in VARIANTS.items():
        print(f"\n=== {variant_name} ===")
        for q in questions:
            start = time.perf_counter()
            try:
                result = run_fn(q["question"])
                answer = result.answer
                sql_log = result.sql_log
                num_llm_calls = result.num_llm_calls
                total_tokens = result.total_tokens
                error = ""
            except Exception as e:
                answer, sql_log, num_llm_calls, total_tokens = "", [], 0, 0
                error = str(e)
            latency_s = time.perf_counter() - start

            correct = grade(q["expected_answer"], answer) if not error else False
            status = "OK" if correct else "MISS"
            print(f"[{status}] {q['id']}: {q['question'][:60]}")

            rows.append(
                {
                    "variant": variant_name,
                    "question_id": q["id"],
                    "question": q["question"],
                    "expected_answer": q["expected_answer"],
                    "actual_answer": answer,
                    "correct": correct,
                    "num_llm_calls": num_llm_calls,
                    "total_tokens": total_tokens,
                    "latency_s": round(latency_s, 2),
                    "sql_log": " ;; ".join(sql_log),
                    "error": error,
                }
            )

    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nWrote {RESULTS_PATH}")

    print("\n=== Summary ===")
    print(f"{'variant':<14} {'accuracy':>10} {'avg_calls':>10} {'avg_tokens':>11} {'avg_latency_s':>14}")
    for variant_name in VARIANTS:
        variant_rows = [r for r in rows if r["variant"] == variant_name]
        n = len(variant_rows)
        accuracy = sum(r["correct"] for r in variant_rows) / n * 100
        avg_calls = sum(r["num_llm_calls"] for r in variant_rows) / n
        avg_tokens = sum(r["total_tokens"] for r in variant_rows) / n
        avg_latency = sum(r["latency_s"] for r in variant_rows) / n
        print(f"{variant_name:<14} {accuracy:>9.1f}% {avg_calls:>10.1f} {avg_tokens:>11.0f} {avg_latency:>14.1f}")


if __name__ == "__main__":
    main()
