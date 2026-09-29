"""Runs the single self-correcting SQL agent (src/agent.py) twice over
eval/questions.jsonl: once with only context/points.md, once with the full
context (points.md + table_relationships.md + variables_infos.md). Both use
the same tool-use loop -- no planner, no verifier -- so this isolates the
effect of the extra context files specifically.

Usage: python scripts/run_context_experiment.py [--model MODEL_ID]
The default model is src/agent.py's module default (currently Haiku 4.5);
pass --model to override it for both configs, e.g. to compare against Opus.
"""

import argparse
import os
import sys

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.eval_harness import run_eval
from src.variants.agent_context_experiment import run_full_context, run_points_only


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=None, help="Override the model for both configs")
    parser.add_argument("--results-path", default="eval/results_context_experiment.csv")
    args = parser.parse_args()

    load_dotenv()
    variants = {
        "agent_points_only": lambda q: run_points_only(q, model=args.model),
        "agent_full_context": lambda q: run_full_context(q, model=args.model),
    }
    run_eval(variants, results_path=args.results_path)


if __name__ == "__main__":
    main()
