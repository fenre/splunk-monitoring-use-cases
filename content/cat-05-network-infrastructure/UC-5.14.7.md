<!-- AUTO-GENERATED from UC-5.14.7.json — DO NOT EDIT -->

---
id: "5.14.7"
title: "HAProxy ACL-Based Traffic Routing Audit"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.7 · HAProxy ACL-Based Traffic Routing Audit

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

## References

- [Vendor documentation](https://docs.haproxy.org/2.8/configuration.html#7)
