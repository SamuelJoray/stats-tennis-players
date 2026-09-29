"""Runs the three architecture variants (no_context, with_context,
multi_agent) over eval/questions.jsonl, grades each answer with a normalized
substring match, and writes eval/results.csv plus a summary table.

Usage: python scripts/run_eval.py
"""

import os
import sys

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.eval_harness import run_eval
from src.variants.multi_agent import run_multi_agent
from src.variants.one_shot import run_baseline

VARIANTS = {
    "no_context": lambda q: run_baseline(q, use_context=False),
    "with_context": lambda q: run_baseline(q, use_context=True),
    "multi_agent": lambda q: run_multi_agent(q),
}


def main():
    load_dotenv()
    run_eval(VARIANTS)


if __name__ == "__main__":
    main()
