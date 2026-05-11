# splunk-uc-mcp

[Model Context Protocol](https://modelcontextprotocol.io/) server for
the [Splunk Monitoring Use Cases catalogue](https://fenre.github.io/splunk-monitoring-use-cases/).
Read-only access to:

- **The full use case catalogue** across primary categories (operational, security, compliance, …)
- **Regulatory frameworks** (GDPR<sup class="ref">[<a href="#ref-4">4</a>]</sup>, HIPAA<sup class="ref">[<a href="#ref-12">12</a>]</sup>, PCI DSS, DORA<sup class="ref">[<a href="#ref-5">5</a>]</sup>, CMMC, NIS2<sup class="ref">[<a href="#ref-3">3</a>]</sup>, EU AI Act<sup class="ref">[<a href="#ref-6">6</a>]</sup>, …)
- **Equipment slugs** for Splunk add-ons and TAs (e.g. `cisco_asa`, `azure`, `kubernetes`)
- **Signed provenance ledger** (regulatory-to-UC mapping decisions)
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

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Primary sources

<a id="ref-1"></a>**[1]** Anthropic, et al. (2026). *Model Context Protocol Specification*. Anthropic PBC. Retrieved May 11, 2026, from https://modelcontextprotocol.io/

### Supporting sources

<a id="ref-2"></a>**[2]** Coalition for Secure AI (CoSAI). (2025, October). *MCP Security Guidance*. Coalition for Secure AI. Retrieved May 11, 2026, from https://www.coalitionforsecureai.org/

<a id="ref-3"></a>**[3]** European Parliament and Council of the European Union. (2022, December). *Directive (EU) 2022/2555 — NIS2 Directive on cybersecurity*. Official Journal of the European Union, L 333. ELI: dir/2022/2555. https://eur-lex.europa.eu/eli/dir/2022/2555/oj

<a id="ref-4"></a>**[4]** European Parliament and Council of the European Union. (2016, April). *Regulation (EU) 2016/679 — General Data Protection Regulation*. Official Journal of the European Union, L 119. ELI: reg/2016/679. https://eur-lex.europa.eu/eli/reg/2016/679/oj

<a id="ref-5"></a>**[5]** European Parliament and Council of the European Union. (2022, December). *Regulation (EU) 2022/2554 — Digital Operational Resilience Act (DORA)*. Official Journal of the European Union, L 333. ELI: reg/2022/2554. https://eur-lex.europa.eu/eli/reg/2022/2554/oj

<a id="ref-6"></a>**[6]** European Parliament and Council of the European Union. (2024, June). *Regulation (EU) 2024/1689 — EU Artificial Intelligence Act*. Official Journal of the European Union. ELI: reg/2024/1689. https://eur-lex.europa.eu/eli/reg/2024/1689/oj

<a id="ref-7"></a>**[7]** Payment Card Industry Security Standards Council. (2018). *Payment Card Industry Data Security Standard v3.2.1* (v3.2.1). PCI SSC. https://www.pcisecuritystandards.org/document_library/?category=pcidss

<a id="ref-8"></a>**[8]** Payment Card Industry Security Standards Council. (2022). *Payment Card Industry Data Security Standard v4.0* (v4.0). PCI SSC. https://www.pcisecuritystandards.org/document_library/?category=pcidss

<a id="ref-9"></a>**[9]** Splunk Inc. (2026). *Splunk Developer Documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://dev.splunk.com/

<a id="ref-10"></a>**[10]** Splunk Inc. (2026). *Splunk Enterprise Documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk

<a id="ref-11"></a>**[11]** U.S. Department of Health & Human Services. (2002). *HIPAA Privacy Rule (45 CFR Parts 160 and 164, Subparts A and E)*. Office for Civil Rights, HHS. 45 CFR 160, 164. https://www.hhs.gov/hipaa/for-professionals/privacy/index.html

<a id="ref-12"></a>**[12]** U.S. Department of Health & Human Services. (2013). *HIPAA Security Rule (45 CFR Parts 160 and 164, Subparts A and C)*. Office for Civil Rights, HHS. 45 CFR 160, 164. https://www.hhs.gov/hipaa/for-professionals/security/index.html

<!-- END-AUTOGENERATED-SOURCES -->
