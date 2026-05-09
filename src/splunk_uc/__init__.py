"""``splunk_uc`` — top-level package for the splunk-monitoring-use-cases catalogue.

Repo-overhaul plan §P6 (2026-05-09).

The package is the canonical home for what used to live ad-hoc in
``scripts/``: catalogue audits, content generators, migrations,
ingest pipelines, and feasibility tooling. The build pipeline
(``tools/build/``) and the MCP server (``mcp/``) keep their
separate package trees, but everything that operates *on* the
catalogue source rather than *building* the static site lives here.

Layout
------

::

    src/splunk_uc/
    ├── __init__.py        # this file
    ├── __main__.py        # `python -m splunk_uc <verb>` dispatcher
    ├── _registry.py       # verb -> callable mapping
    ├── audits/            # quality / structure / drift gates
    ├── generators/        # text + structured artefact emitters
    ├── ingest/            # external-data ingestion (regulations, dependencies)
    ├── migrations/        # one-shot data migrations
    └── feasibility/       # ROI / coverage / gap analyses

Migration strategy
------------------

P6 lands incrementally. Each script in ``scripts/`` is migrated by
moving its body to ``src/splunk_uc/<subpackage>/<name>.py`` and
leaving a thin shim at the original ``scripts/<name>.py`` path so
existing CI workflows, Makefile targets, and ad-hoc maintainer
invocations keep working unchanged. The shim ``imports main`` from
the new location and forwards ``sys.argv[1:]``; this both validates
the migration and makes the cutover risk-free.

Until ``pip install -e .`` is run, the dispatcher is invokable via:

    PYTHONPATH=src python3 -m splunk_uc <verb>

The ``audit-reproducibility`` Makefile target uses this form so the
package works without an install step, matching the build pipeline's
"stdlib-only" ergonomics.
"""

from __future__ import annotations

__all__ = ["__version__"]

# Package version is sourced from VERSION at the repo root. Reading it
# at import time keeps a single source of truth and avoids drift with
# CHANGELOG / pyproject. Failures fall back to "0.0.0+unknown" so the
# package can be imported even from a sdist that omits VERSION.
import pathlib

try:
    _VERSION_PATH = pathlib.Path(__file__).resolve().parents[2] / "VERSION"
    __version__ = _VERSION_PATH.read_text(encoding="utf-8").strip()
except (OSError, UnicodeDecodeError):
    __version__ = "0.0.0+unknown"
