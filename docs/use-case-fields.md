# Use Case Fields (including SSE-aligned fields)

Use cases in this repo support the following optional fields. All are optional unless noted.

## Core fields (existing)

| Field | Markdown key | Description |
|-------|----------------|-------------|
| Criticality | **Criticality:** | 🔴 Critical, 🟠 High, 🟡 Medium, 🟢 Low |
| Difficulty | **Difficulty:** | 🟢 Beginner, 🔵 Intermediate, 🟠 Advanced, 🔴 Expert |
| Value | **Value:** | Why the use case matters. |
| App/TA | **App/TA:** | Splunk Add-ons or apps. |
| Data Sources | **Data Sources:** | Log/metric sources. |
| SPL | **SPL:** | Splunk search (in a ```spl block). |
| Implementation | **Implementation:** | How to deploy and operate (short summary). |
| Detailed implementation | **Detailed implementation:** | Optional. Multi-line step-by-step instructions; shown in the dashboard as “View more detailed instructions”. If omitted, build.py generates a standard set from the other fields. |
| Script example | **Script example:** | Optional. For scripted-input use cases: add a code block after this line with the script. Shown in the modal and in detailed instructions. See [Implementation guide](implementation-guide.md). |
| Visualization | **Visualization:** | Suggested dashboards/charts. |
| CIM Models | **CIM Models:** | Splunk CIM data model names the use case relies on (comma-separated, e.g. `Performance`, `Network_Traffic`, `Change`). See [CIM and data models](cim-and-data-models.md). |
| Premium Apps | **Premium Apps:** | Optional. Splunk premium products required for this use case when applicable (e.g. `Splunk Enterprise Security`, `Splunk ITSI`, `Splunk SOAR`). Omit when the use case works with Splunk Enterprise or Cloud alone. |
| Equipment Models | **Equipment Models:** | Optional. Specific hardware models the use case applies to (e.g. `Cisco Catalyst 9300, Catalyst 9500, ISR 4321, Meraki MX68`). Searchable in the UI — users can type a model number to find relevant use cases. Place after `App/TA`. |
| Data model acceleration | **Data model acceleration:** | Optional. Short note for implementers (e.g. "Enable for Performance, Network_Traffic" or "Required for tstats; summary range ≥30d"). Shown with CIM in the dashboard; [DMA docs](https://docs.splunk.com/Documentation/Splunk/latest/Knowledge/Acceleratedatamodels). |
| Schema | **Schema:** or **OCSF:** | Optional. Schema context: `CIM`, `OCSF`, or e.g. `OCSF: authentication` when the use case aligns with [OCSF](https://schema.ocsf.io/). |
| CIM SPL | **CIM SPL:** | tstats/accelerated query (optional). Requires the listed CIM models to be populated and accelerated. |
| Monitoring type | **Monitoring type:** | Availability, Performance, Security, etc. (comma-separated). |

## Quality metadata (optional, v5.1+)

These fields support the repository's quality and freshness tracking. They are **optional today** but CI will warn when they are missing and may gate new UCs in future versions.

| Field | Markdown key | Description |
|-------|----------------|-------------|
| Status | **Status:** | One of `verified` (production-ready), `community` (contributed, unreviewed), `draft` (work in progress). Default `community` when absent. |
| Last reviewed | **Last reviewed:** | ISO date `YYYY-MM-DD`. Shown on the dashboard as a freshness chip (green ≤6 mo, amber 6–12 mo, red >12 mo). |
| Splunk versions | **Splunk versions:** | Versions the use case is known to work on, e.g. `9.2+`, `9.3+`, `Cloud`. |
| Reviewer | **Reviewer:** | GitHub handle of the last reviewer, or `N/A`. |

### Example

```markdown
- **Status:** verified
- **Last reviewed:** 2026-04-16
- **Splunk versions:** 9.2+, Cloud
- **Reviewer:** @alice
```

## SSE-aligned fields (optional)

These match [Splunk Security Essentials](https://github.com/splunk/security_content) / security_content and help analysts and automation.

| Field | Markdown key | Description |
|-------|----------------|-------------|
| Known false positives | **Known false positives:** | When this detection may fire benignly; helps tuning and triage. |
| References | **References:** | URLs (comma- or semicolon-separated), e.g. MITRE, CVEs, vendor docs. |
| MITRE ATT&CK | **MITRE ATT&CK:** | Technique IDs, comma-separated (e.g. T1562.008, T1110.003). Shown as links in the dashboard. |
| Detection type | **Detection type:** | One of: TTP, Anomaly, Baseline, Hunting, Correlation. |
| Security domain | **Security domain:** | One of: endpoint, network, threat, identity, access, audit, cloud. |
| Required fields | **Required fields:** | Field names needed to run the search (comma-separated). |

### Example (in a UC block)

```markdown
- **Known false positives:** Legitimate admin teardown of CloudTrail; verify with change management.
- **References:** https://attack.mitre.org/techniques/T1562/008/
- **MITRE ATT&CK:** T1562.008
- **Detection type:** TTP
- **Security domain:** cloud
- **Required fields:** user_name, eventName, errorCode
```

### Where to add them

- **Security (cat-10):** All of these are relevant; add where you have the information (10.1–10.9, including ESCU).
- **Other categories:** Use when applicable. **References** (vendor/Splunk docs) and **Known false positives** (tuning context) are recommended for any use case where they add value. Detection type and Security domain are most relevant to security-focused UCs but can be used in others (e.g. cloud, IAM). Enrich non-security use cases with these fields where relevant so the repo stays consistent.

### Backfilling 10.9.x from security_content

The imported ESCU use cases (UC-10.9.x) were backfilled with Known false positives, References, MITRE ATT&CK, Detection type, and Security domain from the [security_content](https://github.com/splunk/security_content) YAMLs.

## Implementation ordering (optional, v1.4+)

Authors can mark each UC with a **wave** (crawl / walk / run) and list **prerequisite UCs** so readers can plan the rollout in the right order. Both fields are optional; absence means the UC has not yet been classified.

| Field | Markdown key | Description |
|-------|----------------|-------------|
| Wave | **Wave:** | One of `🐢 crawl` (foundation — platform + data sources + primary TAs), `🚶 walk` (intermediate — extends or correlates foundation data), or `🏃 run` (advanced — cross-source correlation, ML, or multi-UC orchestration). Emojis are optional; `crawl` / `walk` / `run` on their own also parse. |
| Prerequisite UCs | **Prerequisite UCs:** | Comma-separated list of UC IDs in `UC-X.Y.Z` form (e.g. `UC-1.1.1, UC-13.1.1`). These UCs must be implemented first because they provide data sources, macros, lookups, or upstream detections this one depends on. |

### Validation

`build.py` validates the graph after parsing:

- Unknown UC IDs are errors.
- Self-references (`UC-1.1.1` listing itself) are errors.
- Cycles in the dependency graph are errors (reported using Kahn's topological sort).
- A `walk` or `run` UC that lists a `crawl` prerequisite is expected; the reverse (a `crawl` UC depending on `run`) emits a warning to highlight likely mis-tags.

Wave counts are printed in the build summary (e.g. `Waves: crawl=120, walk=85, run=37, unassigned=6230`) so curators can see coverage at a glance.

### Display

- **Detail view** (dashboard + static pages): the UC shows a wave badge, a clickable "Implement first" list, and a reverse "Enables" list of UCs that depend on it.
- **Category/index view**: a `Crawl → Walk → Run` roadmap lists UCs per wave so curators can plan a rollout bottom-up.
- **API**: both `/api/v1/recommender/uc-thin.json` and `/api/v1/compliance/ucs/index.json` carry `wave` and `prerequisiteUseCases`; per-UC JSON twins also include a top-level `implementationOrdering` object with `wave`, `prerequisiteUseCases`, and a derived `enabledBy` array.

### Example (in a UC block)

```markdown
- **Wave:** 🚶 walk
- **Prerequisite UCs:** UC-1.1.1, UC-13.1.1
```
