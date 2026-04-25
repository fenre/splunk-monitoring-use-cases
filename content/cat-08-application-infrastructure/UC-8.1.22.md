<!-- AUTO-GENERATED from UC-8.1.22.json — DO NOT EDIT -->

---
id: "8.1.22"
title: "Varnish Worker Thread Queue Backlog"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.1.22 · Varnish Worker Thread Queue Backlog

## Description

`n_wrk_queue` grows when worker threads cannot dequeue requests fast enough. Backlog leads to elevated latency and client timeouts.

## Value

Detects thread starvation before Varnish stops keeping up with traffic spikes.

## Implementation

Poll `varnishstat -j` every 30–60s; flatten `MAIN.n_wrk_queue` to `n_wrk_queue`. Correlate with `cache_hit` drops and backend latency.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (`varnishstat -j`).
• Ensure the following data sources are available: `index=cache` `sourcetype=varnish:stats` (`MAIN.n_wrk_queue` / `n_wrk_queue`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ensure JSON stats include worker queue; confirm field name matches your extractor (`n_wrk_queue`).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cache sourcetype="varnish:stats"
| timechart span=1m max(n_wrk_queue) as worker_queue_depth by host
| where worker_queue_depth > 50
```

Understanding this SPL

**Varnish Worker Thread Queue Backlog** — See the description and value fields in this use case JSON.

Documented **Data sources**: `index=cache` `sourcetype=varnish:stats` (`MAIN.n_wrk_queue` / `n_wrk_queue`). **App/TA**: Custom scripted input (`varnishstat -j`). Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

• Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.

Step 3 — Validate
Compare with web server access logs on disk (Apache, NGINX, or W3C) for the same time range, or tail the same sourcetype in Search, to confirm status codes, URIs, and counts.


Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Line chart (queue depth), overlay with `n_wrk_busy`, table (peaks by POP)..

## SPL

```spl
index=cache sourcetype="varnish:stats"
| timechart span=1m max(n_wrk_queue) as worker_queue_depth by host
| where worker_queue_depth > 50
```

## Visualization

Line chart (queue depth), overlay with `n_wrk_busy`, table (peaks by POP).

## References

- [varnishstat — Varnish reference](https://varnish-cache.org/docs/trunk/reference/varnishstat.html)
