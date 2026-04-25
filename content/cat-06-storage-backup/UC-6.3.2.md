<!-- AUTO-GENERATED from UC-6.3.2.json — DO NOT EDIT -->

---
id: "6.3.2"
title: "Backup Job Duration Trending"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-6.3.2 · Backup Job Duration Trending

## Description

Increasing backup durations signal data growth, network congestion, or storage performance issues. Prevents backup window overruns.

## Value

Increasing backup durations signal data growth, network congestion, or storage performance issues. Prevents backup window overruns.

## Implementation

Calculate job duration from start/end timestamps. Track trend over weeks/months. Alert when duration exceeds historical average by >50%. Correlate with data volume changes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Vendor TA.
• Ensure the following data sources are available: Backup job logs (start/end timestamps, data transferred).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Calculate job duration from start/end timestamps. Track trend over weeks/months. Alert when duration exceeds historical average by >50%. Correlate with data volume changes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=backup sourcetype="veeam:job" status="Success"
| eval duration_min=(end_time-start_time)/60
| timechart span=1d avg(duration_min) as avg_duration by job_name
```

Understanding this SPL

**Backup Job Duration Trending** — Increasing backup durations signal data growth, network congestion, or storage performance issues. Prevents backup window overruns.

Documented **Data sources**: Backup job logs (start/end timestamps, data transferred). **App/TA** (typical add-on context): Vendor TA. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: backup; **sourcetype**: veeam:job. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=backup, sourcetype="veeam:job". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **duration_min** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=1d** buckets with a separate series **by job_name** — ideal for trending and alerting on this use case.


Step 3 — Validate
Compare job session state, duration, and transferred bytes with Veeam Backup & Replication or Veeam Enterprise Manager for the same job and time window.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. List media server, proxy, and repository names in the runbook, and when to open a ticket with the application team versus the backup team. Consider visualizations: Line chart (duration trend per job), Table (longest running jobs), Bar chart (avg duration by job).

## SPL

```spl
index=backup sourcetype="veeam:job" status="Success"
| eval duration_min=(end_time-start_time)/60
| timechart span=1d avg(duration_min) as avg_duration by job_name
```

## Visualization

Line chart (duration trend per job), Table (longest running jobs), Bar chart (avg duration by job).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
