<!-- AUTO-GENERATED from UC-8.4.17.json — DO NOT EDIT -->

---
id: "8.4.17"
title: "PHP-FPM Active Worker Saturation Versus max_children"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.4.17 · PHP-FPM Active Worker Saturation Versus max_children

## Description

Sustained high `active_processes/max_children` leaves no burst capacity; the next traffic spike hits the listen queue.

## Value

Drives right-sizing of `pm.max_children` and horizontal scaling.

## Implementation

Ensure `max_children` field exists in JSON; if missing, join with static KV lookup of pool config.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input.
• Ensure the following data sources are available: `index=php` `sourcetype=phpfpm:status`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
If `max_children` is absent from status JSON, add it via lookup from config management.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=php sourcetype="phpfpm:status"
| eval util=round(100*active_processes/max_children,1)
| where util > 85
| timechart span=5m max(util) as util_pct by pool, host
```

Understanding this SPL

**PHP-FPM Active Worker Saturation Versus max_children** — See the description and value fields in this use case JSON.

Documented **Data sources**: `index=php` `sourcetype=phpfpm:status`. **App/TA**: Custom scripted input. Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

• Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.

Step 3 — Validate
Compare with the PHP-FPM pool status page (often `?full`) and a matching line from FPM or web access logs on the host.


Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Gauge per pool, line chart, overlay slow_requests..

## SPL

```spl
index=php sourcetype="phpfpm:status"
| eval util=round(100*active_processes/max_children,1)
| where util > 85
| timechart span=5m max(util) as util_pct by pool, host
```

## Visualization

Gauge per pool, line chart, overlay slow_requests.

## References

- [PHP-FPM Status Page](https://www.php.net/manual/en/install.fpm.configuration.php)
