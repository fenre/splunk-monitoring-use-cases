<!-- AUTO-GENERATED from UC-1.1.61.json — DO NOT EDIT -->

---
id: "1.1.61"
title: "TCP TIME_WAIT Accumulation"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.61 · TCP TIME_WAIT Accumulation

## Description

Counts how many socket rows in each snapshot are in **TIME_WAIT**, then alerts when a host carries more than about thirty-two thousand of them—common when ephemeral ports or aggressive close patterns go wrong under load.

## Value

A giant TIME_WAIT pile often sits next to “cannot assign requested address” or connect failures; catching it in Splunk spares you from guessing in `ss` on dozens of nodes during an outage.

## Implementation

Parse **netstat**-class output with one event per row or a pre-counted `time_wait_count` per host. The sample assumes many lines per host with `state`/`status`; if you pre-aggregate, adjust the `stats` to `sum(time_wait_count)` instead.

## Detailed Implementation

Prerequisites
• Script **ss -tan** or `netstat -tan` on a fixed schedule; `ss` is usually preferred for speed. Emit **key=value** including **host** and the socket **state**.

Step 1 — Configure data collection
Coalesce `state` and `status` in **props** if vendors differ, so the `search` line works without OR spam.

Step 2 — Create the search and alert
SPL in the `spl` field; change **32000** to a number derived from your OS `ip_local_port_range` and workload.

**Understanding this SPL** — `search` first keeps only `TIME_WAIT` lines, `stats` counts per host, then applies a static ceiling. Add `| bucket _time span=1m` earlier if a single giant snapshot misleads you—some teams prefer a **timechart** of counts instead of static max.


Step 3 — Validate
On the host, `ss -s` and `ss -tan state time-wait | wc -l` should be in the same ballpark as Splunk in the last poll. For tuning, also check `sysctl` values for `tcp_fin_timeout` and `ip_local_port_range`.

Step 4 — Operationalize
Work with the app on connection pool sizing, `TIME_WAIT` reuse settings where safe, and whether the service should move to a connection-oriented proxy.



## SPL

```spl
index=os sourcetype=custom:netstat host=*
| search state="TIME_WAIT" OR status="TIME_WAIT"
| stats count as time_wait_count by host
| eval warning_level=32000
| where time_wait_count > warning_level
```

## Visualization

Gauge, Single Value

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
