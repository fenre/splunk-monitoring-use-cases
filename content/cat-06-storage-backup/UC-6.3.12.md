---
id: "6.3.12"
title: "Commvault Job Completion"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-6.3.12 · Commvault Job Completion

## Description

Failed or incomplete Commvault backup jobs leave subclients unprotected. Job-level success tracking is required for audit and restore confidence.

## Value

Failed or incomplete Commvault backup jobs leave subclients unprotected. Job-level success tracking is required for audit and restore confidence.

## Implementation

Ingest completed job events from Commvault. Normalize status values. Alert on Failed; report Partial with same severity as policy dictates.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Commvault Splunk App, Commvault REST/CLI export.
• Ensure the following data sources are available: Commvault job history (subclient, status, error code).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest completed job events from Commvault. Normalize status values. Alert on Failed; report Partial with same severity as policy dictates.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=backup sourcetype="commvault:job"
| where status!="Completed" OR job_status="Failed"
| stats latest(_time) as last_run, latest(error_code) as err by job_name, subclient_name
| table job_name subclient_name last_run err
```

Understanding this SPL

**Commvault Job Completion** — Failed or incomplete Commvault backup jobs leave subclients unprotected. Job-level success tracking is required for audit and restore confidence.

Documented **Data sources**: Commvault job history (subclient, status, error code). **App/TA** (typical add-on context): Commvault Splunk App, Commvault REST/CLI export. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: backup; **sourcetype**: commvault:job. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=backup, sourcetype="commvault:job". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where status!="Completed" OR job_status="Failed"` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by job_name, subclient_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Pipeline stage (see **Commvault Job Completion**): table job_name subclient_name last_run err


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (failed jobs), Single value (failed jobs 24h), Bar chart (failures by error code).

## SPL

```spl
index=backup sourcetype="commvault:job"
| where status!="Completed" OR job_status="Failed"
| stats latest(_time) as last_run, latest(error_code) as err by job_name, subclient_name
| table job_name subclient_name last_run err
```

## Visualization

Table (failed jobs), Single value (failed jobs 24h), Bar chart (failures by error code).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
