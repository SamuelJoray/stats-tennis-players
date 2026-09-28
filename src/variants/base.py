"""Shared return contract for every variant, so scripts/run_eval.py can
treat 'no context', 'with context', and 'multi-agent' identically."""

from dataclasses import dataclass, field


@dataclass
class VariantResult:
    answer: str
    sql_log: list = field(default_factory=list)
    num_llm_calls: int = 0
    total_tokens: int = 0
