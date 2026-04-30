<!-- AUTO-GENERATED from UC-5.14.21.json — DO NOT EDIT -->

---
id: "5.14.21"
title: "Varnish VCL Reload and Compilation Errors"
status: "draft"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.14.21 · Varnish VCL Reload and Compilation Errors

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Change, Fault &middot; **Status:** Draft

*We watch varnish vcl reload and compilation errors and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Compile errors during reloads can strand traffic on old VCL or stop updates.

## Value

Protects release pipelines that touch edge logic.

## Implementation

Page immediately on compile failure in production paths.

## SPL

```spl
index=proxy sourcetype="varnish:log"
| regex _raw="(?i)(VCL compilation failed|syntax error in.*vcl)"
| stats count by host, _raw
| where count >= 1
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Varnish VCL Reload and Compilation Errors» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/users-guide/vcl-separate.html)
