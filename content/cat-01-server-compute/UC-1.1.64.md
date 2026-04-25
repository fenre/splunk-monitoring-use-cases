<!-- AUTO-GENERATED from UC-1.1.64.json — DO NOT EDIT -->

---
id: "1.1.64"
title: "Network Latency Monitoring (Ping RTT)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.64 · Network Latency Monitoring (Ping RTT)

## Description

Summarises round-trip time per host and ping target, then compares the maximum RTT in the window to a host+target local upper bound of mean + two standard deviations, catching unstable long tails.

## Value

Average ping can look fine while a few very late replies spoil voice, replication, or leader election—this test surfaces tail behaviour without needing external synthetics in many shops.

## Implementation

Run `ping` or `fping` on a short cadence, parse **rtt_ms** and **target**, and keep **target** lists under version control. Add `| where stdev>0` if you need to avoid degenerate `upper_bound=avg` when there is a single sample.

## Detailed Implementation

Prerequisites
• Cron or **systemd** timer that calls your script; Splunk user must be allowed to open raw ICMP sockets (often **root** or **cap_net_raw**).

Step 1 — Configure data collection
One event per (host, target) per interval is easier to reason about than a single string with all targets—pick one pattern and stay consistent.

Step 2 — Create the search and alert
The `spl` no longer references an undefined **baseline** field; the bound is per-row from the **stats** of the window. Increase lookback to smooth Wi‑Fi noise if needed.

**CIM note** — There is no standard CIM dataset for ad-hoc ICMP; keep this UC on the **custom** sourcetype unless you import RTT into a metrics workspace.


Step 3 — Validate
From the same host, run `ping` / `mtr` manually for the same **target** and second; compare the Splunk `avg_latency` to what you see. Use path MTU work only for application-layer follow-up, not as the first ICMP proof.

Step 4 — Operationalize
Page network when multiple hosts shift together (fabric issue); page apps when a single `target` drifts (dependency issue).



## SPL

```spl
index=os sourcetype=custom:ping_rtt host=*
| stats avg(rtt_ms) as avg_latency, max(rtt_ms) as max_latency, stdev(rtt_ms) as stddev by host, target
| eval upper_bound=avg_latency+(2*stddev)
| where max_latency > upper_bound
```

## Visualization

Timechart, Gauge

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
