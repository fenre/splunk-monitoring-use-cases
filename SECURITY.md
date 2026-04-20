# Security Policy

This repository ships **Splunk content** (SPL saved searches, conf files, a
static dashboard, and a Python build pipeline) — not a networked service. The
attack surface is narrow, but we take vulnerabilities in any of the following
seriously:

- SPL that exfiltrates data, runs arbitrary commands, or bypasses CIM/ACL
  boundaries
- Build-pipeline scripts that could be weaponised against forkers (supply-chain
  attacks)
- The static dashboard (`index.html` + vendored Swagger UI) — DOM XSS, data
  leakage, or prototype pollution
- The packaged Splunk content shipped under `ta/` (`TA-splunk-use-cases`,
  `DA-ITSI-monitoring-use-cases`, `DA-ESS-monitoring-use-cases`) and the 10
  regulation packs + recommender app + recommender TA shipped under
  `splunk-apps/` — configuration that could cause denial-of-service on a
  Splunk search head, leak data across tenants, or (for the recommender TA)
  expose the modular-input REST surface
- The Model Context Protocol server (`mcp/`, package `splunk-uc-mcp`) —
  read-only by construction, stdio-only transport (no network listener), but
  any input-handling defect that allows path traversal off the catalogue
  root, or any tool that returns more data than its schema advertises, is in
  scope

## Reporting a vulnerability

**Please do NOT open a public GitHub issue for security reports.**

Send vulnerability reports **privately** to one of the following channels:

1. Preferred — [GitHub private vulnerability reporting][gh-psirt] for
   `fenre/splunk-monitoring-use-cases`.
2. Alternative — email **fsudmann@gmail.com** with the subject line
   `[SECURITY] splunk-monitoring-use-cases`.

Please include:

- A clear description of the issue and its impact (what an attacker could
  achieve)
- A minimal reproducer: specific UC ID(s), SPL snippet, file/line references,
  or a tag/commit that demonstrates the issue
- Your preferred disclosure timeline
- Whether you would like credit in the release notes (and the name to use)

We will:

- Acknowledge receipt within **3 business days**
- Triage and respond with an initial assessment within **10 business days**
- Coordinate a fix timeline proportional to severity (critical issues fast-
  tracked; low-severity issues may be batched into the next minor release)
- Publish a fix and a [GitHub Security Advisory][ghsa] once available
- Credit the reporter in the advisory and CHANGELOG (unless you prefer
  anonymity)

## Scope

**In scope:**

- All SPL saved searches, macros, eventtypes, and correlation searches shipped
  in `ta/`, `splunk-apps/`, `use-cases/`, and `catalog.json`
- Python scripts under `scripts/` and `build.py`
- The MCP server source under `mcp/src/splunk_uc_mcp/` (the JSON-RPC
  request/response handlers, the schema-validated tool surface, and the
  resource URI parsers)
- The static dashboard (`index.html`, `data.js`, `custom-text.js`,
  `non-technical-view.js`, `regulatory-primer.html`, `scorecard.html`)
- The Data Sizing Assessment tool (`tools/data-sizing/index.html` + JS)
- Swagger UI assets in `vendor/swagger-ui/` (we pin checksums; tampered
  versions are an in-scope concern)
- GitHub Actions workflows under `.github/workflows/` and the Dependabot
  config at `.github/dependabot.yml`

**Out of scope:**

- Vulnerabilities in upstream Splunk products (Enterprise, ITSI, ES, CIM) —
  report those directly to Splunk via <https://www.splunk.com/en_us/product-security.html>
- Third-party Splunkbase TAs referenced in UC `References:` lines — report to
  the respective vendor
- Social-engineering, physical, or DoS attacks on the GitHub infrastructure
  itself — report to GitHub at <https://bugcrowd.com/github>

## Supported versions

We support the **two most recent minor versions** of the catalog with security
fixes. Older versions continue to function but do not receive patches.

| Version | Supported |
|---------|-----------|
| 7.0.x   | ✅ |
| 6.1.x   | ✅ |
| < 6.1   | ❌ |

## Safe defaults

The project's design includes several defence-in-depth measures that security
reviewers should be aware of:

- Every shipped saved search / correlation search is `disabled = 1` by
  default — installing a content pack cannot by itself trigger alerts or
  generate load.
- Index macros (`uc_index_*`) default to `index=*` but are intended to be
  overridden before use. A misconfigured install cannot exfiltrate beyond the
  Splunk user's existing role scope.
- The 13 packs under `ta/` and `splunk-apps/` (excluding the recommender
  TA) are **configuration-only** — no scripts, no modular inputs, no REST
  endpoints — and can be reviewed deterministically.  The
  `splunk-uc-recommender-ta` is the lone exception: it ships one custom
  modular input (`uc_recommender_modular`) whose source lives under
  `splunk-apps/splunk-uc-recommender-ta/bin/` and is reviewed during every
  release.
- The MCP server (`mcp/`) is read-only by construction (no `write`, no
  `delete`, no shell-out) and uses stdio-only transport (no network
  listener), eliminating the entire class of remote-network attack
  surfaces.  Tool inputs and outputs are JSON-Schema-validated against
  the schemas in `mcp/src/splunk_uc_mcp/schemas/`, with a CI guard
  (`scripts/audit_mcp_tool_schemas.py`) that fails the build if the
  shipped schemas drift from the runtime ones.
- Swagger UI assets are self-hosted under `vendor/swagger-ui/` with
  SHA-256 checksums in `vendor/swagger-ui/checksums.txt` to guard against CDN
  compromise.

## Responsible disclosure timeline

Once a valid vulnerability is confirmed, we aim for the following timelines:

| Severity | Initial fix target |
|----------|--------------------|
| Critical (data exfiltration, RCE) | 7 days |
| High (significant data leak, persistent auth bypass) | 30 days |
| Medium (limited impact, requires specific Splunk configuration) | 60 days |
| Low (best-practice improvements) | Next minor release |

Reporters are welcome to publish their findings after a fix is released; please
coordinate with us on timing so the release note + advisory goes out first.

[gh-psirt]: https://github.com/fenre/splunk-monitoring-use-cases/security/advisories/new
[ghsa]: https://github.com/fenre/splunk-monitoring-use-cases/security/advisories
