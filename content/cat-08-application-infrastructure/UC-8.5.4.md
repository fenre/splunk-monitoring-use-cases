<!-- AUTO-GENERATED from UC-8.5.4.json — DO NOT EDIT -->

---
id: "8.5.4"
title: "Connection Count Monitoring"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.5.4 · Connection Count Monitoring

## Description

Approaching connection limits causes client rejections. Monitoring enables proactive limit adjustment.

## Value

Approaching connection limits causes client rejections. Monitoring enables proactive limit adjustment.

## Implementation

Poll connection metrics every minute. Track connected clients vs maxclients setting. Alert at 80% threshold. Monitor rejected connections counter for actual connection refusals.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input.
• Ensure the following data sources are available: Redis INFO clients, Memcached stats.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll connection metrics every minute. Track connected clients vs maxclients setting. Alert at 80% threshold. Monitor rejected connections counter for actual connection refusals.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cache sourcetype="redis:info"
| timechart span=5m max(connected_clients) as clients, max(maxclients) as limit by host
| eval pct=round(clients/limit*100,1)
| where pct > 80
```

Understanding this SPL

**Connection Count Monitoring** — Approaching connection limits causes client rejections. Monitoring enables proactive limit adjustment.

Documented **Data sources**: Redis INFO clients, Memcached stats. **App/TA** (typical add-on context): Custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cache; **sourcetype**: redis:info. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=cache, sourcetype="redis:info". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• `eval` defines or adjusts **pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where pct > 80` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare with `redis-cli INFO` (and slowlog if relevant) on the same instance and time window.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (connections over time), Gauge (% of max), Single value (current connections).

## SPL

```spl
index=cache sourcetype="redis:info"
| timechart span=5m max(connected_clients) as clients, max(maxclients) as limit by host
| eval pct=round(clients/limit*100,1)
| where pct > 80
```

## Visualization

Line chart (connections over time), Gauge (% of max), Single value (current connections).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
