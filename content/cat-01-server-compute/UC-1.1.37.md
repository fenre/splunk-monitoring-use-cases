---
id: "1.1.37"
title: "NFS Mount Stale Handle Detection"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.1.37 · NFS Mount Stale Handle Detection

## Description

Stale NFS handles cause application hangs and I/O failures that severely impact users.

## Value

Stale NFS handles cause application hangs and I/O failures that severely impact users.

## Implementation

Monitor kernel logs and NFS client logs for stale handle errors. Create immediate alerts with escalation to storage team. Add search to identify affected processes and suggest remount or NFS server recovery.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=syslog, kernel NFS logs`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor kernel logs and NFS client logs for stale handle errors. Create immediate alerts with escalation to storage team. Add search to identify affected processes and suggest remount or NFS server recovery.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=syslog "nfs" ("stale" OR "stale NFS file handle" OR "Stale NFS")
| stats count by host, nfs_server
| where count > 0
```

Understanding this SPL

**NFS Mount Stale Handle Detection** — Stale NFS handles cause application hangs and I/O failures that severely impact users.

Documented **Data sources**: `sourcetype=syslog, kernel NFS logs`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=syslog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, nfs_server** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Alert, Table

## SPL

```spl
index=os sourcetype=syslog "nfs" ("stale" OR "stale NFS file handle" OR "Stale NFS")
| stats count by host, nfs_server
| where count > 0
```

## Visualization

Alert, Table

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
