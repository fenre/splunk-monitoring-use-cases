<!-- AUTO-GENERATED from UC-5.14.23.json — DO NOT EDIT -->

---
id: "5.14.23"
title: "Squid Cache Hit Ratio by Request Method"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.23 · Squid Cache Hit Ratio by Request Method

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Status:** Draft

*We watch squid cache hit ratio by request method and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

CONNECT-heavy networks behave differently in hit ratio than browser traffic.

## Value

Guides peering and SSL bump policies with evidence.

## Implementation

Use `cache_access_log` with Splunk-friendly format; map `%>hs` status and `%rm` method in `props.conf`.

## SPL

```spl
index=proxy sourcetype="squid:access"
| eval meth=coalesce(request_method, cs_method)
| eval is_hit=if(match(code, "TCP_(HIT|MEM_HIT|REFRESH_HIT)"),1,0)
| stats sum(is_hit) as hits count as total by meth
| eval hit_pct=round(100*hits/total,2)
| table meth, hits, total, hit_pct
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Squid Cache Hit Ratio by Request Method» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](http://www.squid-cache.org/Doc/config/access_log/)
