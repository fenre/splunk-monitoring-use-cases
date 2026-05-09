"""Content + artefact generators: scripts that write files.

Generators emit human- and machine-readable artefacts derived from
the SSOT (e.g. plain-language explanations, MITRE coverage reports,
visual maps, OpenAPI clients). Unlike ``audits/`` they DO write
under ``content/``, ``dist/``, ``docs/``, or ``reports/``, so each
verb takes care to be idempotent: running it twice in a row should
either be a byte-identical no-op or surface a clearly-explained diff.

Migration source: ``scripts/generate_*.py`` and select ``scripts/build_*.py``.
"""

from __future__ import annotations

__all__: list[str] = []
