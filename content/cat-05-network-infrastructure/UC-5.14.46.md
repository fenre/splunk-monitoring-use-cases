<!-- AUTO-GENERATED from UC-5.14.46.json — DO NOT EDIT -->

---
id: "5.14.46"
title: "Traefik ACME / Let's Encrypt Renewal Errors"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.46 · Traefik ACME / Let's Encrypt Renewal Errors

## Description

TLS expiry outages are preventable with log monitoring.

## Value

Protects customer trust on public edges.

## Implementation

Prefer DNS challenge in complex networks; monitor cert NotAfter via separate exporter.

## SPL

```spl
index=proxy sourcetype="traefik:log"
| regex _raw="(?i)(acme|letsencrypt).*(error|fail|unable)"
| stats latest(_time) as last_seen count by _raw
| sort - count
| head 20
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## References

- [Vendor documentation](https://doc.traefik.io/traefik/https/acme/)
