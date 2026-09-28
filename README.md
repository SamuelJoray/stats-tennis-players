# Tennis Stats Q&A Agent

Ask questions about professional tennis matches in plain English and get answers backed by real SQL. A Streamlit chat app sends your question to Claude, which writes and runs SQL against a local DuckDB database, then explains the result.

The project also includes a small experiment comparing three ways of answering: no domain context, with domain context, and a planner/SQL-agent/verifier multi-agent pipeline.

## Data & credits

All of the underlying data comes from **[The Match Charting Project](https://github.com/JeffSackmann/tennis_MatchChartingProject)** (MCP), created and maintained by **Jeff Sackmann**. MCP is a crowdsourced effort that has produced detailed, shot-by-shot charting for thousands of professional matches — data that isn't available anywhere else publicly. If you work with this data, consider [contributing a chart of your own](http://www.tennisabstract.com/blog/2015/09/23/the-match-charting-project-quick-start-guide/).

The MCP data is licensed [CC BY-NC-SA 4.0](http://creativecommons.org/licenses/by-nc-sa/4.0/) — **attribution required, non-commercial use only**. This repo does not redistribute the data: `tennis_MatchChartingProject/` is gitignored here and expected to be cloned separately (see Setup).

## What it does

- **`app.py`** — a Streamlit chat UI. Type a question, Claude writes SQL, runs it against `tennis.duckdb`, and answers in plain English. Each answer's SQL and result table are shown in an expander for transparency.
- Under the hood, the schema of every table and a hand-written glossary of MCP's shot-charting notation (the cryptic `1st`/`2nd` point-log codes, e.g. `4f8b2f3b1f#`) are injected into the model's prompt so it can actually make sense of the data (see `src/schema.py`, `src/context.py`, `context/points.md`).

## Setup

```bash
# 1. Clone the MCP data alongside this repo's code
git clone https://github.com/JeffSackmann/tennis_MatchChartingProject.git

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your Anthropic API key
cp .env.example .env   # then edit .env

# 4. Build the local database (one-time; ~18 tables, a few minutes)
python scripts/build_db.py

# 5. Run the app
streamlit run app.py
```

## Architecture

| File | Role |
|---|---|
| `src/tables.py`, `scripts/build_db.py` | ETL: loads every men's/women's CSV (matches, points, and all 16 `-stats-*` categories) into `tennis.duckdb`, unioned into one table per category with a `tour` (`M`/`W`) column. |
| `src/schema.py` | Introspects the database and serializes columns/types/sample values into prompt text — the model's only source of schema knowledge. |
| `src/context.py`, `context/` | Loads hand-written domain notes (e.g. the shot-notation glossary) that schema alone can't convey. |
| `src/db.py` | Read-only DB access with a row cap — the model's SQL can never mutate data. |
| `src/agent.py` | The agent used by the Streamlit app: gives Claude a `run_sql` tool and lets it iterate (up to 5 calls) until it has a final answer, self-correcting on SQL errors. |
| `scripts/ask_v1.py` | The simplest possible version: one call to write SQL, run it, done. No retries. |

## Experiment: does context help? Does multi-agent help?

`scripts/run_eval.py` runs a hand-written set of questions (`eval/questions.jsonl`) through three configurations and grades each answer with a normalized substring match:

- **`no_context`** — one-shot SQL generation, schema only.
- **`with_context`** — identical, plus the shot-notation glossary.
- **`multi_agent`** — a Planner sketches an approach, a self-correcting SQL agent (`src/agent.py`) executes it, and a Verifier reviews the result and can send it back for one revision.

Latest run (`claude-haiku-4-5` for every call, 6 questions):

| variant | accuracy | avg LLM calls | avg tokens | avg latency |
|---|---|---|---|---|
| `no_context` | 50.0% | 2.0 | 3,659 | 2.9s |
| `with_context` | 50.0% | 2.0 | 7,212 | 2.7s |
| `multi_agent` | 83.3% | 6.7 | 48,612 | 17.0s |

A few things this surfaced:

- **Multi-agent buys back a lot of accuracy from a weaker model, at real cost.** Swapping every call from Sonnet to the smaller/cheaper Haiku model dropped the one-shot variants' accuracy noticeably, but the planner → SQL agent → verifier loop recovered most of it — at roughly 13x the tokens and 6x the latency of the plain baseline. Bigger model vs. more agentic scaffolding is a genuine tradeoff here, not a wash.
- **Haiku doesn't always follow "output only SQL."** On harder notation questions, the smaller model sometimes leaked reasoning prose (`"Wait, let me reconsider..."`) into what was supposed to be a bare SQL string, breaking execution outright — a real instruction-following gap, not a bug in the harness.
- **The data itself has a wrinkle worth knowing about**: `matches` contains at least one genuine duplicate `match_id` (the same match logged twice), so "how many matches are there" is legitimately ambiguous between a raw row count and `COUNT(DISTINCT match_id)`. The multi-agent variant caught this independently; the one-shot variants didn't.

Run it yourself with `python scripts/run_eval.py`; results land in `eval/results.csv` (gitignored, regenerated each run).
