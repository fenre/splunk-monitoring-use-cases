---
id: "8.5.1"
title: "Cache Hit/Miss Ratio"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.5.1 · Cache Hit/Miss Ratio

## Description

Cache hit ratio directly measures cache effectiveness. Declining ratio means more backend load and higher latency.

## Value

Cache hit ratio directly measures cache effectiveness. Declining ratio means more backend load and higher latency.

## Implementation

Run `redis-cli INFO` via scripted input every minute. Parse keyspace_hits and keyspace_misses. Calculate hit ratio. Alert when ratio drops below 90%. Correlate with application deployment events (new code may change access patterns).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (`redis-cli INFO`).
• Ensure the following data sources are available: Redis INFO stats, Memcached stats, Varnish stats.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Run `redis-cli INFO` via scripted input every minute. Parse keyspace_hits and keyspace_misses. Calculate hit ratio. Alert when ratio drops below 90%. Correlate with application deployment events (new code may change access patterns).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cache sourcetype="redis:info"
| eval hit_ratio=round(keyspace_hits/(keyspace_hits+keyspace_misses)*100,2)
| timechart span=5m avg(hit_ratio) as cache_hit_pct by host
| where cache_hit_pct < 90
```

Understanding this SPL

**Cache Hit/Miss Ratio** — Cache hit ratio directly measures cache effectiveness. Declining ratio means more backend load and higher latency.

Documented **Data sources**: Redis INFO stats, Memcached stats, Varnish stats. **App/TA** (typical add-on context): Custom scripted input (`redis-cli INFO`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cache; **sourcetype**: redis:info. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=cache, sourcetype="redis:info". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **hit_ratio** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• Filters the current rows with `where cache_hit_pct < 90` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (hit ratio %), Line chart (hit ratio over time), Single value (current hit ratio).

Scripted input (generic example)
This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]
interval = 300
sourcetype = your_sourcetype
index = main
disabled = 0
```

The script should print one event per line (e.g. key=value). Example minimal script (bash):

```bash
#!/usr/bin/env bash
# Output metrics or events, one per line
echo "metric=value timestamp=$(date +%s)"
```

For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=cache sourcetype="redis:info"
| eval hit_ratio=round(keyspace_hits/(keyspace_hits+keyspace_misses)*100,2)
| timechart span=5m avg(hit_ratio) as cache_hit_pct by host
| where cache_hit_pct < 90
```

## Visualization

Gauge (hit ratio %), Line chart (hit ratio over time), Single value (current hit ratio).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
