<!-- AUTO-GENERATED from UC-5.14.33.json — DO NOT EDIT -->

---
id: "5.14.33"
title: "Squid SSL Bump Peek-and-Splice Decision Audit"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.33 · Squid SSL Bump Peek-and-Splice Decision Audit

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Security, Compliance &middot; **Status:** Draft

*We watch squid ssl bump peek-and-splice decision audit and catch issues early, before they turn into outages for the people who rely on the network.*

---

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

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Squid SSL Bump Peek-and-Splice Decision Audit» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](http://www.squid-cache.org/Doc/config/ssl_bump/)
