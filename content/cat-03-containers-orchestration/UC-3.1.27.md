---
id: "3.1.27"
title: "Dangling Images and Volume Cleanup"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.1.27 · Dangling Images and Volume Cleanup

## Description

Orphaned image layers and anonymous volumes accumulate silently and can consume tens of gigabytes of disk. On CI/CD build hosts this is especially aggressive. Monitoring prevents disk-full incidents caused by Docker storage waste.

## Value

Orphaned image layers and anonymous volumes accumulate silently and can consume tens of gigabytes of disk. On CI/CD build hosts this is especially aggressive. Monitoring prevents disk-full incidents caused by Docker storage waste.

## Implementation

Run `docker system df -v --format json` on a schedule and forward the output to Splunk. Track `Reclaimable` bytes for images, volumes, and build cache. Alert when reclaimable space exceeds a threshold (e.g., 10 GB or 50% of Docker storage). For automated cleanup, trigger `docker system prune` via a webhook alert action, but only on non-production hosts. Track cleanup events to verify disk recovery.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `docker system df` scripted input.
• Ensure the following data sources are available: `sourcetype=docker:system_df`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Run `docker system df -v --format json` on a schedule and forward the output to Splunk. Track `Reclaimable` bytes for images, volumes, and build cache. Alert when reclaimable space exceeds a threshold (e.g., 10 GB or 50% of Docker storage). For automated cleanup, trigger `docker system prune` via a webhook alert action, but only on non-production hosts. Track cleanup events to verify disk recovery.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="docker:system_df"
| eval reclaimable_gb=round(reclaimable_bytes/1073741824,2)
| where type IN ("Images","Volumes","BuildCache") AND reclaimable_gb > 5
| table _time, host, type, total_count, active_count, size_gb, reclaimable_gb
| sort -reclaimable_gb
```

Understanding this SPL

**Dangling Images and Volume Cleanup** — Orphaned image layers and anonymous volumes accumulate silently and can consume tens of gigabytes of disk. On CI/CD build hosts this is especially aggressive. Monitoring prevents disk-full incidents caused by Docker storage waste.

Documented **Data sources**: `sourcetype=docker:system_df`. **App/TA** (typical add-on context): `docker system df` scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: docker:system_df. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="docker:system_df". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **reclaimable_gb** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where type IN ("Images","Volumes","BuildCache") AND reclaimable_gb > 5` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Dangling Images and Volume Cleanup**): table _time, host, type, total_count, active_count, size_gb, reclaimable_gb
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (reclaimable space per host), Line chart (storage growth trend), Table (hosts with most waste).

## SPL

```spl
index=containers sourcetype="docker:system_df"
| eval reclaimable_gb=round(reclaimable_bytes/1073741824,2)
| where type IN ("Images","Volumes","BuildCache") AND reclaimable_gb > 5
| table _time, host, type, total_count, active_count, size_gb, reclaimable_gb
| sort -reclaimable_gb
```

## Visualization

Gauge (reclaimable space per host), Line chart (storage growth trend), Table (hosts with most waste).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
