---
id: "7.4.14"
title: "Databricks Job Failure Rate"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.4.14 · Databricks Job Failure Rate

## Description

Failed notebook/jar jobs block downstream analytics. Failure rate by job name prioritizes fixes for critical pipelines.

## Value

Failed notebook/jar jobs block downstream analytics. Failure rate by job name prioritizes fixes for critical pipelines.

## Implementation

Ingest each run completion. Alert on any failure for tier-1 jobs; use fail_rate for high-volume jobs. Include `run_page_url` in raw events for triage.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Databricks job run API, `jobs` audit.
• Ensure the following data sources are available: Job run result (`result_state`, `run_id`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest each run completion. Alert on any failure for tier-1 jobs; use fail_rate for high-volume jobs. Include `run_page_url` in raw events for triage.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=databricks sourcetype="databricks:job_run"
| bin _time span=1d
| stats count(eval(result_state="FAILED")) as failed, count as total by job_name, _time
| eval fail_rate=round(failed/total*100,1)
| where fail_rate > 5 OR failed > 0 AND total < 5
| table job_name failed total fail_rate
```

Understanding this SPL

**Databricks Job Failure Rate** — Failed notebook/jar jobs block downstream analytics. Failure rate by job name prioritizes fixes for critical pipelines.

Documented **Data sources**: Job run result (`result_state`, `run_id`). **App/TA** (typical add-on context): Databricks job run API, `jobs` audit. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: databricks; **sourcetype**: databricks:job_run. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=databricks, sourcetype="databricks:job_run". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by job_name, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **fail_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where fail_rate > 5 OR failed > 0 AND total < 5` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Databricks Job Failure Rate**): table job_name failed total fail_rate


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (failure rate by job), Table (failed runs), Single value (failed jobs 24h).

## SPL

```spl
index=databricks sourcetype="databricks:job_run"
| bin _time span=1d
| stats count(eval(result_state="FAILED")) as failed, count as total by job_name, _time
| eval fail_rate=round(failed/total*100,1)
| where fail_rate > 5 OR failed > 0 AND total < 5
| table job_name failed total fail_rate
```

## Visualization

Line chart (failure rate by job), Table (failed runs), Single value (failed jobs 24h).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
