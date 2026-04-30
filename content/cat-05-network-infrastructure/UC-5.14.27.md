<!-- AUTO-GENERATED from UC-5.14.27.json — DO NOT EDIT -->

---
id: "5.14.27"
title: "Squid ICAP and eCAP Adaptation Failures"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.27 · Squid ICAP and eCAP Adaptation Failures

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance, Security &middot; **Status:** Draft

*We watch squid icap and ecap adaptation failures and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Adaptation failures look like random web errors to users.

## Value

Protects both security coverage and productivity.

## Implementation

Tune service timeouts; scale scanners horizontally when counts rise.

## SPL

```spl
index=proxy sourcetype="squid:cache"
| regex _raw="(?i)(ICAP|ECAP).*(?:fail|error|timeout)"
| bin _time span=5m
| stats count by _time, host
| where count > 10
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Squid ICAP and eCAP Adaptation Failures» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](http://www.squid-cache.org/Doc/config/icap_service/)
