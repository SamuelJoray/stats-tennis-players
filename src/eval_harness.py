"""Shared harness: run a set of named variants over an eval/*.jsonl question
set, grade each answer with a normalized substring match, write a results
CSV, and print a per-variant summary table.

Used by scripts/run_eval.py (the no_context/with_context/multi_agent
architecture comparison) and scripts/run_context_experiment.py (the
points-only vs full-context comparison) so the running/grading/reporting
logic isn't duplicated between the two.
"""

import csv
import json
import os
import re
import time

QUESTIONS_PATH = "eval/questions.jsonl"
RESULTS_PATH = "eval/results.csv"


def load_questions(path: str = QUESTIONS_PATH):
    questions = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                questions.append(json.loads(line))
    return questions


TOLERANCE = 0.02  # 2% relative -- a different but defensible methodology
# (e.g. COUNT(*) vs COUNT(DISTINCT match_id) on data with a few duplicate
# keys) often lands within a percent or two of the "expected" number without
# being wrong. A strict substring match punished that; this doesn't.

NUMBER_RE = re.compile(r"-?\d[\d,]*\.?\d*")


def normalize(text: str) -> str:
    text = text.lower().replace(",", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_numbers(text: str) -> list:
    numbers = []
    for match in NUMBER_RE.finditer(text):
        try:
            numbers.append(float(match.group().replace(",", "")))
        except ValueError:
            continue
    return numbers


def grade(expected: str, actual: str, tolerance: float = TOLERANCE) -> bool:
    """Numeric answers are graded within a relative tolerance -- any number
    in the (free-form) actual answer that's close enough to the expected
    value counts as correct, not just an exact substring match. Falls back
    to a normalized substring match for non-numeric expected answers."""
    try:
        expected_num = float(expected.replace(",", "").replace("%", "").strip())
    except ValueError:
        expected_num = None

    if expected_num is not None:
        for num in extract_numbers(actual):
            if expected_num == 0:
                if num == 0:
                    return True
            elif abs(num - expected_num) / abs(expected_num) <= tolerance:
                return True
        return False

    return normalize(expected) in normalize(actual)


def run_eval(variants: dict, questions_path: str = QUESTIONS_PATH, results_path: str = RESULTS_PATH):
    """`variants` maps a name to a callable(question: str) -> VariantResult
    (see src/variants/base.py). Returns the list of per-question result rows."""
    questions = load_questions(questions_path)

    rows = []
    for variant_name, run_fn in variants.items():
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

    os.makedirs(os.path.dirname(results_path), exist_ok=True)
    with open(results_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nWrote {results_path}")

    print("\n=== Summary ===")
    print(f"{'variant':<20} {'accuracy':>10} {'avg_calls':>10} {'avg_tokens':>11} {'avg_latency_s':>14}")
    for variant_name in variants:
        variant_rows = [r for r in rows if r["variant"] == variant_name]
        n = len(variant_rows)
        accuracy = sum(r["correct"] for r in variant_rows) / n * 100
        avg_calls = sum(r["num_llm_calls"] for r in variant_rows) / n
        avg_tokens = sum(r["total_tokens"] for r in variant_rows) / n
        avg_latency = sum(r["latency_s"] for r in variant_rows) / n
        print(f"{variant_name:<20} {accuracy:>9.1f}% {avg_calls:>10.1f} {avg_tokens:>11.0f} {avg_latency:>14.1f}")

    return rows
