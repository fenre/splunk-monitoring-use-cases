<!-- AUTO-GENERATED from UC-7.3.20.json — DO NOT EDIT -->

---
id: "7.3.20"
title: "MySQL Aborted Connection and Handshake Failure Spike"
criticality: "high"
splunkPillar: "Security"
---

# UC-7.3.20 · MySQL Aborted Connection and Handshake Failure Spike

## Description

Sudden increases in aborted connections or access denied errors point to credential attacks, TLS mismatches, or pool misconfiguration—common MySQL/MariaDB operational alerts.

## Value

Supports SOC detection and helps DBAs separate attacks from application deploy mistakes quickly.

## Implementation

Prefer structured error log with connection id and src_ip. If only counters exist, use delta(Aborted_connects) per poll. Correlate with firewall and WAF. Suppress known scanner IPs via lookup.

## SPL

```spl
index=database (sourcetype="mysql:error" OR sourcetype="mysql:log")
| search "Aborted connection" OR "Access denied for user"
| bin _time span=15m
| stats count as events dc(host) as targets by user, src_ip, _time
| where events > 100
```

## Visualization

Timeline (events), Table (user, src_ip), Top values (error subtypes).

## References

- [MySQL Server Error Log Reference](https://dev.mysql.com/doc/refman/8.0/en/error-log.html)
