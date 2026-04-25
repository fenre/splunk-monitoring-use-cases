<!-- AUTO-GENERATED from UC-5.14.48.json — DO NOT EDIT -->

---
id: "5.14.48"
title: "Traefik Retry Middleware Activations"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.48 · Traefik Retry Middleware Activations

## Description

Retries mask flaky upstreams but add load when misconfigured.

## Value

Balances resilience versus thundering herds.

## Implementation

Enable retries only on idempotent routes; watch for retry amplification.

## SPL

```spl
index=proxy sourcetype="traefik:access"
| where RetryAttempts > 0
| stats sum(RetryAttempts) as retries by ServiceName
| sort - retries
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## References

- [Vendor documentation](https://doc.traefik.io/traefik/middlewares/http/retry/)
