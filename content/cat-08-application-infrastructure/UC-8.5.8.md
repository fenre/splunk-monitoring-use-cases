<!-- AUTO-GENERATED from UC-8.5.8.json — DO NOT EDIT -->

---
id: "8.5.8"
title: "Memcached Hit Ratio and Eviction Rate"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.5.8 · Memcached Hit Ratio and Eviction Rate

## Description

Cache hit ratio and eviction rate measure cache effectiveness and capacity pressure. Declining hit ratio or rising evictions indicate undersized cache or changing access patterns.

## Value

Cache hit ratio and eviction rate measure cache effectiveness and capacity pressure. Declining hit ratio or rising evictions indicate undersized cache or changing access patterns.

## Implementation

Run `echo stats | nc localhost 11211` (or memcached stats protocol) via scripted input every minute. Parse get_hits, get_misses, evictions, bytes, bytes_read, bytes_written. Forward to Splunk via HEC. Calculate hit ratio; alert when below 85%. Track eviction rate; alert when evictions per second exceed 5. Correlate with memory usage (limit_maxbytes).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (memcached stats).
• Ensure the following data sources are available: memcached stats command (get_hits, get_misses, evictions).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Run `echo stats | nc localhost 11211` (or memcached stats protocol) via scripted input every minute. Parse get_hits, get_misses, evictions, bytes, bytes_read, bytes_written. Forward to Splunk via HEC. Calculate hit ratio; alert when below 85%. Track eviction rate; alert when evictions per second exceed 5. Correlate with memory usage (limit_maxbytes).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cache sourcetype="memcached:stats"
| eval hit_ratio=round(get_hits/(get_hits+get_misses)*100,2)
| timechart span=5m avg(hit_ratio) as hit_pct, per_second(evictions) as eviction_rate by host
| where hit_pct < 85 OR eviction_rate > 5
```

Understanding this SPL

**Memcached Hit Ratio and Eviction Rate** — Cache hit ratio and eviction rate measure cache effectiveness and capacity pressure. Declining hit ratio or rising evictions indicate undersized cache or changing access patterns.

Documented **Data sources**: memcached stats command (get_hits, get_misses, evictions). **App/TA** (typical add-on context): Custom scripted input (memcached stats). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cache; **sourcetype**: memcached:stats. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=cache, sourcetype="memcached:stats". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **hit_ratio** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• Filters the current rows with `where hit_pct < 85 OR eviction_rate > 5` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare with `memcached` `stats` output for the same instance and a few raw events in Search.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (hit ratio %), Line chart (hit ratio and eviction rate over time), Single value (current eviction rate), Table (instances with low hit ratio).

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
index=cache sourcetype="memcached:stats"
| eval hit_ratio=round(get_hits/(get_hits+get_misses)*100,2)
| timechart span=5m avg(hit_ratio) as hit_pct, per_second(evictions) as eviction_rate by host
| where hit_pct < 85 OR eviction_rate > 5
```

## Visualization

Gauge (hit ratio %), Line chart (hit ratio and eviction rate over time), Single value (current eviction rate), Table (instances with low hit ratio).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
