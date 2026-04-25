<!-- AUTO-GENERATED from UC-1.1.52.json — DO NOT EDIT -->

---
id: "1.1.52"
title: "Connection Tracking Table Exhaustion"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.1.52 · Connection Tracking Table Exhaustion

## Description

Detects when the netfilter connection tracking table on a host is most of the way to its hard maximum, a condition that will soon block or drop new flow setups.

## Value

Avoiding a full conntrack table protects stateful firewalls, NAT, and any service that cannot accept “cannot allocate new connection” style failures during busy periods.

## Implementation

Sample `current_count` and `max_size` (from `/proc/sys/net/netfilter/nf_conntrack_max` or equivalent) into Splunk, compute utilization, and page before you reach the drop regime above roughly ninety percent in most shops.

## Detailed Implementation

Prerequisites
• Deploy a small script (often paired with the TA) that reads `nf_conntrack_count` and the configured max, then posts **key=value** lines to Splunk on a 60 second cadence.

Step 1 — Configure data collection
Keep units consistent: both counts must be in the same integer space. Re-read max after sysctls or boot.

Step 2 — Create the search and alert
The SPL in the `spl` field is self-contained; set separate alerts at 80% (warn) and 95% (page) if you prefer two saved searches.


Step 3 — Validate
On host, compare `cat /proc/sys/net/netfilter/nf_conntrack_count` to the latest event; ensure `ss -s` or `conntrack -S` (where available) does not show divergent health.

Step 4 — Operationalize
Runbook: raise `nf_conntrack_max` with capacity review, reduce wasteful long-lived connections, or shard workloads.



## SPL

```spl
index=os sourcetype=custom:conntrack host=*
| stats latest(current_count) as current, latest(max_size) as maximum by host
| eval usage_pct=(current/maximum)*100
| where usage_pct > 80
```

## Visualization

Gauge, Alert

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
