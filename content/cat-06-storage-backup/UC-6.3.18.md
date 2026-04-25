<!-- AUTO-GENERATED from UC-6.3.18.json — DO NOT EDIT -->

---
id: "6.3.18"
title: "Backup Data Growth Trending by Workload"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-6.3.18 · Backup Data Growth Trending by Workload

## Description

Per-workload front-end bytes backed up trend identifies data sprawl, VM growth, or unexpected database growth before repository exhaustion.

## Value

Per-workload front-end bytes backed up trend identifies data sprawl, VM growth, or unexpected database growth before repository exhaustion.

## Implementation

Sum data per job daily. Use `predict` for growth. Alert when week-over-week growth exceeds threshold (e.g., 25%). Compare to repository free space.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Vendor TA.
• Ensure the following data sources are available: Job statistics `data_transferred_bytes` or `processed_size` per job/run.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Sum data per job daily. Use `predict` for growth. Alert when week-over-week growth exceeds threshold (e.g., 25%). Compare to repository free space.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=backup sourcetype="veeam:job" status="Success"
| timechart span=1d sum(data_transferred_gb) as daily_gb by job_name
| predict daily_gb as forecast future_timespan=30
```

Understanding this SPL

**Backup Data Growth Trending by Workload** — Per-workload front-end bytes backed up trend identifies data sprawl, VM growth, or unexpected database growth before repository exhaustion.

Documented **Data sources**: Job statistics `data_transferred_bytes` or `processed_size` per job/run. **App/TA** (typical add-on context): Vendor TA. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: backup; **sourcetype**: veeam:job. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=backup, sourcetype="veeam:job". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1d** buckets with a separate series **by job_name** — ideal for trending and alerting on this use case.
• Pipeline stage (see **Backup Data Growth Trending by Workload**): predict daily_gb as forecast future_timespan=30


Step 3 — Validate
Compare job session state, duration, and transferred bytes with Veeam Backup & Replication or Veeam Enterprise Manager for the same job and time window.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. List media server, proxy, and repository names in the runbook, and when to open a ticket with the application team versus the backup team. Consider visualizations: Line chart (daily GB with forecast per job), Table (fastest-growing jobs), Top values (growth %).

## SPL

```spl
index=backup sourcetype="veeam:job" status="Success"
| timechart span=1d sum(data_transferred_gb) as daily_gb by job_name
| predict daily_gb as forecast future_timespan=30
```

## Visualization

Line chart (daily GB with forecast per job), Table (fastest-growing jobs), Top values (growth %).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
