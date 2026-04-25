<!-- AUTO-GENERATED from UC-8.2.25.json — DO NOT EDIT -->

---
id: "8.2.25"
title: "PHP-FPM Max Children Reached Events"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.2.25 · PHP-FPM Max Children Reached Events

## Description

When `max children reached` increments, new requests queue at the socket and clients see 502/504 from nginx or Apache.

## Value

Direct signal to raise `pm.max_children` or fix slow PHP before outages.

## Implementation

Poll frequently enough to catch spikes; combine with listen queue metrics from UC-8.2.11 patterns.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input polling `pm.status_path`.
• Ensure the following data sources are available: `index=php` `sourcetype=phpfpm:status` (`max children reached` counter).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Normalize the counter name at HEC if spaces break extraction.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=php sourcetype="phpfpm:status"
| eval mc=coalesce('max_children_reached', max_children_reached)
| where mc > 0
| sort - mc
| dedup host, pool
| table _time, host, pool, mc, active_processes, idle_processes
```

Understanding this SPL

**PHP-FPM Max Children Reached Events** — See the description and value fields in this use case JSON.

Documented **Data sources**: `index=php` `sourcetype=phpfpm:status` (`max children reached` counter). **App/TA**: Custom scripted input polling `pm.status_path`. Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

• Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.

Step 3 — Validate
Compare with JBoss, WebLogic, or Tomcat admin consoles, or `catalina` / server logs on the host, for the same window. Confirm hostnames and fields match the vendor UI.


Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Single value (pools in violation), table (pool detail), trend of `mc` delta..

## SPL

```spl
index=php sourcetype="phpfpm:status"
| eval mc=coalesce('max_children_reached', max_children_reached)
| where mc > 0
| sort - mc
| dedup host, pool
| table _time, host, pool, mc, active_processes, idle_processes
```

## Visualization

Single value (pools in violation), table (pool detail), trend of `mc` delta.

## References

- [PHP-FPM Status Page](https://www.php.net/manual/en/install.fpm.configuration.php)
