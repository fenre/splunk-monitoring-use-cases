<!-- AUTO-GENERATED from UC-5.14.49.json — DO NOT EDIT -->

---
id: "5.14.49"
title: "Traefik Mutual TLS Client Certificate Errors"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.49 · Traefik Mutual TLS Client Certificate Errors

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Security, Audit &middot; **Status:** Draft

*We watch traefik mutual tls client certificate errors and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

mTLS ecosystems break silently when CAs rotate.

## Value

Keeps partner B2B APIs reliable.

## Implementation

Configure `tls.options.clientAuthType`; never log private keys or full chains in access logs.

## SPL

```spl
index=proxy sourcetype="traefik:access"
| where DownstreamStatus==401 OR match(_raw, "(?i)(unknown ca|certificate required|handshake failure)")
| stats count by RouterName, ClientAddr
| where count > 15
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Traefik Mutual TLS Client Certificate Errors» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://doc.traefik.io/traefik/https/tls/)
