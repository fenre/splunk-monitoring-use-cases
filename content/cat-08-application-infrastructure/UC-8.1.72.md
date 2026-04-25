<!-- AUTO-GENERATED from UC-8.1.72.json — DO NOT EDIT -->

---
id: "8.1.72"
title: "Memcached SASL Authentication Failure Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-8.1.72 · Memcached SASL Authentication Failure Detection

## Description

Repeated SASL failures may indicate credential rotation mistakes, offline LDAP, or brute-force attempts against cache endpoints exposed beyond trust zones.

## Value

Protects in-memory data stores that sometimes hold serialized sessions or PII from unauthorized access.

## Implementation

Enable SASL (`-S`) in controlled environments; forward logs with `chmod` restrictions. If only `auth_errors` counter exists, delta it like other counters. Correlate with firewall and VPC flow logs for client IPs.

## SPL

```spl
index=infrastructure (sourcetype="memcached:stats" OR sourcetype="memcached:log")
| search auth_errors>0 OR "authentication failed" OR "SASL" AND ("fail" OR "error")
| eval ae=tonumber(auth_errors)
| bin _time span=15m
| stats sum(ae) as auth_errs count as log_hits by host, _time
| where auth_errs > 5 OR log_hits > 10
```

## Visualization

Timeline (auth_errs), Table (host, log sample).

## References

- [Memcached — SASL](https://github.com/memcached/memcached/wiki/SASLHowto)
