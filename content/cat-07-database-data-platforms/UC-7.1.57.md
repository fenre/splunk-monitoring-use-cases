<!-- AUTO-GENERATED from UC-7.1.57.json — DO NOT EDIT -->

---
id: "7.1.57"
title: "ClickHouse ZooKeeper Session Failures Correlation"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.1.57 · ClickHouse ZooKeeper Session Failures Correlation

## Description

ClickHouse replication and DDL coordination depend on stable ZooKeeper sessions; repeated session or coordination errors predict readonly tables, stuck merges, and DDL failures. Surfacing bursts by host speeds joint triage with the ZooKeeper team.

## Value

Reduces prolonged replication lag and prevents emergency failover when metadata coordination degrades.

## Implementation

Set `inputs.conf` `monitor://` or container sidecar to ingest ClickHouse logs with `DATETIME_CONFIG` matching ClickHouse log format. Tag `host` as the ClickHouse server. Create a lookup mapping known maintenance. Pair with `zookeeper:mntr` from the ZK cluster in a separate index for joint dashboards.

## SPL

```spl
index=database sourcetype="clickhouse:server_log"
| search "ZooKeeper" AND ("Session expired" OR "Connection loss" OR "Coordination::Exception" OR "Cannot allocate block number")
| rex field=_raw "Code:\s+(?<zk_code>\d+)\.\s+(?<zk_msg>.+)"
| bin _time span=5m
| stats count as events values(zk_msg) as msgs by host, _time
| where events >= 5
```

## Visualization

Timeline (events), Table (host, msgs), Top hosts bar chart.

## References

- [ClickHouse — ZooKeeper configuration](https://clickhouse.com/docs/en/operations/server-configuration-parameters/settings#server-settings_zookeeper)
