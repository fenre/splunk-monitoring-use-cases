---
id: "1.1.77"
title: "Unauthorized Cron Job Additions"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.1.77 · Unauthorized Cron Job Additions

## Description

Unauthorized cron jobs enable persistent malware execution and data exfiltration.

## Value

Unauthorized cron jobs enable persistent malware execution and data exfiltration.

## Implementation

Monitor /var/spool/cron/crontabs/ and /etc/cron.d/ for modifications via auditctl. Create alerts on any new cron job additions. Compare against known application cron jobs from baseline.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=linux_audit`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor /var/spool/cron/crontabs/ and /etc/cron.d/ for modifications via auditctl. Create alerts on any new cron job additions. Compare against known application cron jobs from baseline.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=linux_audit path~="/var/spool/cron/crontabs/*" action=modified
| stats count by host, auid, file_name
| where count > 0
```

Understanding this SPL

**Unauthorized Cron Job Additions** — Unauthorized cron jobs enable persistent malware execution and data exfiltration.

Documented **Data sources**: `sourcetype=linux_audit`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: linux_audit. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=linux_audit. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, auid, file_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Alert, Table

## SPL

```spl
index=os sourcetype=linux_audit path~="/var/spool/cron/crontabs/*" action=modified
| stats count by host, auid, file_name
| where count > 0
```

## Visualization

Alert, Table

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
