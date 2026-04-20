---
id: "1.1.68"
title: "Rootkit Detection via File Integrity"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.1.68 · Rootkit Detection via File Integrity

## Description

File integrity changes indicate potential rootkit installation or unauthorized system modification.

## Value

File integrity changes indicate potential rootkit installation or unauthorized system modification.

## Implementation

Deploy AIDE (Advanced Intrusion Detection Environment) with daily scans. Create alerts for unexpected file changes in /bin, /sbin, /lib directories. Include baseline scans on system initialization.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=custom:aide, AIDE database changes`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy AIDE (Advanced Intrusion Detection Environment) with daily scans. Create alerts for unexpected file changes in /bin, /sbin, /lib directories. Include baseline scans on system initialization.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=custom:aide host=*
| stats count by host, file_path, change_type
| where change_type IN ("added", "changed", "removed") AND count > 0
```

Understanding this SPL

**Rootkit Detection via File Integrity** — File integrity changes indicate potential rootkit installation or unauthorized system modification.

Documented **Data sources**: `sourcetype=custom:aide, AIDE database changes`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: custom:aide. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=custom:aide. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, file_path, change_type** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where change_type IN ("added", "changed", "removed") AND count > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Alert, Table

## SPL

```spl
index=os sourcetype=custom:aide host=*
| stats count by host, file_path, change_type
| where change_type IN ("added", "changed", "removed") AND count > 0
```

## Visualization

Alert, Table

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
