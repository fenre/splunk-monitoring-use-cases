---
id: "1.1.40"
title: "XFS Filesystem Errors and Recovery"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.40 · XFS Filesystem Errors and Recovery

## Description

XFS errors indicate potential corruption in high-performance storage systems commonly used in enterprise environments.

## Value

XFS errors indicate potential corruption in high-performance storage systems commonly used in enterprise environments.

## Implementation

Monitor XFS-specific kernel messages. Create alerts for any XFS I/O errors or shutdown messages. Include xfs_repair suggestions and track patterns across storage arrays.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=syslog, kernel logs`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor XFS-specific kernel messages. Create alerts for any XFS I/O errors or shutdown messages. Include xfs_repair suggestions and track patterns across storage arrays.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=syslog host=* ("XFS" OR "xfs_*" AND ("error" OR "IO Error" OR "shutdown"))
| stats count by host, mount_point
| where count > 0
```

Understanding this SPL

**XFS Filesystem Errors and Recovery** — XFS errors indicate potential corruption in high-performance storage systems commonly used in enterprise environments.

Documented **Data sources**: `sourcetype=syslog, kernel logs`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=syslog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, mount_point** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Alert, Table

## SPL

```spl
index=os sourcetype=syslog host=* ("XFS" OR "xfs_*" AND ("error" OR "IO Error" OR "shutdown"))
| stats count by host, mount_point
| where count > 0
```

## Visualization

Alert, Table

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
