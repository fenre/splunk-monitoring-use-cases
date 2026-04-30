<!-- AUTO-GENERATED from UC-5.14.5.json — DO NOT EDIT -->

---
id: "5.14.5"
title: "HAProxy Stick-Table and Rate-Limit Table Pressure"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.5 · HAProxy Stick-Table and Rate-Limit Table Pressure

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Security, Performance &middot; **Status:** Draft

*We watch haproxy stick-table and rate-limit table pressure and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Full stick-tables silently change traffic steering and security posture.

## Value

Keeps bot defenses and ACL stickiness predictable under attack.

## Implementation

Size `stick-table` with `size` and `expire` appropriate to QPS; alert on `table_full` class messages.

## SPL

```spl
index=proxy sourcetype="haproxy:syslog"
| regex _raw="(?i)(stick-table|gpc0|rate-limit|table_full)"
| stats count by host
| where count >= 1
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «HAProxy Stick-Table and Rate-Limit Table Pressure» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://docs.haproxy.org/2.8/configuration.html#stick-table)
