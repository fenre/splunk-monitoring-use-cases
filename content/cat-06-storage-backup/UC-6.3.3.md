---
id: "6.3.3"
title: "Missed Backup Detection"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-6.3.3 · Missed Backup Detection

## Description

A backup that doesn't run at all is worse than one that fails — it's invisible. Detection ensures no system is left unprotected.

## Value

A backup that doesn't run at all is worse than one that fails — it's invisible. Detection ensures no system is left unprotected.

## Implementation

Maintain a lookup table of expected backup schedules. Run a scheduled search comparing expected vs actual runs. Alert when any job misses its window. Correlate with backup server health events.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Vendor TA, custom correlation.
• Ensure the following data sources are available: Backup scheduler logs, expected schedule lookup.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Maintain a lookup table of expected backup schedules. Run a scheduled search comparing expected vs actual runs. Alert when any job misses its window. Correlate with backup server health events.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
| inputlookup backup_schedule.csv
| join type=left max=1 job_name
    [search index=backup sourcetype="veeam:job" earliest=-24h
     | stats latest(_time) as last_run by job_name]
| where isnull(last_run) OR last_run < relative_time(now(), "-26h")
| table job_name, expected_schedule, last_run
```

Understanding this SPL

**Missed Backup Detection** — A backup that doesn't run at all is worse than one that fails — it's invisible. Detection ensures no system is left unprotected.

Documented **Data sources**: Backup scheduler logs, expected schedule lookup. **App/TA** (typical add-on context): Vendor TA, custom correlation. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Loads rows via `inputlookup` (KV store or CSV lookup) for enrichment or reporting.
• Joins to a subsearch with `join` — set `max=` to match cardinality and avoid silent truncation.
• Filters the current rows with `where isnull(last_run) OR last_run < relative_time(now(), "-26h")` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Missed Backup Detection**): table job_name, expected_schedule, last_run


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (missed jobs with schedule details), Single value (number of missed jobs), Status grid (job name × date).

## SPL

```spl
| inputlookup backup_schedule.csv
| join type=left max=1 job_name
    [search index=backup sourcetype="veeam:job" earliest=-24h
     | stats latest(_time) as last_run by job_name]
| where isnull(last_run) OR last_run < relative_time(now(), "-26h")
| table job_name, expected_schedule, last_run
```

## Visualization

Table (missed jobs with schedule details), Single value (number of missed jobs), Status grid (job name × date).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
