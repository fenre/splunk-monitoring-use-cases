<!-- AUTO-GENERATED from UC-5.14.3.json — DO NOT EDIT -->

---
id: "5.14.3"
title: "HAProxy Queue Time vs Response Time Saturation Ratio"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.3 · HAProxy Queue Time vs Response Time Saturation Ratio

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity &middot; **Status:** Draft

*We watch haproxy queue time vs response time saturation ratio and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Queue-heavy latency means the proxy or servers cannot dequeue fast enough even if app CPU is fine.

## Value

Directs tuning at maxconn, threads, or origin scale instead of micro-optimizing code alone.

## Implementation

Confirm millisecond units in `props.conf`. Tune ratio threshold per API; pair with server `cur_sess`.

## SPL

```spl
index=proxy sourcetype="haproxy:http"
| eval Tw=tonumber(Wait), Tr=tonumber(Response)
| eval q_ratio=if(Tr>0, round(Tw/Tr,3), null())
| where Tw > 50 AND q_ratio > 0.5
| timechart span=5m perc95(q_ratio) by backend
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «HAProxy Queue Time vs Response Time Saturation Ratio» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://www.haproxy.com/blog/the-four-golden-signals-for-haproxy/)
