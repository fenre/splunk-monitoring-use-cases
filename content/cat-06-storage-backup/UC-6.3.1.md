<!-- AUTO-GENERATED from UC-6.3.1.json — DO NOT EDIT -->

---
id: "6.3.1"
title: "Backup Job Success Rate"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-6.3.1 · Backup Job Success Rate

## Description

Failed backups leave systems unprotected. Tracking success rate ensures recoverability and compliance with data protection policies.

## Value

Failed backups leave systems unprotected. Tracking success rate ensures recoverability and compliance with data protection policies.

## Implementation

For Veeam: use the Veeam App for Splunk or ingest via HEC from Enterprise Manager REST (`/api/v1/jobSessions`); normalize `job_name`, `result`, `end_time` fields. For Veritas NetBackup: forward master/media server syslog or use the OpsCenter REST export. Alert when `result!=Success` for jobs flagged as `backup_tier=critical` in a lookup. Throttle per `job_name` to avoid alert storms during infrastructure outages.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Veeam App for Splunk, Commvault Splunk App, or scripted API input.
• Ensure the following data sources are available: Backup server job logs (job name, status, start/end time, data size).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
For Veeam: use the Veeam App for Splunk or ingest via HEC from Enterprise Manager REST (`/api/v1/jobSessions`); normalize `job_name`, `result`, `end_time` fields. For Veritas NetBackup: forward master/media server syslog or use the OpsCenter REST export. Alert when `result!=Success` for jobs flagged as `backup_tier=critical` in a lookup. Throttle per `job_name` to avoid alert storms during infrastructure outages.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=backup sourcetype="veeam:job"
| stats count(eval(status="Success")) as success, count(eval(status="Failed")) as failed, count as total by job_name
| eval success_rate=round(success/total*100,1)
| where success_rate < 100
| sort success_rate
```

Understanding this SPL

**Backup Job Success Rate** — Failed backups leave systems unprotected. Tracking success rate ensures recoverability and compliance with data protection policies.

Documented **Data sources**: Backup server job logs (job name, status, start/end time, data size). **App/TA** (typical add-on context): Veeam App for Splunk, Commvault Splunk App, or scripted API input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: backup; **sourcetype**: veeam:job. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=backup, sourcetype="veeam:job". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by job_name** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **success_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where success_rate < 100` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare job session state, duration, and transferred bytes with Veeam Backup & Replication or Veeam Enterprise Manager for the same job and time window.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. List media server, proxy, and repository names in the runbook, and when to open a ticket with the application team versus the backup team. Consider visualizations: Single value (overall success rate %), Table (failed jobs with details), Bar chart (success/fail by job), Trend line (daily success rate).

## SPL

```spl
index=backup sourcetype="veeam:job"
| stats count(eval(status="Success")) as success, count(eval(status="Failed")) as failed, count as total by job_name
| eval success_rate=round(success/total*100,1)
| where success_rate < 100
| sort success_rate
```

## Visualization

Single value (overall success rate %), Table (failed jobs with details), Bar chart (success/fail by job), Trend line (daily success rate).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
