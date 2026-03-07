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
| Implementation | **Implementation:** | How to deploy and operate. |
| Visualization | **Visualization:** | Suggested dashboards/charts. |
| CIM Models | **CIM Models:** | Data model names (comma-separated). |
| CIM SPL | **CIM SPL:** | tstats/accelerated query (optional). |
| Monitoring type | **Monitoring type:** | Availability, Performance, Security, etc. (comma-separated). |

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

- **Security (cat-10):** All of these are relevant; add where you have the information (especially for 10.1–10.8 and any hand-written 10.9 UCs).
- **Other categories:** Use when applicable (e.g. References, Known false positives for any detection-style use case; MITRE/Detection type/Security domain only for security-focused UCs).

### Backfilling 10.9.x from security_content

The 1,988 imported ESCU use cases (UC-10.9.4 through 10.9.1990) were backfilled with Known false positives, References, MITRE ATT&CK, Detection type, and Security domain from the [security_content](https://github.com/splunk/security_content) YAMLs. To re-run the backfill after updating the clone:

```bash
cd use-cases
python3 backfill_sse_fields.py --repo /path/to/security_content
```

See [sse-import.md](sse-import.md) for full import and merge steps.
