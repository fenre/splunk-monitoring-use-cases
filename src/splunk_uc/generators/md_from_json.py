"""splunk_uc.generators.md_from_json — retired 2026-05-18 (F21 close).

History
-------

Until 2026-05-18 this module wrote per-UC ``content/cat-NN-<slug>/UC-X.Y.Z.md``
companion files from the canonical ``UC-X.Y.Z.json`` sidecars in the same
directory. The companions were generated artefacts (``--check`` enforced by
``make sync-generated-check``); they were never consumed by the build pipeline
itself — ``tools/build/parse_content.py`` reads the JSON sidecars exclusively.

F21 in the repository-health plan asked for the companions to be removed from
git so the repo doesn't carry 7,929 generated artefacts under SSOT directories.
This module is retained as a no-op stub purely so:

* The coverage baseline entry at
  ``data/baselines/coverage-v9.1.0.json#tier_2_modules`` stays valid (the file
  still exists; the baseline pin test in
  ``tests/scripts/test_audit_coverage_budget.py`` keeps passing).
* Any out-of-tree caller that ``import splunk_uc.generators.md_from_json``
  does not crash with ``ModuleNotFoundError``.

What replaces the deleted companions
------------------------------------

The per-UC, LLM-friendly markdown twin is emitted at build time by
``tools/build/templates/uc.py::render_markdown_twin`` into
``dist/uc/UC-X.Y.Z/uc.md`` for the public site, stamped with
``Last-modified`` and ``Catalogue-version``. That is the contract advertised
in ``AGENTS.md`` and on every UC HTML page via the
``<link rel="alternate" type="text/markdown">`` tag.

See also
--------

* ``docs/health-check-2026-progress.md`` — F21 row (DONE 2026-05-18)
* ``docs/adr/0007-json-as-source-of-truth.md`` — generated-artefact contract
* ``docs/adr/0009-generated-artefact-policy.md`` — when a generated artefact
  should live in-tree vs. dist-only
"""

from __future__ import annotations


_RETIRED_MSG = (
    "splunk_uc.generators.md_from_json was retired on 2026-05-18 as part of "
    "the F21 close (deletion of the 7,929 content/cat-*/UC-*.md companions). "
    "The per-UC markdown twin is now emitted at build time only by "
    "tools/build/templates/uc.py::render_markdown_twin into "
    "dist/uc/UC-X.Y.Z/uc.md. See docs/health-check-2026-progress.md F21."
)


def main(argv: list[str] | None = None) -> int:
    """Stub entry point — prints the retirement notice and exits non-zero."""
    import sys

    print(_RETIRED_MSG, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
