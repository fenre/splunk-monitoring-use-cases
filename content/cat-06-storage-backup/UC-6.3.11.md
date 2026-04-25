<!-- AUTO-GENERATED from UC-6.3.11.json — DO NOT EDIT -->

---
id: "6.3.11"
title: "Veeam Backup Job Status Summary"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-6.3.11 · Veeam Backup Job Status Summary

## Description

Roll-up of last job result per workload (Success/Warning/Failed/Running) for executive and NOC dashboards. Complements session-level detail with a single row per protected entity.

## Value

Roll-up of last job result per workload (Success/Warning/Failed/Running) for executive and NOC dashboards. Complements session-level detail with a single row per protected entity.

## Implementation

Schedule hourly. Map Warning to ticket for review. Escalate Failed immediately. Track Running jobs exceeding expected window as Warning.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Veeam App for Splunk, Enterprise Manager API.
• Ensure the following data sources are available: `veeam:job` or `veeam:job_session` with `job_name`, `status`, `end_time`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Schedule hourly. Map Warning to ticket for review. Escalate Failed immediately. Track Running jobs exceeding expected window as Warning.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=backup sourcetype="veeam:job_session"
| stats latest(_time) as last_end, latest(status) as status, latest(duration_sec) as duration by job_name
| where status IN ("Failed","Warning") OR duration > 28800
| table job_name last_end status duration
```

Understanding this SPL

**Veeam Backup Job Status Summary** — Roll-up of last job result per workload (Success/Warning/Failed/Running) for executive and NOC dashboards. Complements session-level detail with a single row per protected entity.

Documented **Data sources**: `veeam:job` or `veeam:job_session` with `job_name`, `status`, `end_time`. **App/TA** (typical add-on context): Veeam App for Splunk, Enterprise Manager API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: backup; **sourcetype**: veeam:job_session. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=backup, sourcetype="veeam:job_session". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by job_name** so each row reflects one combination of those dimensions.
• Filters the current rows with `where status IN ("Failed","Warning") OR duration > 28800` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Veeam Backup Job Status Summary**): table job_name last_end status duration


Step 3 — Validate
Compare job session state, duration, and transferred bytes with Veeam Backup & Replication or Veeam Enterprise Manager for the same job and time window.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. List media server, proxy, and repository names in the runbook, and when to open a ticket with the application team versus the backup team. Consider visualizations: Status grid (job × last status), Single value (failed count), Table (jobs needing attention).

## SPL

```spl
index=backup sourcetype="veeam:job_session"
| stats latest(_time) as last_end, latest(status) as status, latest(duration_sec) as duration by job_name
| where status IN ("Failed","Warning") OR duration > 28800
| table job_name last_end status duration
```

## Visualization

Status grid (job × last status), Single value (failed count), Table (jobs needing attention).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
