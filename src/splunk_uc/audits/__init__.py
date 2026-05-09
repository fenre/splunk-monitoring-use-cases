"""Catalogue audits: structural, cross-reference, drift, and reproducibility gates.

Audits answer the question "is the catalogue self-consistent and
reproducible right now?" — they read from ``content/``, ``dist/``,
``data/``, ``schemas/``, and ``docs/`` but never modify the source
of truth. Every audit module exposes a ``main(argv) -> int`` callable
so it composes cleanly into both ``python -m splunk_uc <verb>`` and
direct ``python scripts/<shim>.py`` invocations.

Migration source: ``scripts/audit_*.py``.
"""

from __future__ import annotations

__all__: list[str] = []
