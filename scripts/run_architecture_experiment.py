"""Runs two Haiku-powered agents over eval/questions.jsonl, both given the
full context (points.md + table_relationships.md + variables_infos.md), to
isolate the effect of architecture alone:
- single_agent: the self-correcting tool-use loop (src/agent.py), no planner/verifier.
- multi_agent: planner -> that same SQL agent -> verifier (src/variants/multi_agent.py).

Usage: python scripts/run_architecture_experiment.py
"""

import os
import sys

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.eval_harness import run_eval
from src.variants.agent_context_experiment import run_full_context
from src.variants.multi_agent import run_multi_agent

VARIANTS = {
    "single_agent_full_context": run_full_context,
    "multi_agent_full_context": run_multi_agent,
}


def main():
    load_dotenv()
    run_eval(VARIANTS, results_path="eval/results_architecture_experiment.csv")


if __name__ == "__main__":
    main()
