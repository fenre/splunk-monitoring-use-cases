<!-- AUTO-GENERATED from UC-2.9.2.json — DO NOT EDIT -->

---
id: "2.9.2"
title: "OpenStack Neutron Agent Liveness and RPC Failures"
criticality: "critical"
splunkPillar: "IT Operations"
---

# UC-2.9.2 · OpenStack Neutron Agent Liveness and RPC Failures

## Description

Down L3/DHCP/metadata agents break tenant connectivity even when Nova looks healthy. Early RPC and heartbeat anomalies predict partial network partitions.

## Value

Avoids tenant-visible outages and shortens bridge between cloud and network teams.

## Implementation

Normalize agent heartbeats to epoch. Page when stale beyond SLA. Join with RabbitMQ queue depth if available.

## SPL

```spl
index=openstack sourcetype="openstack:neutron" earliest=-2h
| eval hb_age=now()-tonumber(coalesce(last_heartbeat_epoch, heartbeat_ts))
| where hb_age>120 OR match(lower(_raw), "(?i)rpc.?timeout|amqp|unavailable|agent.*down")
| stats latest(hb_age) as stale_sec by agent_type, host, binary
```

## Visualization

Timeline agent health; table worst hosts; overlay AMQP errors.

## References

- [OpenStack Neutron](https://docs.openstack.org/neutron/latest/)
