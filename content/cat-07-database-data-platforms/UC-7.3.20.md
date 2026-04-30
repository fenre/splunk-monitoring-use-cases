<!-- AUTO-GENERATED from UC-7.3.20.json — DO NOT EDIT -->

---
id: "7.3.20"
title: "MySQL Aborted Connection and Handshake Failure Spike"
status: "draft"
criticality: "high"
splunkPillar: "Security"
---

# UC-7.3.20 · MySQL Aborted Connection and Handshake Failure Spike

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security &middot; **Status:** Draft

*We watch how many sessions and pooled connections the fleet uses so we can scale or fix apps before the database hits its connection limits.*

---

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

## Known False Positives

Planned changes, load tests, and vendor maintenance in the data platform can move the same metrics this search uses; we compare to baselines, change records, and on-call context before we treat a hit as a production incident.

## References

- [MySQL Server Error Log Reference](https://dev.mysql.com/doc/refman/8.0/en/error-log.html)
