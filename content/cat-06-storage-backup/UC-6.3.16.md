<!-- AUTO-GENERATED from UC-6.3.16.json — DO NOT EDIT -->

---
id: "6.3.16"
title: "Backup Window Utilization"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-6.3.16 · Backup Window Utilization

## Description

Jobs that consume most of the backup window risk overlap with production or fail to finish. Utilization % guides schedule tuning and parallel job limits.

## Value

Jobs that consume most of the backup window risk overlap with production or fail to finish. Utilization % guides schedule tuning and parallel job limits.

## Implementation

Define backup window per policy in lookup. Compare job duration to window length. Alert when utilization >85% or job end exceeds window end.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Vendor job logs.
• Ensure the following data sources are available: Job start/end, defined backup window start/end per policy.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Define backup window per policy in lookup. Compare job duration to window length. Alert when utilization >85% or job end exceeds window end.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=backup sourcetype="veeam:job" status="Success"
| eval duration_min=(end_time-start_time)/60
| lookup backup_policy job_name OUTPUT window_start_hour window_end_hour
| eval window_min=(window_end_hour-window_start_hour)*60
| eval util_pct=round(duration_min/window_min*100,1)
| where util_pct > 85
| table job_name duration_min window_min util_pct
```

Understanding this SPL

**Backup Window Utilization** — Jobs that consume most of the backup window risk overlap with production or fail to finish. Utilization % guides schedule tuning and parallel job limits.

Documented **Data sources**: Job start/end, defined backup window start/end per policy. **App/TA** (typical add-on context): Vendor job logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: backup; **sourcetype**: veeam:job. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=backup, sourcetype="veeam:job". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **duration_min** — often to normalize units, derive a ratio, or prepare for thresholds.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• `eval` defines or adjusts **window_min** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **util_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where util_pct > 85` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Backup Window Utilization**): table job_name duration_min window_min util_pct


Step 3 — Validate
Compare job session state, duration, and transferred bytes with Veeam Backup & Replication or Veeam Enterprise Manager for the same job and time window.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. List media server, proxy, and repository names in the runbook, and when to open a ticket with the application team versus the backup team. Consider visualizations: Bar chart (utilization % by job), Line chart (duration trend vs window), Table (jobs at risk of overrun).

## SPL

```spl
index=backup sourcetype="veeam:job" status="Success"
| eval duration_min=(end_time-start_time)/60
| lookup backup_policy job_name OUTPUT window_start_hour window_end_hour
| eval window_min=(window_end_hour-window_start_hour)*60
| eval util_pct=round(duration_min/window_min*100,1)
| where util_pct > 85
| table job_name duration_min window_min util_pct
```

## Visualization

Bar chart (utilization % by job), Line chart (duration trend vs window), Table (jobs at risk of overrun).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
