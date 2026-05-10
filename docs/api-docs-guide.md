# API Docs Page — User Guide

The [API Docs page](../api-docs.html) is the human-readable, in-browser
explorer for the catalogue's read-only JSON API. It renders the
[`openapi.yaml`](../openapi.yaml) specification with **Swagger UI**, so
you get clickable endpoint cards, request/response schemas, example
payloads, and inline `Try it out`.

Audience: integrators wiring the catalogue into their RAG pipeline,
SOAR playbook, ITSI module, dashboard, or any other downstream system
that consumes JSON.

For the policy that governs the API contract see
[API Versioning](api-versioning.md). For prompt-engineering recipes
that consume the API see [`AGENTS-EXAMPLES.md`](../AGENTS-EXAMPLES.md).
For the underlying field abbreviations in `catalog.json` see
[Catalog Schema](catalog-schema.md).

## Quick start

1. Open [`api-docs.html`](../api-docs.html).
2. Browse the endpoint groups in the left navigation (Catalog,
   Compliance, MITRE, OSCAL, Equipment, Recommender, Evidence packs,
   Discovery).
3. Click any endpoint to expand its detail.
4. Click **Try it out → Execute** to send a live request from your
   browser. The response renders inline.

The page is fully static — `openapi.yaml` is the only file the page
fetches besides Swagger UI's own assets.

## What the API offers

Every endpoint lives under `/api/v1/`. Five endpoint families:

### Discovery

- `manifest.json` — top-level pointers to every other endpoint.
- `context.jsonld` — JSON-LD context for the catalogue's vocabulary.
- `openapi.yaml` — the spec the API Docs page itself renders.
- `README.md` — same content as `docs/api-versioning.md`'s public side.

### Catalog (the core)

- `catalog.json` — the full machine-readable catalogue with
  abbreviated keys; see [Catalog Schema](catalog-schema.md).
- `category/<id>/index.json` — per-category drill.
- `uc/UC-X.Y.Z/index.json` — per-UC twin (also has `uc.md` plain-markdown
  twin and `index.html` human page).

### Compliance

- `compliance/index.json` — index of every regulation we map.
- `compliance/coverage.json` — coverage statistics.
- `compliance/gaps.json` — uncovered clauses with priority weights.
- `compliance/regulations/<id>.json` — per-regulation detail.
- `compliance/regulations/<id>@<version>.json` — per-regulation, per-version detail.
- `compliance/clauses/index.json` — every clause with its mapped UCs (consumed by the [Clause Navigator](clause-navigator-guide.md)).
- `compliance/story/<id>.json` — narrative story (consumed by the [Compliance Story](compliance-story-guide.md)).
- `compliance/ucs/<id>.json` — per-UC compliance roll-up.

### OSCAL

- `oscal/index.json` — OSCAL discovery.
- `oscal/catalogs/<id>.json` — OSCAL Catalog model per regulation.
- `oscal/component-definitions/<uc>.json` — OSCAL Component Definition per UC.

### MITRE / D3FEND

- `mitre/index.json` — MITRE coverage entry point.
- `mitre/techniques.json` — every technique with mapped UCs.
- `mitre/coverage.json` — tactic × technique coverage matrix.
- `mitre/d3fend.json` — D3FEND defensive-technique mappings.

### Recommender

- `recommender/sourcetype-index.json` — sourcetype → UC reverse index.
- `recommender/cim-index.json` — CIM model → UC reverse index.
- `recommender/app-index.json` — app/TA → UC reverse index.
- `recommender/uc-thin.json` — minimal UC records used for in-Splunk recommender matching.
- `recommender/splunkbase-index.json` — Splunkbase id → UC reverse index.

### Equipment

- `equipment/index.json` — every equipment slug.
- `equipment/<id>.json` — per-equipment UC list.

### Evidence packs

- `evidence-packs/<regulation>.json` — JSON twin of each
  [evidence pack](evidence-packs/) markdown.

## Working with Swagger UI

### The endpoint card

Each card has:

- HTTP method + path.
- Summary and description.
- A **Parameters** table for path/query parameters.
- A **Responses** section with the JSON schema for each status code.
- A **Try it out** button.

### Try it out

Click **Try it out** on any endpoint, fill in the parameters (path
parameters are required, query parameters usually optional), then
**Execute**. Swagger UI fires an actual HTTP request from your browser
and shows:

- The constructed cURL command (great for copy-paste).
- The response body (JSON, formatted).
- The response status code and headers.

Because the API is fully read-only and CORS-permitted from the
GitHub Pages origin, this works without authentication.

### Schemas tab

The right sidebar of every response card shows the JSON schema for the
payload, generated from the OpenAPI spec. Use this to:

- Understand the shape before writing parsing code.
- Generate types for TypeScript, Pydantic, Go structs, etc., via
  `openapi-generator-cli` or similar.
- Validate fixtures.

## Stability commitments

`/api/v1/` is **frozen** at v7.0.0. The following are guaranteed for
the lifetime of v1:

- Stable URL paths.
- Stable response shape (additive changes only — new fields are
  permitted, removals or type changes are not).
- Stable abbreviation keys (see [Catalog Schema](catalog-schema.md)).

Read [API Versioning](api-versioning.md) for the full policy.

## Performance notes

- `catalog.json` is large (~5 MB compressed). For RAG pipelines or
  bulk processing, fetch it **once** and cache.
- Per-UC twins are tiny (~2 KB) and ideal for "fetch what you need"
  patterns.
- The build emits `integrity.json` with SHA-256 of every artefact; use
  it to skip re-fetching unchanged files.
- The MCP server (see [MCP Server](mcp-server.md)) provides a
  query-driven interface that's often more efficient than scanning
  raw JSON.

## Where to fetch from

- **Live (recommended)**: `https://fenre.github.io/splunk-monitoring-use-cases/api/v1/…`
- **Local clone**: build the catalogue (`make build`) and read from
  `dist/api/v1/…`.
- **MCP server** (recommended for AI agents): see
  [`mcp/README.md`](../mcp/README.md) and [MCP Server](mcp-server.md).

## Where to go next

- [API Versioning](api-versioning.md) — formal contract.
- [Catalog Schema](catalog-schema.md) — what every key means.
- [Build Artefacts Reference](build-artefacts-reference.md) — every
  output of `make build`.
- [`AGENTS-EXAMPLES.md`](../AGENTS-EXAMPLES.md) — copy-paste recipes
  for AI agents consuming the API.
- [MCP Server](mcp-server.md) — typed query interface for AI agents.
- [Recommender App](recommender-app.md) — the Splunk app that consumes
  the recommender endpoints.
