# splunk-uc-mcp

[Model Context Protocol](https://modelcontextprotocol.io/) server for
the [Splunk Monitoring Use Cases catalogue](https://fenre.github.io/splunk-monitoring-use-cases/).
Read-only access to:

- **6 424 use cases** across 23 categories (operational, security, compliance, …)
- **60 regulations** (GDPR, HIPAA, PCI DSS, DORA, CMMC, NIS2, EU AI Act, …)
- **105 equipment slugs** (Splunk add-ons and TAs, e.g. `cisco_asa`, `azure`, `kubernetes`)
- **Signed provenance ledger** (1 889 regulatory-to-UC mapping decisions)
- **Compliance gap analysis** (pre-computed uncovered clauses per regulation)

Designed for both **compliance officer / auditor** and **detection engineer**
personas. Every operation reads pre-built `api/v1/*.json` endpoints; the
server never mutates catalogue data and never executes shell commands.

## Install

```bash
# Clone the parent repository and install from source.
git clone https://github.com/fenre/splunk-monitoring-use-cases.git
cd splunk-monitoring-use-cases
pip install -e mcp/
```

Minimum Python 3.11. A PyPI release is tracked under Phase 7 of the
project roadmap.

## Usage

### Stdio (local, single-tenant)

Stdio is the default and strongly recommended transport — it eliminates
DNS-rebinding risks and requires no authentication surface. Launch the
server and let your MCP client (Cursor, Claude Desktop, Claude Code, MCP
Inspector) drive JSON-RPC over stdin/stdout.

```bash
# From a local clone of this repo — picks up api/v1 automatically:
splunk-uc-mcp

# Explicitly pointed at a clone:
splunk-uc-mcp --catalog-root /path/to/splunk-monitoring-use-cases

# Standalone (no local clone — fall back to the hosted mirror):
splunk-uc-mcp --base-url https://fenre.github.io/splunk-monitoring-use-cases

# Verbose logs on stderr (stdout stays reserved for JSON-RPC frames):
splunk-uc-mcp --verbose
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

Reload Cursor. The `splunk-uc` tool list appears in the MCP tools
pane.

### Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json`
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
claude mcp list   # verify: splunk-uc (stdio) — running
```

### MCP Inspector (debugging / smoke test)

```bash
npx @modelcontextprotocol/inspector splunk-uc-mcp \
  --catalog-root /absolute/path/to/splunk-monitoring-use-cases
```

## Tools

| Name | Purpose |
|------|---------|
| `search_use_cases` | Keyword + category / regulation / equipment / MITRE filter |
| `get_use_case` | Full SPL, implementation notes, compliance array for one UC |
| `list_categories` | The 23 categories with per-subcategory UC counts |
| `list_regulations` | All 60 regulations with tier, jurisdiction, tags |
| `get_regulation` | Regulation detail (optionally version-specific) |
| `list_equipment` | All 105 equipment slugs with UC + regulation counts |
| `get_equipment` | UCs grouped by category + regulation mappings for one slug |
| `find_compliance_gap` | Uncovered clauses per regulation; optional equipment overlay |

Full reference with request/response examples lives in
[`docs/mcp-server.md`](../docs/mcp-server.md).

## Resources

URI-addressable views over the same data:

- `uc://usecase/{uc_id}` — e.g. `uc://usecase/22.1.1`
- `uc://category/{cat_id}` — e.g. `uc://category/22`
- `reg://{regulation_id}` and `reg://{regulation_id}@{version}` — e.g. `reg://gdpr@2016-679`
- `equipment://{equipment_id}` — e.g. `equipment://azure`
- `ledger://` — signed provenance ledger (summary; local clone only)

## Persona transcripts (abbreviated)

Compliance officer → "What GDPR Art.32 clauses are still uncovered
for my Azure footprint?"

1. `find_compliance_gap({"regulations":["gdpr"], "equipment_id":"azure"})` → the
   gap list with an `equipmentOverlay` pointing at the UCs that already
   cover parts of the gap.
2. `reg://gdpr@2016-679` → human-readable article text to share with
   the business unit.
3. `get_use_case({"uc_id":"22.1.8"})` → full SPL + compliance[] for
   the single search that closes the largest uncovered clause.

Detection engineer → "Give me every UC that lights up on Cisco ISE
authentication telemetry."

1. `equipment://cisco_ise` → 34 UCs grouped by category.
2. `search_use_cases({"query":"brute force","equipment":"cisco_ise","limit":10})`.
3. `get_use_case({"uc_id":"1.1.65"})` → SPL + known false positives.

Longer transcripts, full argument/response shapes, and troubleshooting
recipes are in [`docs/mcp-server.md`](../docs/mcp-server.md).

## Security

The server follows the CoSAI MCP security guidance:

- Read-only. No MCP tool mutates any file or runs shell commands.
- Strict input validation on every identifier (regex-validated slugs,
  bounded URIs, 200-char query cap).
- 10 MB payload cap on both local reads and streamed HTTPS responses.
- Stdio transport only — no HTTP listener, no authentication surface
  to harden, no DNS-rebinding risk.
- Local catalog reads are sandboxed to `api/v1/` and `data/provenance/`;
  traversal sequences are rejected.
- HTTPS fallback only follows an allow-listed base URL (GitHub Pages
  by default).
- Tool-call arguments are SHA-256 hashed before logging (first 12 bytes).

## Development

```bash
pip install -e '.[test]'
pytest -q                               # 291 tests, <2s cold cache
python3 ../scripts/audit_mcp_tool_schemas.py   # drift guard
```

The drift guard is wired into
[`.github/workflows/validate.yml`](../.github/workflows/validate.yml)
so pull requests fail fast if a tool's `OUTPUT_SCHEMA` drifts from
the live `api/v1/*.json` shape.

## License

MIT (inherits from the parent repository).
