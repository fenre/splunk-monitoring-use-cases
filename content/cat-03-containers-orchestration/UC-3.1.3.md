---
id: "3.1.3"
title: "Container CPU Throttling"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.1.3 · Container CPU Throttling

## Description

CPU throttling means the container is hitting its CPU limit and being artificially slowed. Causes latency spikes invisible to standard CPU utilization metrics.

## Value

CPU throttling means the container is hitting its CPU limit and being artificially slowed. Causes latency spikes invisible to standard CPU utilization metrics.

## Implementation

Collect Docker stats via `docker stats --format '{{json .}}'` or read cgroup files directly (`/sys/fs/cgroup/cpu/docker/<id>/cpu.stat`). Monitor `throttled_time` and `nr_throttled`. Alert when >25% of periods are throttled.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (cgroup stats), Splunk OpenTelemetry Collector.
• Ensure the following data sources are available: `sourcetype=docker:stats`, cgroup `cpu.stat`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect Docker stats via `docker stats --format '{{json .}}'` or read cgroup files directly (`/sys/fs/cgroup/cpu/docker/<id>/cpu.stat`). Monitor `throttled_time` and `nr_throttled`. Alert when >25% of periods are throttled.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="docker:stats"
| eval throttle_pct = round(nr_throttled / nr_periods * 100, 1)
| where throttle_pct > 25
| stats avg(throttle_pct) as avg_throttle by container_name
| sort -avg_throttle
```

Understanding this SPL

**Container CPU Throttling** — CPU throttling means the container is hitting its CPU limit and being artificially slowed. Causes latency spikes invisible to standard CPU utilization metrics.

Documented **Data sources**: `sourcetype=docker:stats`, cgroup `cpu.stat`. **App/TA** (typical add-on context): Custom scripted input (cgroup stats), Splunk OpenTelemetry Collector. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: docker:stats. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="docker:stats". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **throttle_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where throttle_pct > 25` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by container_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (throttle % over time), Table (container, throttle %, CPU limit), Bar chart.

## SPL

```spl
index=containers sourcetype="docker:stats"
| eval throttle_pct = round(nr_throttled / nr_periods * 100, 1)
| where throttle_pct > 25
| stats avg(throttle_pct) as avg_throttle by container_name
| sort -avg_throttle
```

## Visualization

Line chart (throttle % over time), Table (container, throttle %, CPU limit), Bar chart.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
