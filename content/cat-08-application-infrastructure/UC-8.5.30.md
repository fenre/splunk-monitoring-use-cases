<!-- AUTO-GENERATED from UC-8.5.30.json — DO NOT EDIT -->

---
id: "8.5.30"
title: "ActiveMQ KahaDB Journal Disk Pressure Before Broker Stall"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.5.30 · ActiveMQ KahaDB Journal Disk Pressure Before Broker Stall

## Description

KahaDB writes sequential journal files on disk; when the volume fills or the broker hits `StoreLimit`, producers block and messages stop draining. Combining filesystem-level IO errors from `activemq.log` with `StorePercentUsage` for KahaDB-configured brokers catches the failure mode before complete flow shutdown.

## Value

Prevents catastrophic messaging outages during storage sprawl or mis-sized data volumes by alerting while the broker can still shed load or expand disk.

## Implementation

Prefer tagging `persistence_adapter` or `PersistenceAdapterName` at ingest; when null, store-pressure alerts still fire—exclude confirmed JDBC-only brokers via a lookup. Monitor the partition that hosts `activemq_data` at the OS layer in parallel. Set `store_pct` threshold just below your operational runbook limit (often 80–90%).

## SPL

```spl
index=messaging (sourcetype="activemq:log" OR sourcetype="activemq:broker") earliest=-24h
| eval store_pct=coalesce(StorePercentUsage, round(store_used*100/nullif(store_limit,0),1))
| eval journal_signal=if(sourcetype="activemq:log" AND match(_raw, "(?i)(No space left on device|IOException.*(journal|kahadb)|Persistence store.*(full|limit)|KahaDB.*(ERROR|failed))"), 1, 0)
| eval is_jdbc=if(like(lower(coalesce(persistence_adapter, PersistenceAdapterName, "")), "%jdbc%"), 1, 0)
| where journal_signal==1 OR (sourcetype="activemq:broker" AND is_jdbc==0 AND store_pct>=85)
| table _time, host, sourcetype, broker_name, store_pct, journal_signal, is_jdbc, _raw
```

## Visualization

Single value (max store %), timeline of log matches, table (broker, store_pct, sample log line).

## References

- [Apache ActiveMQ — KahaDB](https://activemq.apache.org/kahadb)
- [Apache ActiveMQ — JMX reference (Broker MBeans)](https://activemq.apache.org/jmx.html)
