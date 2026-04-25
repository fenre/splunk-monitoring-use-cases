<!-- AUTO-GENERATED from UC-6.3.22.json — DO NOT EDIT -->

---
id: "6.3.22"
title: "Backup Job Overlap and Schedule Conflict Detection"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-6.3.22 · Backup Job Overlap and Schedule Conflict Detection

## Description

Overlapping full backups or too many concurrent jobs overload the backup infrastructure and extend backup windows. Detecting overlap supports schedule tuning and resource sizing.

## Value

Overlapping full backups or too many concurrent jobs overload the backup infrastructure and extend backup windows. Detecting overlap supports schedule tuning and resource sizing.

## Implementation

Ingest job start and duration. For each time window, count concurrent jobs per host or media server. Alert when more than N full backups run concurrently or when backup window is exceeded.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Backup vendor logs or API.
• Ensure the following data sources are available: Backup job start/end timestamps, job type (full/incremental).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest job start and duration. For each time window, count concurrent jobs per host or media server. Alert when more than N full backups run concurrently or when backup window is exceeded.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=backup sourcetype=backup_job
| eval start_epoch=_time end_epoch=_time+duration_sec
| stats values(job_name) as jobs by host, _time
| where mvcount(jobs) > 3
| table _time host jobs
```

Understanding this SPL

**Backup Job Overlap and Schedule Conflict Detection** — Overlapping full backups or too many concurrent jobs overload the backup infrastructure and extend backup windows. Detecting overlap supports schedule tuning and resource sizing.

Documented **Data sources**: Backup job start/end timestamps, job type (full/incremental). **App/TA** (typical add-on context): Backup vendor logs or API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: backup; **sourcetype**: backup_job. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=backup, sourcetype=backup_job. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **start_epoch** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by host, _time** so each row reflects one combination of those dimensions.
• Filters the current rows with `where mvcount(jobs) > 3` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Backup Job Overlap and Schedule Conflict Detection**): table _time host jobs


Step 3 — Validate
Compare the same metric, object name, and interval in the vendor or cloud console (array, backup, or object store) that is the source of truth for this feed.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. List media server, proxy, and repository names in the runbook, and when to open a ticket with the application team versus the backup team. Consider visualizations: Timeline (jobs by start/end), Table (overlapping jobs), Single value (max concurrent).

## SPL

```spl
index=backup sourcetype=backup_job
| eval start_epoch=_time end_epoch=_time+duration_sec
| stats values(job_name) as jobs by host, _time
| where mvcount(jobs) > 3
| table _time host jobs
```

## Visualization

Timeline (jobs by start/end), Table (overlapping jobs), Single value (max concurrent).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
