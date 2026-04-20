---
id: "3.1.13"
title: "Container Restart Loop Detection"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.1.13 · Container Restart Loop Detection

## Description

Rapid start/die cycles burn CPU and obscure root cause; detecting loops early isolates bad images or bad configs before cascading failures.

## Value

Rapid start/die cycles burn CPU and obscure root cause; detecting loops early isolates bad images or bad configs before cascading failures.

## Implementation

Track paired start/die bursts per container in sliding windows. Alert when >3 restart cycles in 15 minutes. Enrich with `exitCode` from die events.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Connect for Docker.
• Ensure the following data sources are available: `sourcetype=docker:events`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Track paired start/die bursts per container in sliding windows. Alert when >3 restart cycles in 15 minutes. Enrich with `exitCode` from die events.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="docker:events" action="die" OR action="start"
| bin _time span=5m
| stats dc(action) as actions, count by _time, container_name, host
| where actions>=2 AND count>=6
| sort -count
```

Understanding this SPL

**Container Restart Loop Detection** — Rapid start/die cycles burn CPU and obscure root cause; detecting loops early isolates bad images or bad configs before cascading failures.

Documented **Data sources**: `sourcetype=docker:events`. **App/TA** (typical add-on context): Splunk Connect for Docker. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: docker:events. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="docker:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by _time, container_name, host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where actions>=2 AND count>=6` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (start/die), Table (container, cycles, host), Single value (looping containers).

## SPL

```spl
index=containers sourcetype="docker:events" action="die" OR action="start"
| bin _time span=5m
| stats dc(action) as actions, count by _time, container_name, host
| where actions>=2 AND count>=6
| sort -count
```

## Visualization

Timeline (start/die), Table (container, cycles, host), Single value (looping containers).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
