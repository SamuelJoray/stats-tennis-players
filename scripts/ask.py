"""CLI for the Milestone B agent (src/agent.py) -- the tool-use loop.

Usage: python scripts/ask.py "your question"
"""

import os
import sys

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent import TennisAgent


def main():
    if len(sys.argv) < 2:
        print('Usage: python scripts/ask.py "your question"')
        sys.exit(1)
    question = sys.argv[1]

    load_dotenv()
    agent = TennisAgent()
    result = agent.ask(question, verbose=True)

    print("\n--- ANSWER ---")
    print(result["answer"])


if __name__ == "__main__":
    main()
