<!-- AUTO-GENERATED from UC-1.1.51.json — DO NOT EDIT -->

---
id: "1.1.51"
title: "TCP Retransmission Rate Elevation"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.51 · TCP Retransmission Rate Elevation

## Description

Flags hosts where TCP retransmission segments in each five-minute bucket jump well above a host-specific rolling mean, a strong hint of loss, congestion, or driver issues on the path.

## Value

Rising retrans rates usually hit throughput and tail latency at the same time; catching the slope early shortens network and application war rooms.

## Implementation

Ingest retransmission counters (here `retransSegs` from a netstat-class feed) at a steady interval, bucket to five minutes, and compare each bucket to a rolling `streamstats` band so occasional spikes in healthy churn do not false-positive constantly.

## Detailed Implementation

Prerequisites
• Install `Splunk_TA_nix` and enable a netstat-style input, or build a `custom:tcp_retrans` script that prints cumulative `retransSegs` from `/proc/net/snmp`.

Step 1 — Configure data collection
If you use **counters**, either emit deltas in the script or precompute delta `retransSegs` per interval so the **sum** in Splunk is meaningful. Align collection interval with the `bin` span for stable math.

Step 2 — Create the search and alert

```spl
index=os sourcetype=netstat host=*
| bin _time span=5m
| stats sum(retransSegs) as retrans by host, _time
| streamstats window=100 avg(retrans) as baseline stdev(retrans) as stddev by host
| eval upper=baseline+(2*stddev)
| where retrans > upper
```

**Understanding this SPL** — Anomaly over time per host using `streamstats`; widen `window` on chatty sites so baselines are meaningful.


Step 3 — Validate
On the host, compare with `nstat -z` or `ss -i` and packet captures if needed; also check switch error counters on the same period.

Step 4 — Operationalize
Route to network and app owners together—pure host tuning rarely fixes a fabric issue.



## SPL

```spl
index=os sourcetype=netstat host=*
| bin _time span=5m
| stats sum(retransSegs) as retrans by host, _time
| streamstats window=100 avg(retrans) as baseline stdev(retrans) as stddev by host
| eval upper=baseline+(2*stddev)
| where retrans > upper
```

## Visualization

Timechart, Anomaly Chart

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
