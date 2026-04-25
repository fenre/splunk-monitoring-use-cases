<!-- AUTO-GENERATED from UC-6.3.7.json — DO NOT EDIT -->

---
id: "6.3.7"
title: "Backup Data Volume Trending"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-6.3.7 · Backup Data Volume Trending

## Description

Tracks data growth rate for capacity planning of backup infrastructure. Identifies unexpected data surges early.

## Value

Tracks data growth rate for capacity planning of backup infrastructure. Identifies unexpected data surges early.

## Implementation

Sum data transferred across all backup jobs daily. Track trend and apply predictive analytics for 30/60/90-day forecasts. Compare against available repository capacity.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Vendor TA.
• Ensure the following data sources are available: Backup job statistics (data transferred per job).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Sum data transferred across all backup jobs daily. Track trend and apply predictive analytics for 30/60/90-day forecasts. Compare against available repository capacity.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=backup sourcetype="veeam:job" status="Success"
| timechart span=1d sum(data_transferred_gb) as daily_volume
| predict daily_volume as predicted future_timespan=30
```

Understanding this SPL

**Backup Data Volume Trending** — Tracks data growth rate for capacity planning of backup infrastructure. Identifies unexpected data surges early.

Documented **Data sources**: Backup job statistics (data transferred per job). **App/TA** (typical add-on context): Vendor TA. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: backup; **sourcetype**: veeam:job. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=backup, sourcetype="veeam:job". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1d** buckets — ideal for trending and alerting on this use case.
• Pipeline stage (see **Backup Data Volume Trending**): predict daily_volume as predicted future_timespan=30


Step 3 — Validate
Compare job session state, duration, and transferred bytes with Veeam Backup & Replication or Veeam Enterprise Manager for the same job and time window.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. List media server, proxy, and repository names in the runbook, and when to open a ticket with the application team versus the backup team. Consider visualizations: Line chart (daily backup volume with prediction), Bar chart (volume by job type), Single value (total backed up today).

## SPL

```spl
index=backup sourcetype="veeam:job" status="Success"
| timechart span=1d sum(data_transferred_gb) as daily_volume
| predict daily_volume as predicted future_timespan=30
```

## Visualization

Line chart (daily backup volume with prediction), Bar chart (volume by job type), Single value (total backed up today).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
