<!-- AUTO-GENERATED from UC-8.1.71.json — DO NOT EDIT -->

---
id: "8.1.71"
title: "Memcached Network Bytes Read and Written Throughput"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.1.71 · Memcached Network Bytes Read and Written Throughput

## Description

Network throughput approaching NIC limits causes latency jitter even if CPU looks fine. Byte counters from memcached complement switch telemetry for end-to-end cache performance.

## Value

Informs NIC upgrades, placement, and batching changes before packet drops appear only at the switch.

## Implementation

Adjust bin span to match poll interval when computing mbps. For cumulative counters, use consistent `delta` windows. Validate 10GbE vs 25GbE host limits in alert thresholds.

## SPL

```spl
index=infrastructure sourcetype="memcached:stats"
| eval br=tonumber(bytes_read)
| eval bw=tonumber(bytes_written)
| bin _time span=5m
| stats latest(br) as bread latest(bw) as bwrite by host, _time
| streamstats window=2 global=f delta(bread) as read_bps delta(bwrite) as write_bps by host
| eval read_mbps=round(read_bps/300/1048576,2)
| eval write_mbps=round(write_bps/300/1048576,2)
| where read_mbps > 800 OR write_mbps > 800
```

## Visualization

Area chart (read_mbps, write_mbps), Table (host).

## References

- [Memcached wiki — tuning](https://github.com/memcached/memcached/wiki/Performance)
