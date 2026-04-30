<!-- AUTO-GENERATED from UC-5.14.26.json — DO NOT EDIT -->

---
id: "5.14.26"
title: "Squid CONNECT Tunnel Duration and Volume"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.26 · Squid CONNECT Tunnel Duration and Volume

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Security, Performance &middot; **Status:** Draft

*We watch squid connect tunnel duration and volume and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

CONNECT dominates bandwidth on many enterprise proxies.

## Value

Supports fair sharing and DLP placement decisions.

## Implementation

Ensure log format includes duration; never log decrypted payload. Comply with local interception law.

## SPL

```spl
index=proxy sourcetype="squid:access"
| where request_method=="CONNECT"
| eval dur_ms=tonumber(time_taken_ms)
| eval bytes=tonumber(bytes_sent)+tonumber(bytes_received)
| timechart span=5m perc95(dur_ms) as p95_tunnel_ms sum(bytes) as tunnel_bytes
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Squid CONNECT Tunnel Duration and Volume» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](http://www.squid-cache.org/Doc/config/access_log/)
