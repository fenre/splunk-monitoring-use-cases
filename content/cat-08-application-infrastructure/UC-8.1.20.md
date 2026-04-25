<!-- AUTO-GENERATED from UC-8.1.20.json — DO NOT EDIT -->

---
id: "8.1.20"
title: "PHP-FPM Slow Request Counter Increases"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.1.20 · PHP-FPM Slow Request Counter Increases

## Description

The `slow_requests` counter increments when requests exceed `request_slowlog_timeout`. Sustained increases pinpoint slow PHP code, database calls, or external APIs.

## Value

Surfaces PHP endpoints that breach slow thresholds so you can tune code or pool settings before queues explode.

## Implementation

Expose `pm.status_path` over loopback, poll JSON every minute, and parse `slow_requests`, `active processes`, and `idle processes`. Alert on delta spikes, not one-off counter values.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input or HEC (PHP-FPM `pm.status_path`); Add On for Traefik Proxy patterns optional for edge logs.
• Ensure the following data sources are available: `index=php` `sourcetype=phpfpm:status` JSON from `pm.status_path`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `/status?json` on each pool; ensure `slow_requests` is extracted; use `delta` on the counter for alert logic.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=php sourcetype="phpfpm:status"
| sort 0 _time
| delta slow_requests as slow_delta
| where slow_delta > 10
| table _time, host, pool, slow_requests, slow_delta
```

Understanding this SPL

**PHP-FPM Slow Request Counter Increases** — See the description and value fields in this use case JSON.

Documented **Data sources**: `index=php` `sourcetype=phpfpm:status` JSON from `pm.status_path`. **App/TA**: Custom scripted input or HEC (PHP-FPM `pm.status_path`); Add On for Traefik Proxy patterns optional for edge logs. Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

• Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.

Step 3 — Validate
Compare with web server access logs on disk (Apache, NGINX, or W3C) for the same time range, or tail the same sourcetype in Search, to confirm status codes, URIs, and counts.


Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Line chart (`slow_requests` counter), bar chart (slow_delta per pool), correlation with upstream database latency..

## SPL

```spl
index=php sourcetype="phpfpm:status"
| sort 0 _time
| delta slow_requests as slow_delta
| where slow_delta > 10
| table _time, host, pool, slow_requests, slow_delta
```

## Visualization

Line chart (`slow_requests` counter), bar chart (slow_delta per pool), correlation with upstream database latency.

## References

- [PHP-FPM Status Page](https://www.php.net/manual/en/install.fpm.configuration.php)
