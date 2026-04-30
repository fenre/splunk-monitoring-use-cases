<!-- AUTO-GENERATED from UC-5.14.4.json — DO NOT EDIT -->

---
id: "5.14.4"
title: "HAProxy SSL/TLS Handshake Failure Rate"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.4 · HAProxy SSL/TLS Handshake Failure Rate

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Security, Availability &middot; **Status:** Draft

*We watch haproxy ssl/tls handshake failure rate and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

TLS failures block whole cohorts of clients and often precede major incidents after renewals.

## Value

Protects partner and mobile traffic that is sensitive to cipher and chain changes.

## Implementation

Enable sufficient TLS logging without secrets. Join failure spikes with certificate inventory expiry.

## SPL

```spl
index=proxy sourcetype="haproxy:http"
| regex _raw="(?i)(SSL handshake failure|verify error|alert unknown ca|alert certificate)"
| bin _time span=5m
| stats count by frontend, _time
| where count > 20
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «HAProxy SSL/TLS Handshake Failure Rate» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://docs.haproxy.org/2.8/configuration.html#5.1)
