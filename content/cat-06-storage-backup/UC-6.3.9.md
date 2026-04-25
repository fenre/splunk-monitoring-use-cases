<!-- AUTO-GENERATED from UC-6.3.9.json — DO NOT EDIT -->

---
id: "6.3.9"
title: "Veeam Backup Job Monitoring"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-6.3.9 · Veeam Backup Job Monitoring

## Description

Job success/failure/warning status, duration, and data transferred are essential for backup reliability. Immediate visibility into job outcomes ensures data protection SLAs are met and enables rapid troubleshooting.

## Value

Job success/failure/warning status, duration, and data transferred are essential for backup reliability. Immediate visibility into job outcomes ensures data protection SLAs are met and enables rapid troubleshooting.

## Implementation

Use Veeam Enterprise Manager REST API (`/api/sessionMgr`) or PowerShell script invoking `Get-VBRSession` to collect job session data. Poll every 15–30 minutes or trigger on job completion. Extract job_name, status (Success/Failed/Warning), start/end time (for duration), and data transferred. Index to Splunk with sourcetype `veeam:job_session`. Alert immediately on status=Failed; warning on status=Warning. Alert when duration exceeds backup window (e.g., >8 hours).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom (Veeam Enterprise Manager REST API, PowerShell output).
• Ensure the following data sources are available: Veeam job session data (REST API or PowerShell Get-VBRSession).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use Veeam Enterprise Manager REST API (`/api/sessionMgr`) or PowerShell script invoking `Get-VBRSession` to collect job session data. Poll every 15–30 minutes or trigger on job completion. Extract job_name, status (Success/Failed/Warning), start/end time (for duration), and data transferred. Index to Splunk with sourcetype `veeam:job_session`. Alert immediately on status=Failed; warning on status=Warning. Alert when duration exceeds backup window (e.g., >8 hours).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=backup sourcetype="veeam:job_session"
| stats latest(_time) as last_run, latest(status) as status, latest(duration_min) as duration_min, latest(data_transferred_gb) as data_gb by job_name
| where status!="Success" OR duration_min>480
| table job_name, last_run, status, duration_min, data_gb
| sort last_run
```

Understanding this SPL

**Veeam Backup Job Monitoring** — Job success/failure/warning status, duration, and data transferred are essential for backup reliability. Immediate visibility into job outcomes ensures data protection SLAs are met and enables rapid troubleshooting.

Documented **Data sources**: Veeam job session data (REST API or PowerShell Get-VBRSession). **App/TA** (typical add-on context): Custom (Veeam Enterprise Manager REST API, PowerShell output). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: backup; **sourcetype**: veeam:job_session. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=backup, sourcetype="veeam:job_session". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by job_name** so each row reflects one combination of those dimensions.
• Filters the current rows with `where status!="Success" OR duration_min>480` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Veeam Backup Job Monitoring**): table job_name, last_run, status, duration_min, data_gb
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare job session state, duration, and transferred bytes with Veeam Backup & Replication or Veeam Enterprise Manager for the same job and time window.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. List media server, proxy, and repository names in the runbook, and when to open a ticket with the application team versus the backup team. Consider visualizations: Table (job, status, duration, data transferred), Single value (failed jobs count), Bar chart (duration by job), Status grid (job × date).

## SPL

```spl
index=backup sourcetype="veeam:job_session"
| stats latest(_time) as last_run, latest(status) as status, latest(duration_min) as duration_min, latest(data_transferred_gb) as data_gb by job_name
| where status!="Success" OR duration_min>480
| table job_name, last_run, status, duration_min, data_gb
| sort last_run
```

## Visualization

Table (job, status, duration, data transferred), Single value (failed jobs count), Bar chart (duration by job), Status grid (job × date).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
