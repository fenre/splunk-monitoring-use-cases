<!-- AUTO-GENERATED from UC-5.14.33.json — DO NOT EDIT -->

---
id: "5.14.33"
title: "Squid SSL Bump Peek-and-Splice Decision Audit"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.33 · Squid SSL Bump Peek-and-Splice Decision Audit

## Description

Regulators expect proof of what is inspected versus passed through.

## Value

Reduces legal and privacy risk through transparency.

## Implementation

Restrict index permissions; follow jurisdiction on TLS inspection. Redact sensitive domains in exports.

## SPL

```spl
index=proxy sourcetype="squid:access"
| where match(_raw, "(?i)bump|splice|peek|SSL_")
| stats count by ssl_bump_action, dst_domain
| sort - count
| head 50
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## References

- [Vendor documentation](http://www.squid-cache.org/Doc/config/ssl_bump/)
