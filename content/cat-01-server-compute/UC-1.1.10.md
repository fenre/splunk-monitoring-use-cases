---
id: "1.1.10"
title: "Cron Job Failure Monitoring"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.10 · Cron Job Failure Monitoring

## Description

Failed cron jobs can silently break batch processing, backups, log rotation, and maintenance tasks. Catching failures early prevents cascading issues.

## Value

Failed cron jobs can silently break batch processing, backups, log rotation, and maintenance tasks. Catching failures early prevents cascading issues.

## Implementation

Forward `/var/log/cron`. For critical cron jobs, create a "heartbeat" approach: expect a success message within a window, alert on absence. Use `| inputlookup expected_crons | join` pattern for missing run detection.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`, Syslog.
• Ensure the following data sources are available: `sourcetype=cron` or `sourcetype=syslog` source="/var/log/cron".
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward `/var/log/cron`. For critical cron jobs, create a "heartbeat" approach: expect a success message within a window, alert on absence. Use `| inputlookup expected_crons | join` pattern for missing run detection.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os (sourcetype=cron OR source="/var/log/cron") ("error" OR "failed" OR "EXIT STATUS" OR "ORPHAN")
| rex "CMD \((?<cron_cmd>[^)]+)\)"
| rex "CROND\[(?<pid>\d+)\]"
| stats count by host, cron_cmd, _time
| sort -_time
```

Understanding this SPL

**Cron Job Failure Monitoring** — Failed cron jobs can silently break batch processing, backups, log rotation, and maintenance tasks. Catching failures early prevents cascading issues.

Documented **Data sources**: `sourcetype=cron` or `sourcetype=syslog` source="/var/log/cron". **App/TA** (typical add-on context): `Splunk_TA_nix`, Syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: cron. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=cron. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• Extracts fields with `rex` (regular expression).
• `stats` rolls up events into metrics; results are split **by host, cron_cmd, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of failed cron jobs, Single value panel (failures last 24h), Missing job detection table.

## SPL

```spl
index=os (sourcetype=cron OR source="/var/log/cron") ("error" OR "failed" OR "EXIT STATUS" OR "ORPHAN")
| rex "CMD \((?<cron_cmd>[^)]+)\)"
| rex "CROND\[(?<pid>\d+)\]"
| stats count by host, cron_cmd, _time
| sort -_time
```

## Visualization

Table of failed cron jobs, Single value panel (failures last 24h), Missing job detection table.

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
