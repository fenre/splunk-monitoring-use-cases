<!-- AUTO-GENERATED from UC-1.1.78.json — DO NOT EDIT -->

---
id: "1.1.78"
title: "Open Port Changes"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.1.78 · Open Port Changes

## Description

Compares the latest **port_list** string from each `openPorts` sample to the immediately previous sample for the same **host**, surfacing new listening-port shapes when the list changes (requires two polls per host).

## Value

A port that was not in yesterday’s `openPorts` window is a fast second opinion before you reach for a live **packet** capture—especially for unexpected **LISTEN** on high-numbered or database ports.

## Implementation

If your TA uses multi-value **port** fields instead of a single `port_list` string, replace the `!=` with `mvdiff` / `setdiff` logic on **mv** fields. Seed a **lookup** of `approved_ports` for noise control.

## Detailed Implementation

Prerequisites
• `openPorts` script enabled on a cadence that is faster than the longest service restart you care about; otherwise you will miss a five-second listener.

**SPL** — The **streamstats** form replaces the old template that referenced **previous_ports** without defining it. If you prefer state in a **KV** store, you can re-write with **lookup**+**outputlookup** per host instead.


Step 3 — Validate
`ss -lntup` on the same host after the alert; for proof of **PID**, use `lsof -i` or your EDR, not the raw **openPorts** line alone in regulated cases.

Step 4 — Operationalize
Any **openPorts**+**docker-proxy** on unexpected ports should be paired with the container ID from your orchestration log.



## SPL

```spl
index=os sourcetype=openPorts host=*
| streamstats window=2 global=f last(port_list) as prev_ports by host
| where isnotnull(prev_ports) AND port_list!=prev_ports
```

## Visualization

Alert, Table

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
