---
id: "6.4.1"
title: "File Access Audit"
criticality: "high"
splunkPillar: "Security"
---

# UC-6.4.1 · File Access Audit

## Description

Provides full audit trail of file access for compliance (SOX, HIPAA, PCI-DSS). Enables investigation of data breaches and unauthorized access.

## Value

Provides full audit trail of file access for compliance (SOX, HIPAA, PCI-DSS). Enables investigation of data breaches and unauthorized access.

## Implementation

Enable "Audit Object Access" via GPO on file servers. Configure SACLs on sensitive folders. Forward Security logs via Universal Forwarder. Filter high-volume events to focus on sensitive paths.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows` (Security Event Log).
• Ensure the following data sources are available: Windows Security Event Log (Event ID 4663 — object access), NFS access logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable "Audit Object Access" via GPO on file servers. Configure SACLs on sensitive folders. Forward Security logs via Universal Forwarder. Filter high-volume events to focus on sensitive paths.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4663
| stats count by Account_Name, ObjectName, AccessMask
| sort -count
| head 50
```

Understanding this SPL

**File Access Audit** — Provides full audit trail of file access for compliance (SOX, HIPAA, PCI-DSS). Enables investigation of data breaches and unauthorized access.

Documented **Data sources**: Windows Security Event Log (Event ID 4663 — object access), NFS access logs. **App/TA** (typical add-on context): `Splunk_TA_windows` (Security Event Log). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by Account_Name, ObjectName, AccessMask** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Limits the number of rows with `head`.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (user, file, access type, count), Bar chart (top accessed files), Timeline (access events for specific files).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4663
| stats count by Account_Name, ObjectName, AccessMask
| sort -count
| head 50
```

## Visualization

Table (user, file, access type, count), Bar chart (top accessed files), Timeline (access events for specific files).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
