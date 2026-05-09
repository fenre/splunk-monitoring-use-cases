"""ROI, coverage, gap, and prioritisation analyses.

Feasibility verbs answer "what should we work on next?" — they
reason about UC criticality, regulatory coverage, equipment models,
prerequisite chains, and operational waves. Unlike ``audits/``,
their goal is to *guide* future authoring rather than gate
existing changes.

Migration source: ``scripts/feasibility_*.py``,
``scripts/coverage_*.py``, and ``scripts/gap_*.py``.
"""

from __future__ import annotations

__all__: list[str] = []
