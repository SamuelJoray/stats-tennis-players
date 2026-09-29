"""Experiment: does context beyond context/points.md (i.e.
table_relationships.md and variables_infos.md) actually help the single
self-correcting SQL agent (src/agent.py, Milestone B)?

Unlike src/variants/one_shot.py's no_context/with_context split, both configs
here always include points.md -- the variable being tested is whether the
table-relationship and column-glossary notes on top of it change anything,
not whether notation context exists at all.
"""

from src.agent import TennisAgent
from src.variants.base import VariantResult


def _run(question: str, context_files, model: str | None) -> VariantResult:
    kwargs = {"context_files": context_files}
    if model is not None:
        kwargs["model"] = model
    agent = TennisAgent(**kwargs)
    result = agent.ask(question)
    return VariantResult(
        answer=result["answer"],
        sql_log=result["sql_log"],
        num_llm_calls=result["num_llm_calls"],
        total_tokens=result["total_tokens"],
    )


def run_points_only(question: str, model: str | None = None) -> VariantResult:
    return _run(question, context_files=["points.md"], model=model)


def run_full_context(question: str, model: str | None = None) -> VariantResult:
    return _run(question, context_files=None, model=model)
