<!-- AUTO-GENERATED from UC-5.14.2.json — DO NOT EDIT -->

---
id: "5.14.2"
title: "HAProxy Connection Retry and Redispatch Volume"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.2 · HAProxy Connection Retry and Redispatch Volume

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Resilience, Performance &middot; **Status:** Draft

*We watch haproxy connection retry and redispatch volume and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Retries absorb brief faults but high volume masks systemic overload or brownouts.

## Value

Surfaces upstream instability that averages hide until SLAs break.

## Implementation

Extend `log-format` to include retry/redispatch counters; validate with `show stat`. Baseline per service.

## SPL

```spl
index=proxy sourcetype="haproxy:http"
| regex field=_raw "(?i)retry=(?<retry>\d+)"
| stats sum(retry) as retries by backend, server
| where retries > 100
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «HAProxy Connection Retry and Redispatch Volume» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://docs.haproxy.org/2.8/configuration.html#log-format)
