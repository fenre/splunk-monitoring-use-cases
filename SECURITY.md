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
- The Model Context Protocol<sup class="ref">[<a href="#ref-1">1</a>]</sup> server (`mcp/`, package `splunk-uc-mcp`) —
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
  in `ta/`, `splunk-apps/`, `content/`, and `catalog.json`
- Python scripts under `scripts/`, `tools/build/`, and `tools/audits/`
- The MCP server source under `mcp/src/splunk_uc_mcp/` (the JSON-RPC
  request/response handlers, the schema-validated tool surface, and the
  resource URI parsers)
- The static dashboard (`index.html`, shipped `dist/` pages, `custom-text.js`,
  `non-technical-view.js`, `regulatory-primer.html`, `scorecard.html`)
- The Data Sizing Assessment tool (`tools/data-sizing/index.html` + JS)
- Swagger UI assets in `vendor/swagger-ui/` (we pin checksums; tampered
  versions are an in-scope concern)
- GitHub Actions workflows under `.github/workflows/` and the Dependabot
  config at `.github/dependabot.yml`

**Out of scope:**

- Vulnerabilities in upstream Splunk products (Enterprise, ITSI, ES, CIM) —
  report those directly to Splunk via <https://www.splunk.com/en_us/product-security.html>
- Third-party Splunkbase<sup class="ref">[<a href="#ref-7">7</a>]</sup> TAs referenced in UC `References:` lines — report to
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
  the schemas defined inline in `mcp/src/splunk_uc_mcp/tools/`, with a CI guard
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

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** Anthropic, et al. (2026). *Model Context Protocol Specification*. Anthropic PBC. Retrieved May 11, 2026, from https://modelcontextprotocol.io/

<a id="ref-2"></a>**[2]** Cybersecurity and Infrastructure Security Agency. (2026). *CISA Known Exploited Vulnerabilities Catalog*. U.S. Department of Homeland Security. Retrieved May 11, 2026, from https://www.cisa.gov/known-exploited-vulnerabilities-catalog

<a id="ref-3"></a>**[3]** National Institute of Standards and Technology. (2012). *Computer Security Incident Handling Guide* (Revision 2). U.S. Department of Commerce. NIST SP 800-61 Rev. 2. Retrieved May 11, 2026, from https://csrc.nist.gov/pubs/sp/800/61/r2/final

<a id="ref-4"></a>**[4]** OWASP Foundation. (2026). *OWASP Cheat Sheet Series*. OWASP Foundation, Inc. Retrieved May 11, 2026, from https://cheatsheetseries.owasp.org/

<a id="ref-5"></a>**[5]** Splunk Inc. (2026). *Search Reference: SPL Commands and Functions*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/WhatsInThisManual

<a id="ref-6"></a>**[6]** Splunk Inc. (2026). *Splunk IT Service Intelligence Administration Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/ITSI

<a id="ref-7"></a>**[7]** Splunk Inc. (2026). *Splunkbase — the Splunk app marketplace*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://splunkbase.splunk.com/

<details>
<summary>Additional online sources cited in the document body (4)</summary>

<a id="ref-8"></a>**[8]** splunk.com. *splunk.com: Product Security*. Retrieved May 11, 2026, from https://www.splunk.com/en_us/product-security.html

<a id="ref-9"></a>**[9]** bugcrowd.com. *bugcrowd.com: Github*. Retrieved May 11, 2026, from https://bugcrowd.com/github

<a id="ref-10"></a>**[10]** github.com. *GitHub: fenre/splunk-monitoring-use-cases*. Retrieved May 11, 2026, from https://github.com/fenre/splunk-monitoring-use-cases/security/advisories/new

<a id="ref-11"></a>**[11]** github.com. *GitHub: fenre/splunk-monitoring-use-cases*. Retrieved May 11, 2026, from https://github.com/fenre/splunk-monitoring-use-cases/security/advisories

</details>

### Cited by

- [`docs/ci-architecture.md`](docs/ci-architecture.md)
- [`docs/enterprise-deployment.md`](docs/enterprise-deployment.md)
- [`docs/external-consumer-matrix.md`](docs/external-consumer-matrix.md)

<!-- END-AUTOGENERATED-SOURCES -->
