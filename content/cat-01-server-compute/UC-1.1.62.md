<!-- AUTO-GENERATED from UC-1.1.62.json — DO NOT EDIT -->

---
id: "1.1.62"
title: "Network Bandwidth Utilization by Interface (Linux)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.62 · Network Bandwidth Utilization by Interface (Linux)

## Description

Builds five-minute byte deltas on each interface from cumulative counters, converts the combined send+receive volume into megabits per second, and flags intervals above a high baseline (500 Mbps here—tune to your link speeds).

## Value

Knowing which NICs are saturated for long stretches drives upgrades, rebalancing, and QoS before queuing and drops spread across apps that share the same link.

## Implementation

Keep the `interfaces` input on a short interval (≤60s) so first/last inside each five-minute bin reflects real use. Set `>500` from your p95 capacity (for example, alert when sustained above 70% of a 1 Gbps link by using `>700`).

## Detailed Implementation

Prerequisites
• `Splunk_TA_nix` with the **interfaces** scripted input pointed at the **os** index.
• Optional: CIM add-on to tag the sourcetype so the **tstats** block works.

Step 1 — Configure data collection
If samples are sparser than the five-minute **bin**, narrow the bin or switch to a `timechart` of **per_second* functions on summarized metrics.

Step 2 — Create the search and alert
Tuning recipe: set **mbps** threshold to `0.7 * link_gbps * 1000` for 70% util alerts once you add a `lookup` for link speed per `host`+`interface`.

**Optional CIM / accelerated form** — The `cimSpl` mirrors the same **mbps** idea over **All_Traffic**; rename **All_Traffic.dvc** / **src_interface** in your build if your CIM mapping uses different interface field names (many shops alias **src_interface** to **interface**).


Step 3 — Validate
`ip -s link` for errors, `sar -n DEV` (if `sar` exists) for sanity on throughput, and compare peak **mbps** in Splunk to what you expect from application charts.

Step 4 — Operationalize
Pair panels with the **Dropped Packets** use case in this library for the same **interface** field.



## SPL

```spl
index=os sourcetype=interfaces host=*
| bin _time span=5m
| stats first(bytes_in) as s_in last(bytes_in) as e_in first(bytes_out) as s_out last(bytes_out) as e_out by host, interface, _time
| eval dbytes_in=e_in-s_in
| eval dbytes_out=e_out-s_out
| eval mbps=((dbytes_in+dbytes_out)*8)/300/1000000
| where mbps>500
```

## CIM SPL

```spl
| tstats `summariesonly` sum(All_Traffic.bytes_in) as bi sum(All_Traffic.bytes_out) as bo
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.dvc All_Traffic.src_interface span=5m
| eval mbps=((bi+bo)*8)/300/1000000
| where mbps>500
```

## Visualization

Timechart, Heatmap

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
