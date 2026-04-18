# Splunk UC MCP server — operator & developer guide

> **TL;DR** — Install [`splunk-uc-mcp`](../mcp/) locally (`pip install -e mcp/`)
> and point your MCP-aware editor (Cursor, Claude Desktop, Claude Code,
> MCP Inspector) at it. The server exposes the 6 424 use cases, 60
> regulations, 105 equipment slugs, and the signed provenance ledger
> published by this repository as Model Context Protocol tools and
> resources. Read-only, stdio-only, no authentication surface, and no
> catalogue mutation. Two personas are served equally well:
>
> - **Compliance officer / auditor** — "show me the uncovered GDPR
>   clauses my Azure footprint is about to bail out", and
> - **Detection engineer** — "give me every UC that lights up on
>   `cisco_ise` authentication telemetry, with the SPL and known
>   false positives".

This document covers:

- [What the server ships](#what-the-server-ships)
- [Architecture](#architecture)
- [Install and client setup](#install-and-client-setup)
- [Tool reference](#tool-reference)
- [Resource reference](#resource-reference)
- [Persona transcripts](#persona-transcripts)
- [Security model](#security-model)
- [Developer guide](#developer-guide)
- [Troubleshooting](#troubleshooting)

---

## What the server ships

`splunk-uc-mcp` is a pure-Python 3.11+ package that speaks JSON-RPC
[Model Context Protocol](https://modelcontextprotocol.io/) over stdio.
It runs inside the local shell started by the MCP-aware editor and
talks to the catalogue via pre-built static JSON under
`/api/v1/` — either from a local clone or, as a fallback, from the
project's GitHub Pages mirror.

| Surface | Count | Source |
| --- | --- | --- |
| Tools | 8 | Declared in [`mcp/src/splunk_uc_mcp/server.py`](../mcp/src/splunk_uc_mcp/server.py) |
| URI families | 4 (`uc://`, `reg://`, `equipment://`, `ledger://`) | Declared in [`mcp/src/splunk_uc_mcp/resources/uri_scheme.py`](../mcp/src/splunk_uc_mcp/resources/uri_scheme.py) |
| Use cases exposed | 6 424 | `api/v1/recommender/uc-thin.json` + per-UC endpoints |
| Regulations | 60 | `api/v1/compliance/regulations/index.json` |
| Equipment slugs | 105 | `api/v1/equipment/index.json` |
| Compliance gap report | 1 | `api/v1/compliance/gaps.json` |
| Signed provenance ledger | 1 889 entries | `data/provenance/mapping-ledger.json` (local only) |

Every operation is **read-only**. The server never writes to disk and
never issues shell commands. There is no authentication layer because
the stdio transport makes the agent the sole trust boundary.

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│ MCP client (Cursor / Claude Desktop / Claude Code / MCP Inspector)   │
│                                                                      │
│   ─ starts splunk-uc-mcp via `command` + `args`                      │
│   ─ speaks JSON-RPC over stdin/stdout                                │
│   ─ renders tool-call results + resource reads as LLM context        │
└───────────────────────────▲──────────────────────────────────────────┘
                            │ JSON-RPC (stdio)
┌───────────────────────────┴──────────────────────────────────────────┐
│ splunk-uc-mcp (python package, this repo)                            │
│                                                                      │
│   ┌────────────┐  ┌──────────────────────┐  ┌──────────────────────┐ │
│   │ server.py  │─▶│ tools/*.py (8 tools) │─▶│ catalog.py           │ │
│   │ stdio loop │  │ resources/uri_scheme │  │ (local + HTTPS)      │ │
│   └────────────┘  └──────────────────────┘  └──────────┬───────────┘ │
└─────────────────────────────────────────────────────────┼────────────┘
                 ┌───────────────────────────────────────┘
                 │ 1st: local clone (fast)
┌────────────────▼──────────────────────────────────────────────────────┐
│ Local checkout of splunk-monitoring-use-cases                         │
│   /api/v1/**.json      (deterministic catalogue, 11 MB)               │
│   /data/provenance/**  (signed mapping ledger)                        │
└───────────────────────────────────────────────────────────────────────┘
                 │ 2nd fallback (when no local clone)
┌────────────────▼──────────────────────────────────────────────────────┐
│ GitHub Pages mirror                                                   │
│   https://fenre.github.io/splunk-monitoring-use-cases/api/v1/*.json   │
│   (HTTPS only; base URL is regex-validated to block SSRF)             │
└───────────────────────────────────────────────────────────────────────┘
```

Key design choices:

- **Local-first**. When the server detects an `api/v1/manifest.json`
  under `--catalog-root` (or the repo containing the installed
  package) it reads everything from disk — zero latency, works
  offline, usable in air-gapped environments.
- **HTTPS fallback**. When no local clone is available the server
  falls back to an HTTPS GET against the GitHub Pages mirror. The
  base URL is locked to an allow-list regex, path traversal is
  explicitly rejected, and every response is capped at 10 MB.
- **Static JSON data plane**. Every catalogue artefact is pre-built by
  `scripts/generate_api_surface.py` and shipped with the repository.
  The MCP server never computes anything expensive — it slices
  pre-cached static JSON.
- **Drift-guarded**. `scripts/audit_mcp_tool_schemas.py` exercises
  every tool against the live `api/v1` tree at CI time and validates
  the result against the tool's declared outputSchema. A field rename
  on either side of the pipe fails the pull request.

## Install and client setup

### Prerequisites

- Python 3.11+ (the MCP SDK requires it).
- A local clone of this repository (recommended) or network access
  to the GitHub Pages mirror.

### Installation

The package lives under [`mcp/`](../mcp/) in this repo. It is not yet
on PyPI — install it from source:

```bash
git clone https://github.com/fenre/splunk-monitoring-use-cases.git
cd splunk-monitoring-use-cases
pip install -e mcp/
```

This installs a `splunk-uc-mcp` console script on `$PATH`.

### Verify the install

```bash
splunk-uc-mcp --version
# splunk-uc-mcp <package-version>
```

A quick manual smoke test:

```bash
splunk-uc-mcp --verbose 2>server.log &
# point MCP Inspector at the PID → list tools → call search_use_cases
```

### Cursor

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "splunk-uc": {
      "command": "splunk-uc-mcp",
      "args": ["--catalog-root", "/absolute/path/to/splunk-monitoring-use-cases"]
    }
  }
}
```

Reload Cursor (`Command → Developer: Reload Window`). The
`splunk-uc` tool list will appear in the MCP tools pane.

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`
(macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "splunk-uc": {
      "command": "splunk-uc-mcp",
      "args": ["--catalog-root", "/absolute/path/to/splunk-monitoring-use-cases"]
    }
  }
}
```

Restart the desktop app.

### Claude Code (CLI)

```bash
claude mcp add splunk-uc \
  --command splunk-uc-mcp \
  --arg --catalog-root \
  --arg /absolute/path/to/splunk-monitoring-use-cases
```

Verify:

```bash
claude mcp list
# splunk-uc (stdio) — running
```

### MCP Inspector (developer tool)

```bash
npx @modelcontextprotocol/inspector splunk-uc-mcp \
  --catalog-root /absolute/path/to/splunk-monitoring-use-cases
```

The Inspector exposes a web UI for tool calls, resource reads, and
JSON-RPC frame inspection — invaluable when debugging drift.

### Running without a local clone

```bash
splunk-uc-mcp --base-url https://fenre.github.io/splunk-monitoring-use-cases
```

The signed provenance ledger is **not** served by the mirror — it
lives inside the repo so the Sigstore signature travels with git
history. `ledger://` resource reads return `not_found` in
mirror-only mode.

## Tool reference

Every tool returns structured JSON. Errors are returned as
`isError=True` `CallToolResult`s with the payload
`{"error": "<kind>", "message": "<human readable>"}`. Error kinds are
`invalid_input`, `not_found`, and `catalog_error`.

### `search_use_cases`

Search the catalogue by keyword and/or filters. Returns a compact row
per match suitable for follow-up `get_use_case` calls.

```json
{
  "query": "Azure sign-in",            // optional free text
  "category": "22.1",                  // optional primary or "cat.sub"
  "regulation_id": "gdpr",             // optional slug
  "equipment": "azure",                // optional slug
  "mitre_technique": "T1110.003",      // optional T####[.###]
  "limit": 10                          // 1-50, default 10
}
```

Response shape:

```json
{
  "count": 10,
  "totalMatched": 45,
  "useCases": [
    {
      "id": "22.1.8",
      "title": "...",
      "equipment": ["azure"],
      "regulationIds": ["gdpr@2016-679", "hipaa@2013-final"],
      "mitreAttack": ["T1110.003"]
    }
  ]
}
```

### `get_use_case`

Return the full detail for one UC — SPL, implementation notes, known
false positives, references, and the full `compliance[]` array (with
clause, mode, assurance, and rationale for each regulatory citation).

```json
{"uc_id": "22.1.1"}
```

### `list_categories`

Return the 23 primary categories with per-subcategory UC counts.
Useful as a discovery step before `search_use_cases`.

```json
{}
```

### `list_regulations`

List the 60 regulations with jurisdiction, tier, and tag metadata.

```json
{
  "tier": 1,              // optional 1-3
  "jurisdiction": "EU",   // optional 1-16 chars
  "tag": "privacy"        // optional 1-48 chars
}
```

### `get_regulation`

Regulation detail (optionally version-specific). Pass
`version="2016-679"` (GDPR) or `version="2016-679/2024-amend"` for
the full per-version document.

```json
{"regulation_id": "gdpr", "version": "2016-679"}
```

### `list_equipment`

The 105 equipment slugs with UC and regulation counts. Accepts a
`regulation_id` filter to narrow to a specific framework (e.g.
"show me every equipment slug that has at least one GDPR UC").

```json
{
  "regulation_id": "gdpr",          // optional slug
  "min_use_case_count": 5           // default 0
}
```

### `get_equipment`

Per-equipment view: UCs grouped by category, regulations grouped by
framework, and the list of model compounds (e.g. `hardware_bmc_edac`).

```json
{"equipment_id": "azure"}
```

### `find_compliance_gap`

Return the pre-computed gap analysis for one or more regulations:
which common clauses still have zero UC coverage, filtered through
the project's tier-based priority model. Accepts an optional
`equipment_id` to overlay which uncovered clauses the target
deployment already catches via UCs bearing that equipment tag.

```json
{
  "regulations": ["gdpr", "hipaa"],   // 1-20 slugs
  "equipment_id": "azure"             // optional overlay
}
```

## Resource reference

URI-addressable views over the same data. These are ideal for MCP
clients that prefer a "fetch the document" model over a "call a
function" model (for example, Claude Code's file-picker UX).

| URI pattern | Example | Tool equivalent |
| --- | --- | --- |
| `uc://usecase/{uc_id}` | `uc://usecase/22.1.1` | `get_use_case` |
| `uc://category/{cat_id}` | `uc://category/22` | filtered `list_categories` |
| `reg://{regulation_id}` | `reg://gdpr` | `get_regulation` |
| `reg://{regulation_id}@{version}` | `reg://gdpr@2016-679` | `get_regulation` (versioned) |
| `equipment://{equipment_id}` | `equipment://azure` | `get_equipment` |
| `ledger://` | `ledger://` | *(no tool equivalent)* |

`list_resources` deliberately returns an empty set — the catalogue is
too large to enumerate. Clients should use the `list_*` tools to
discover IDs and then read the URI. Resource reads return compact JSON
text with the same error envelope as tool calls (`{"error": "<kind>",
"message": "..."}`).

## Persona transcripts

Both transcripts assume an agent configured with the stdio server
above. Natural-language turns are abbreviated; tool calls are shown
in JSON-RPC shorthand.

### Persona A — Compliance officer / auditor

> "We're preparing the GDPR audit for our Azure-heavy business unit.
> Which Art.32 clauses still have no UC coverage, and does any of the
> gap go away if the Azure detections already in place count?"

1. **Scope the problem**

    ```text
    tool: find_compliance_gap
    args: {"regulations": ["gdpr"], "equipment_id": "azure"}
    ```

    The response contains the per-regulation gap object, plus an
    `equipmentOverlay` section listing which uncovered clauses are
    already hit by UCs bearing `equipment:"azure"`. The agent reports
    "23 uncovered Art.5 / Art.32 clauses, 6 of which Azure already
    catches."

2. **Drill into a specific clause**

    ```text
    resource: reg://gdpr@2016-679
    ```

    The agent cross-references Art.32(1)(b) ("ability to ensure
    ongoing confidentiality, integrity, availability…") and picks
    the two UCs already tagged to it from the `mapsToUcIds` array.

3. **Show the SPL that covers one of those UCs**

    ```text
    tool: get_use_case
    args: {"uc_id": "22.1.8"}
    ```

    Returns title, description, full SPL, `implementationNotes`, and
    every `compliance[]` entry. The officer has a single URL to share
    with the business unit: the GDPR article, the Splunk saved search,
    and the provenance entry (via `ledger://`).

### Persona B — Detection engineer

> "I just onboarded a Cisco ISE estate. Give me every use case that
> lights up on ISE authentication telemetry, ranked by criticality,
> and surface known false-positive footguns for each."

1. **Find the equipment slug**

    ```text
    tool: list_equipment
    args: {"regulation_id": null, "min_use_case_count": 1}
    ```

    Engineer skims the list and picks `cisco_ise`.

2. **Pull the per-equipment view**

    ```text
    resource: equipment://cisco_ise
    ```

    Response: `useCasesByCategory` groups the 34 relevant UCs into
    Authentication (18), Network (7), Compliance (9). Engineer picks
    the Authentication slice.

3. **Search by keyword within the slice**

    ```text
    tool: search_use_cases
    args: {"query": "brute force", "equipment": "cisco_ise", "limit": 10}
    ```

4. **Pull full detail for each match**

    ```text
    tool: get_use_case
    args: {"uc_id": "1.1.65"}
    ```

    Engineer reviews SPL, fires it in a test search head, copies the
    `knownFalsePositives` list into the saved search comment, commits
    to the ops repo. Repeat for the remaining 9 candidates.

5. **Sanity-check MITRE coverage**

    ```text
    tool: search_use_cases
    args: {"mitre_technique": "T1110.003", "equipment": "cisco_ise"}
    ```

Both personas never leave the IDE and never run arbitrary shell
commands — every piece of context the LLM needs comes from the MCP
server's static JSON reads.

## Security model

Aligned with the [CoSAI MCP security guidance](https://www.coalitionforsecureai.org/wp-content/uploads/2025/10/CoSAI_MCP_Security_AISC1.pdf) (the same guidance encoded into the workspace-level
`codeguard-0-mcp-security` rule that ships with this project's Cursor
configuration):

| Control | Implementation |
| --- | --- |
| Read-only | No MCP tool writes to disk; no shell execution path exists. |
| Input validation | Every slug, UC ID, version, category, MITRE technique, and URL is regex-validated before use. |
| Bounded payloads | 10 MB hard cap (`MAX_PAYLOAD_BYTES`) on both local file reads and streamed HTTPS responses. |
| Path traversal | Local paths are validated segment-by-segment; `/.`, `/..`, and absolute paths are rejected. |
| SSRF protection | HTTPS base URL is pinned to a regex allow-list; redirects are not followed transparently. |
| Stdio only | No HTTP listener, no bind to `0.0.0.0`. DNS-rebinding attacks do not apply. |
| No secret handling | The catalogue is fully public; the server never reads env vars, tokens, or credentials. |
| Log hygiene | Tool-call arguments are SHA-256 hashed (first 12 bytes) before logging, so sensitive inputs never land on disk. |
| Sandboxing advice | Run the server under the editor's default tool sandbox; the package is pure-Python with no native deps. |
| Supply chain | `mcp/pyproject.toml` pins compatible ranges; test dependencies (`pytest`, `respx`) are separated so production installs stay minimal. |

CoSAI's "Do not rely on the LLM for validation" rule is observed —
every tool validates its own arguments server-side and rejects
malformed input with a structured `invalid_input` error, even if the
client elects to skip client-side JSON Schema validation.

## Developer guide

### Local development

```bash
cd mcp/
pip install -e '.[test]'
pytest -q               # 291 tests, <2s cold cache
```

### Key files

| Path | Role |
| --- | --- |
| [`src/splunk_uc_mcp/server.py`](../mcp/src/splunk_uc_mcp/server.py) | Tool + resource registration, JSON-RPC lifecycle. |
| [`src/splunk_uc_mcp/catalog.py`](../mcp/src/splunk_uc_mcp/catalog.py) | Local-first + HTTPS fallback data loader with SSRF + payload controls. |
| [`src/splunk_uc_mcp/tools/*.py`](../mcp/src/splunk_uc_mcp/tools/) | One module per tool (schema + handler). |
| [`src/splunk_uc_mcp/resources/uri_scheme.py`](../mcp/src/splunk_uc_mcp/resources/uri_scheme.py) | Custom URI parser for the 4 URI families. |
| [`tests/`](../mcp/tests/) | Pytest suite: unit tests for every tool/resource + an in-memory JSON-RPC server test. |
| [`scripts/audit_mcp_tool_schemas.py`](../scripts/audit_mcp_tool_schemas.py) | CI drift guard — exercises every tool against the live `api/v1` tree and validates outputs. |
| [`.github/workflows/validate.yml`](../.github/workflows/validate.yml) | Installs the package, runs tests, and runs the drift guard on every PR. |

### Adding a new tool

1. Create `src/splunk_uc_mcp/tools/<name>.py` with `<NAME>_SCHEMA`,
   `<NAME>_OUTPUT_SCHEMA`, and a sync handler.
2. Re-export from `tools/__init__.py`.
3. Register in `server.py`'s `_tool_definitions()` and `_tool_dispatch()`.
4. Write unit tests + a synthetic-catalog fixture case.
5. Add the tool to `scripts/audit_mcp_tool_schemas.py`'s `_PROBE_ARGS`.

The drift guard will catch you if the output schema and the real
`api/v1` shape disagree — fix one or the other and push.

### Releasing

The package version is `mcp/pyproject.toml` `[project].version`. The
CI drift guard + unit tests must be green before publishing. PyPI
release is TODO (Phase 7).

## Troubleshooting

### "Tools list is empty in my editor"

The editor could not start the server. Check the MCP client log:

- **Cursor** — `~/.cursor/logs/<date>/exthost.log`
- **Claude Desktop** — `~/Library/Logs/Claude/mcp-server-splunk-uc.log`
- **Claude Code** — `claude mcp logs splunk-uc`

Common causes:

- `splunk-uc-mcp` is not on `$PATH` — re-run `pip install -e mcp/`
  inside the same Python the editor uses.
- `--catalog-root` points at the wrong directory (must contain
  `api/v1/manifest.json`). Absolute paths only.
- The editor needs a reload after config changes.

### "CatalogValidationError: --catalog-root … does not contain api/v1/manifest.json"

Run `python3 scripts/generate_api_surface.py` from the repo root
to materialise the `api/v1/` tree. It is gitignored by default
because the committed tree can drift.

### "Output validation error: structuredContent does not match schema"

The drift guard should have caught this in CI. If you're seeing it
locally:

```bash
python3 scripts/audit_mcp_tool_schemas.py --verbose
```

It reports the exact tool and the JSON pointer of the mismatch. Fix
either the tool's `OUTPUT_SCHEMA` or the underlying API generator.

### "Remote fallback fails with 403 / 404"

The GitHub Pages mirror is rate-limited. Prefer a local clone; if
impossible, cache the catalogue in a private mirror and pass
`--base-url https://your.mirror/path`. The base URL regex accepts
`https://` hosts with alphanumeric subdomain components.

### "ledger:// returns not_found"

The signed provenance ledger lives in the repo, not the GitHub Pages
mirror. Use `--catalog-root` pointed at a local clone.

---

Questions or patches welcome. Start with
[`mcp/README.md`](../mcp/README.md) for the quick-start, dive into
[`src/splunk_uc_mcp/server.py`](../mcp/src/splunk_uc_mcp/server.py)
for the wiring, and read
[`tests/test_server.py`](../mcp/tests/test_server.py) for the
in-memory JSON-RPC integration pattern.
