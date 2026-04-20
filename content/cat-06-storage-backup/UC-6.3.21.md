---
id: "6.3.21"
title: "Restore Job Success and Duration Trending"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-6.3.21 · Restore Job Success and Duration Trending

## Description

Restore failures or abnormally long restores indicate corrupt backups, network issues, or misconfiguration. Tracking ensures recovery procedures are validated and RTO is achievable.

## Value

Restore failures or abnormally long restores indicate corrupt backups, network issues, or misconfiguration. Tracking ensures recovery procedures are validated and RTO is achievable.

## Implementation

Ingest restore job completion events. Track success/failure and duration. Alert on any restore failure. Baseline restore duration by job type; alert when duration exceeds 2x baseline. Run periodic test restores and log results.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Backup vendor logs, job status API.
• Ensure the following data sources are available: Restore job status, duration, bytes restored.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest restore job completion events. Track success/failure and duration. Alert on any restore failure. Baseline restore duration by job type; alert when duration exceeds 2x baseline. Run periodic test restores and log results.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=backup sourcetype=backup_restore job_type=restore
| bin _time span=1d
| stats count(eval(status="failed")) as failures, count(eval(status="success")) as success, avg(duration_sec) as avg_duration by job_name, _time
| eval fail_rate=round(failures/(failures+success)*100, 1)
| where failures > 0 OR avg_duration > 3600
```

Understanding this SPL

**Restore Job Success and Duration Trending** — Restore failures or abnormally long restores indicate corrupt backups, network issues, or misconfiguration. Tracking ensures recovery procedures are validated and RTO is achievable.

Documented **Data sources**: Restore job status, duration, bytes restored. **App/TA** (typical add-on context): Backup vendor logs, job status API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: backup; **sourcetype**: backup_restore. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=backup, sourcetype=backup_restore. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by job_name, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **fail_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where failures > 0 OR avg_duration > 3600` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (job, success, failures, avg duration), Line chart (restore duration trend), Single value (last 7d fail rate).

## SPL

```spl
index=backup sourcetype=backup_restore job_type=restore
| bin _time span=1d
| stats count(eval(status="failed")) as failures, count(eval(status="success")) as success, avg(duration_sec) as avg_duration by job_name, _time
| eval fail_rate=round(failures/(failures+success)*100, 1)
| where failures > 0 OR avg_duration > 3600
```

## Visualization

Table (job, success, failures, avg duration), Line chart (restore duration trend), Single value (last 7d fail rate).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
