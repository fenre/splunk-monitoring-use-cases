<!-- AUTO-GENERATED from UC-8.4.18.json — DO NOT EDIT -->

---
id: "8.4.18"
title: "Squid Cache Storage and Swap Utilization"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.4.18 · Squid Cache Storage and Swap Utilization

## Description

Disk cache exhaustion forces evictions and raises origin load; swap metrics predict hardware upgrades.

## Value

Avoids surprise origin floods when cache disks fill.

## Implementation

Expose `mgr:info` or SNMP counters via scripted input; normalize KB fields at ingest.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: SNMP polling of `cacheCurrentDiskUsage`, `cacheCurrentStoreSwapSize`, or scripted `squidclient mgr:info`.
• Ensure the following data sources are available: Squid `store_io` metrics (`sourcetype=squid:snmp` or `squid:info`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Field names must match your scripted parser; adjust `current_swap_kb` mapping.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=proxy sourcetype="squid:info"
| eval swap_pct=if(max_swap_kb>0, round(100*current_swap_kb/max_swap_kb,1), null())
| where swap_pct > 85
| table _time, host, swap_pct, current_swap_kb, max_swap_kb
```

Understanding this SPL

**Squid Cache Storage and Swap Utilization** — See the description and value fields in this use case JSON.

Documented **Data sources**: Squid `store_io` metrics (`sourcetype=squid:snmp` or `squid:info`). **App/TA**: SNMP polling of `cacheCurrentDiskUsage`, `cacheCurrentStoreSwapSize`, or scripted `squidclient mgr:info`. Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

• Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.

Step 3 — Validate
Compare with the API gateway or mesh admin (Kong, Apigee, AWS API Gateway, etc.) and a raw log tail for the same time range.


Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Line chart (swap_pct), single value, forecast with `predict` optional..

## SPL

```spl
index=proxy sourcetype="squid:info"
| eval swap_pct=if(max_swap_kb>0, round(100*current_swap_kb/max_swap_kb,1), null())
| where swap_pct > 85
| table _time, host, swap_pct, current_swap_kb, max_swap_kb
```

## Visualization

Line chart (swap_pct), single value, forecast with `predict` optional.

## References

- [Squid Configuration Manual — Access Log](http://www.squid-cache.org/Doc/config/access_log/)
