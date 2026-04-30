<!-- AUTO-GENERATED from UC-5.14.7.json — DO NOT EDIT -->

---
id: "5.14.7"
title: "HAProxy ACL-Based Traffic Routing Audit"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.7 · HAProxy ACL-Based Traffic Routing Audit

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Audit, Security &middot; **Status:** Draft

*We watch haproxy acl-based traffic routing audit and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Routing audits support tenant isolation and forensic reconstruction.

## Value

Demonstrates control effectiveness to risk teams without packet capture.

## Implementation

Add stable rule identifiers for regulated splits; scrub URIs with PII.

## SPL

```spl
index=proxy sourcetype="haproxy:http"
| stats count by fe_name, be_name
| sort - count
| head 40
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «HAProxy ACL-Based Traffic Routing Audit» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://docs.haproxy.org/2.8/configuration.html#7)
