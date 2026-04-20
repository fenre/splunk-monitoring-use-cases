"""tools.audits — CI-blocking quality gates.

Each module is a standalone CLI that exits non-zero on a policy
violation. The merged ``ci.yml`` workflow runs every module in parallel.

Modules
-------
url_freeze     — Block merges that remove or rename a URL exposed by the
                 latest release's ``dist/manifest.json``.
schema_diff    — Detect breaking changes to JSON Schemas; cross-check
                 the version bump against docs/schema-versioning.md.
schema_meta    — Assert every schema declares the required-metadata set
                 (`$id`, `version`, `x-stability`, `x-since`,
                 `x-changelog`).
budgets        — Enforce per-asset-class size budgets from
                 ``tools/build/budgets.json``.
a11y           — Run axe-core via Playwright on a sample of pages.
spl_lint       — Static SPL validation (port of scripts/audit_*).
cim_compliance — Cross-check CIM data model declarations.
links          — Internal + external link checker.
"""

__all__ = [
    "url_freeze",
    "schema_diff",
    "schema_meta",
    "budgets",
]
