---
id: "1.1.94"
title: "Failed Log Forwarding"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.94 · Failed Log Forwarding

## Description

Failed log forwarding creates data loss in centralized logging infrastructure, creating gaps in monitoring and compliance.

## Value

Failed log forwarding creates data loss in centralized logging infrastructure, creating gaps in monitoring and compliance.

## Implementation

Monitor rsyslog/syslog-ng logs for forwarding failures. Create alerts on connection or name resolution errors. Include impact assessment showing how many events are being dropped.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=syslog, rsyslog/syslog-ng error logs`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor rsyslog/syslog-ng logs for forwarding failures. Create alerts on connection or name resolution errors. Include impact assessment showing how many events are being dropped.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=syslog ("rsyslog" OR "syslog-ng") ("error" OR "connection refused" OR "name resolution failed")
| stats count by host, remote_host
| where count > 0
```

Understanding this SPL

**Failed Log Forwarding** — Failed log forwarding creates data loss in centralized logging infrastructure, creating gaps in monitoring and compliance.

Documented **Data sources**: `sourcetype=syslog, rsyslog/syslog-ng error logs`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=syslog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, remote_host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Alert, Table

## SPL

```spl
index=os sourcetype=syslog ("rsyslog" OR "syslog-ng") ("error" OR "connection refused" OR "name resolution failed")
| stats count by host, remote_host
| where count > 0
```

## Visualization

Alert, Table

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
