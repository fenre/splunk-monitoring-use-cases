---
id: "3.1.4"
title: "Container Memory Utilization"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.1.4 · Container Memory Utilization

## Description

Tracking memory usage relative to limits catches containers approaching OOM before they're killed. Enables proactive limit adjustments.

## Value

Tracking memory usage relative to limits catches containers approaching OOM before they're killed. Enables proactive limit adjustments.

## Implementation

Collect `docker stats` output at regular intervals. Alert when memory usage exceeds 80% of limit. Trend over time to catch gradual memory leaks.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Connect for Docker, custom scripted input.
• Ensure the following data sources are available: `sourcetype=docker:stats`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect `docker stats` output at regular intervals. Alert when memory usage exceeds 80% of limit. Trend over time to catch gradual memory leaks.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="docker:stats"
| eval mem_pct = round(mem_usage / mem_limit * 100, 1)
| stats latest(mem_pct) as mem_pct by container_name
| where mem_pct > 80
| sort -mem_pct
```

Understanding this SPL

**Container Memory Utilization** — Tracking memory usage relative to limits catches containers approaching OOM before they're killed. Enables proactive limit adjustments.

Documented **Data sources**: `sourcetype=docker:stats`. **App/TA** (typical add-on context): Splunk Connect for Docker, custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: docker:stats. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="docker:stats". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **mem_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by container_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where mem_pct > 80` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge per container, Table with limit context, Line chart (trending).

## SPL

```spl
index=containers sourcetype="docker:stats"
| eval mem_pct = round(mem_usage / mem_limit * 100, 1)
| stats latest(mem_pct) as mem_pct by container_name
| where mem_pct > 80
| sort -mem_pct
```

## Visualization

Gauge per container, Table with limit context, Line chart (trending).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
