# Tennis Stats Q&A Agent

Ask questions about professional tennis matches in plain English and get answers backed by real SQL. A Streamlit chat app sends your question to Claude, which writes and runs SQL against a local DuckDB database, then explains the result.

The project also includes three small experiments comparing: no context vs. domain context vs. a planner/SQL-agent/verifier pipeline; a minimal glossary vs. the full set of context notes; and a single self-correcting agent vs. that same multi-agent pipeline. All results below use `claude-haiku-4-5`.

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
| `src/agent.py` | The agent used by the Streamlit app: gives Claude a `run_sql` tool and lets it iterate (up to 8 calls) until it has a final answer, self-correcting on SQL errors. The system prompt (schema + context) is marked cacheable, so repeated calls within a question — and across questions in an eval run — reuse it at ~10% of the normal input cost instead of resending it at full price every time. |
| `scripts/ask_v1.py` | The simplest possible version: one call to write SQL, run it, done. No retries. |
| `src/variants/one_shot.py`, `src/variants/multi_agent.py`, `src/variants/agent_context_experiment.py` | The comparable "variant" implementations used by the eval scripts below — one-shot SQL generation, the planner/SQL-agent/verifier pipeline, and the points-only-vs-full-context single agent, respectively. Each returns a common `VariantResult` (answer, SQL log, call count, token count). |
| `src/eval_harness.py` | Shared logic for all three eval scripts: loads `eval/questions.jsonl`, runs a set of named variants over it, grades each answer, writes a results CSV, prints a summary table. Grading uses a 2%-relative-tolerance numeric comparison (extracts every number from the free-form answer, checks if any is close enough to the expected value) rather than an exact substring match — see "What we learned" below for why. |

## Experiments

`eval/questions.jsonl` is a hand-written, hand-verified set of 13 questions (every `expected_answer` was checked against a real SQL query before being written down — see each question's `notes`). Three scripts run different configurations over it through the shared harness in `src/eval_harness.py`, which grades an answer correct if it contains a number within 2% of the expected value, not an exact substring match — see "What we learned" below for why that distinction matters.

### 1. `scripts/run_eval.py` — does context help? Does multi-agent help?

- **`no_context`** — one-shot SQL generation, schema only, no self-correction.
- **`with_context`** — identical, plus the shot-notation glossary.
- **`multi_agent`** — a Planner sketches an approach, a self-correcting SQL agent (`src/agent.py`) executes it, and a Verifier reviews the result and can send it back for one revision.

| variant | accuracy | avg LLM calls | avg tokens | avg latency |
|---|---|---|---|---|
| `no_context` | 53.8% | 2.0 | 3,749 | 3.1s |
| `with_context` | 69.2% | 2.0 | 324 | 2.5s |
| `multi_agent` | 76.9% | 7.8 | 11,563 | 22.2s |

Context alone buys a real ~15-point accuracy jump over nothing at all, and the multi-agent pipeline adds a further but smaller gain on top, at much higher latency. Take `with_context`'s 324-token average with a grain of salt, though — see the caching caveat below.

### 2. `scripts/run_context_experiment.py` — how much of that context actually matters?

Both configs use the same self-correcting single agent (`src/agent.py`) and always include `context/points.md` (the shot-notation glossary); the only difference is whether `context/table_relationships.md` and `context/variables_infos.md` (table-join rules, column definitions, documented data-quality traps) are also included.

| variant | accuracy | avg LLM calls | avg tokens | avg latency |
|---|---|---|---|---|
| `agent_points_only` | 69.2% | 4.3 | 5,417 | 8.2s |
| `agent_full_context` | 84.6% | 3.0 | 2,556 | 5.9s |

The extra context doesn't just improve accuracy — it makes the agent **cheaper and faster too**, needing fewer exploratory queries because it isn't discovering the schema's quirks (nested categories, NULL-vs-empty-string, duplicate keys) through trial and error on every question.

### 3. `scripts/run_architecture_experiment.py` — single agent vs. multi-agent, holding context fixed

Both configs get the full context; the only difference is architecture.

| variant | accuracy | avg LLM calls | avg tokens | avg latency |
|---|---|---|---|---|
| `single_agent_full_context` | 92.3% | 3.2 | 2,970 | 5.7s |
| `multi_agent_full_context` | 69.2% | 7.3 | 9,628 | 20.3s |

This is a **reversal** of what we found earlier in this project (before the context and tool-budget fixes below), when multi-agent had the clear edge. Once the single agent's context and tool-call budget were good enough to solve most questions on its own, the planner/verifier wrapper stopped paying for itself — two concrete failure modes explain the drop: the SQL-writing sub-agent inside `multi_agent` shares the same fixed tool-call budget as the standalone agent, but has to process the Planner's prepended plan before it can even start exploring, and gave up mid-solve on two questions the single agent solved cleanly; separately, on one question it wrote `"1st" LIKE '6%*'` intending to match aces, not realizing the `%` wildcard also matches full multi-shot rallies that happen to end in a winner — overcounting by more than 2x. More orchestration isn't free, and its payoff depends entirely on how good the thing being orchestrated already is.

### What we learned building this

- **Documentation fixes that state general facts about the data generalize; fixes tuned to a specific wrong answer don't.** Rewriting `table_relationships.md` to explicitly say "`stats_returndepth`'s `row` column has two overlapping breakdowns, use only `row = 'Total'`" fixed the exact bug it targeted on the first try — and as a side effect, the agent's own verification step surfaced a *second*, previously unknown bug (duplicate rows in that same table) we then documented too. That's the good kind of fix. We deliberately avoided the bad kind: after diagnosing a regex bug purely by iterating until a specific question's number matched, we recognized that "fixing" it that way would just be teaching to the test, and removed the two questions that had already been used to directly motivate a context patch (`q8`, `q9`) rather than re-test them and call it progress.
- **Raising the tool-call budget (`MAX_TOOL_CALLS`, 5 → 8) directly fixed real failures.** Several questions weren't reasoning failures at all — the agent was still making progress when it hit the call limit and had to give up. This is a different lever from context or architecture, and it's nearly free to tune.
- **Prompt caching cuts cost, but it also changes what your existing metrics mean.** Once the system prompt is cached, `input_tokens` becomes "uncached remainder only" — so a naive `input_tokens + output_tokens` sum (what this project's `total_tokens` metric uses) quietly *understates* real prompt size for any variant that benefits from caching, which is exactly why `with_context`'s 324-token average above looks so small. The cost savings are real; the token-count comparison across cached vs. uncached variants isn't apples-to-apples anymore.
- **Exact-substring grading punished technically-defensible answers.** An agent that computed `COUNT(DISTINCT match_id)` instead of `COUNT(*)` on data with a few duplicate keys isn't wrong, it made a different reasonable call — but a strict substring match failed it anyway. Switching to a 2%-relative-tolerance numeric comparison changed several "misses" into correct answers across every experiment above without letting genuinely wrong answers (like the `q6` overcounting bug) slip through.

Run any script yourself, e.g. `python scripts/run_eval.py`; results land in `eval/results*.csv` (gitignored, regenerated each run).
