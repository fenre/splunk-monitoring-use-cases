<!-- AUTO-GENERATED from UC-7.1.73.json — DO NOT EDIT -->

---
id: "7.1.73"
title: "Cassandra Dropped Mutations and Read Timeouts"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.1.73 · Cassandra Dropped Mutations and Read Timeouts

## Description

Dropped mutations and read timeouts mean coordinators could not complete requests in time—often GC, overload, or replica unavailability. Treating log bursts as a first-class signal reduces mean time to detect compared to waiting for client dashboards.

## Value

Protects revenue-critical APIs backed by Cassandra from silent degradation when a subset of replicas is sick.

## Implementation

Normalize log levels; use `TRANSFORMS` to extract `coordinator`, `keyspace`, `table` when present. Ingest GC logs with `pause_time_ms` extracted for correlation searches (`join`). Suppress known load-test hosts. Page when event rate exceeds 10 per 5 minutes outside drills.

## SPL

```spl
index=database (sourcetype="cassandra:system" OR sourcetype="cassandra:gc")
| search "DroppedMutation" OR "ReadTimeout" OR "Operation timed out" OR (sourcetype="cassandra:gc" AND "GC pause" AND pause_time_ms>2000)
| rex field=_raw "(?<timeout_kind>Read|Write|CAS) timeout"
| bin _time span=5m
| stats count as events values(timeout_kind) as kinds by host, _time
| where events >= 10
```

## Visualization

Timeline (events), Table (host, kinds), Overlay GC pause max line.

## References

- [Apache Cassandra — Timeouts](https://cassandra.apache.org/doc/latest/cassandra/configuration/cass_yaml.html#request-timeout)
