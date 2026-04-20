# ADR-0004: Python stdlib only for build and audits

- **Status:** Accepted
- **Date:** 2023-03-15 (ratified retroactively 2026-04-16)
- **Deciders:** Repository maintainers

## Context

The build pipeline and audit suite are the load-bearing tools of the repository. Every contributor must be able to run them locally. Every CI run must be able to run them reliably. A forker must be able to stand up the same pipeline for a different content domain without inheriting a dependency graph.

The work the build and audits do is:

- Read ~24 markdown files.
- Regex-parse headings and bulleted fields.
- Traverse a small in-memory tree.
- Emit JSON and text files.
- Run HTTP HEAD requests against ~200 external URLs for link validation.

None of this needs Pandas, nor BeautifulSoup, nor Markdown-it, nor PyYAML.

## Decision

**All Python code in this repository uses the Python 3 standard library only, with no third-party packages.**

Specifically:

- [`build.py`](../../build.py) imports only `glob`, `json`, `os`, `re`, `shutil`, `sys`, `datetime`.
- Every script under [`scripts/`](../../scripts/) imports only stdlib modules. URL fetching uses `urllib.request`, not `requests`.
- There is no `requirements.txt`, no `Pipfile`, no `poetry.lock` for the core scripts.
  (Note: `mcp/pyproject.toml` exists for the MCP server package, which has its own dependency set.)

The sole exception is the Node one-liner in the CI workflow that syntax-checks `non-technical-view.js`. Node is a runtime, not a dependency, and is used for nothing else.

## Consequences

**Positive:**

- A fresh clone and `python3 build.py` builds the full site with no install step.
- CI is fast: no `pip install`, no cache invalidation, no version pinning.
- Forks inherit no dependency graph. A replicator for Sentinel/KQL/ASIM can keep the same constraint trivially.
- Supply-chain attack surface through Python dependencies is zero.
- Scripts run on any Python 3.8+ interpreter on any OS, with no virtualenv management.

**Negative:**

- Some convenience is lost. Examples:
  - Hand-rolled markdown parser rather than using `markdown` or `mistune`.
  - Hand-rolled JSON schema validation in `audit_catalog_schema.py` rather than using `jsonschema`.
  - HTTP link checking uses `urllib.request` with manual timeouts rather than `httpx` async.
- Mitigation: the jobs the build does are simple; stdlib is sufficient; performance is acceptable.

## When to break this rule

This ADR is strong but not absolute. Future capability that legitimately requires a dependency (e.g. a proper SPL parser written in `pyparsing`, or `jinja2` for Splunk conf templating) should be isolated in a separate script, documented in the script header, and pinned to a specific version. The build (`build.py`) and the core audits remain stdlib-only.

If v6.0's executable test harness needs a SPL grammar, the grammar lives in `scripts/run_uc_tests.py` and that single script is allowed to depend on `pyparsing`; everything else stays stdlib.

## Alternatives considered

- **Pin a small `requirements.txt` with `markdown`, `pyyaml`, `jsonschema`, `requests`.** Rejected for the reasons above.
- **Rewrite in Go or Rust.** Rejected: contributors skew Python; Python stdlib is enough; toolchain burden would be net negative.
- **Use a markdown compiler like Pandoc.** Rejected: large binary dependency; CI caches would grow.

## Links

- Implementation: [`build.py`](../../build.py)
- Scripts: [`scripts/`](../../scripts/)
- Workflow: `.github/workflows/validate.yml`
- Superseded by: —
