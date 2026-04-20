---
id: "8.5.10"
title: "Varnish Cache Hit Rate and Backend Health"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.5.10 · Varnish Cache Hit Rate and Backend Health

## Description

Cache efficiency and backend connection failures indicate Varnish health. Backend failures cause cache misses and user-facing errors.

## Value

Cache efficiency and backend connection failures indicate Varnish health. Backend failures cause cache misses and user-facing errors.

## Implementation

Run `varnishstat -j` via scripted input every minute. Parse MAIN.cache_hit, MAIN.cache_miss, MAIN.backend_fail, MAIN.backend_busy, MAIN.backend_unhealthy. Forward to Splunk via HEC. Alert when hit ratio drops below 80% or backend failures occur. Correlate backend_fail with backend health probes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (varnishstat, varnishlog).
• Ensure the following data sources are available: varnishstat JSON output.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Run `varnishstat -j` via scripted input every minute. Parse MAIN.cache_hit, MAIN.cache_miss, MAIN.backend_fail, MAIN.backend_busy, MAIN.backend_unhealthy. Forward to Splunk via HEC. Alert when hit ratio drops below 80% or backend failures occur. Correlate backend_fail with backend health probes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cache sourcetype="varnish:stats"
| eval hit_ratio=round(cache_hit/(cache_hit+cache_miss)*100,2)
| where hit_ratio < 80 OR backend_fail > 0 OR backend_busy > 0
| timechart span=5m avg(hit_ratio) as hit_pct, sum(backend_fail) as backend_failures by host
```

Understanding this SPL

**Varnish Cache Hit Rate and Backend Health** — Cache efficiency and backend connection failures indicate Varnish health. Backend failures cause cache misses and user-facing errors.

Documented **Data sources**: varnishstat JSON output. **App/TA** (typical add-on context): Custom scripted input (varnishstat, varnishlog). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cache; **sourcetype**: varnish:stats. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=cache, sourcetype="varnish:stats". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **hit_ratio** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where hit_ratio < 80 OR backend_fail > 0 OR backend_busy > 0` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (hit ratio %), Line chart (hit ratio and backend failures), Table (backend health status), Single value (backend failures).

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
index=cache sourcetype="varnish:stats"
| eval hit_ratio=round(cache_hit/(cache_hit+cache_miss)*100,2)
| where hit_ratio < 80 OR backend_fail > 0 OR backend_busy > 0
| timechart span=5m avg(hit_ratio) as hit_pct, sum(backend_fail) as backend_failures by host
```

## Visualization

Gauge (hit ratio %), Line chart (hit ratio and backend failures), Table (backend health status), Single value (backend failures).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
