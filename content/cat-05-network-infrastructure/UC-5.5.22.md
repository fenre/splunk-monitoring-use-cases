<!-- AUTO-GENERATED from UC-5.5.22.json — DO NOT EDIT -->

---
id: "5.5.22"
title: "Aruba EdgeConnect SD-WAN Tunnel and Application Performance"
status: "community"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.5.22 · Aruba EdgeConnect SD-WAN Tunnel and Application Performance

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Performance &middot; **Wave:** Crawl &middot; **Status:** Community

*We watch the SD-WAN appliances at branch offices report whether their connections to headquarters are healthy. When a connection goes down or starts dropping data, we alert the network team within minutes — long before users at that branch start complaining about slow apps.*

---

## Description

Tracks tunnel state and peer health across the HPE Aruba EdgeConnect (formerly Silver Peak) SD-WAN fabric. Counts DOWN and DEGRADED events per appliance / tunnel / peer triplet so a single bad transport surfaces to the top of the table even when the overall fabric appears healthy.

## Value

EdgeConnect powers SD-WAN for organisations that want WAN optimisation as a first-class feature alongside the SD-WAN overlay. The platform's selling point — Boost (compression, deduplication, caching) — also makes it harder to debug when something goes wrong, because traffic that the network team expects to see is being optimised away. Centralising tunnel and peer telemetry in Splunk lets the NOC see Boost bypass events, BIO failover, and tunnel-down transitions from one console — which the on-prem Orchestrator cannot do for organisations running multi-vendor SD-WAN estates.

## Implementation

Forward EdgeConnect appliance syslog to Splunk on UDP/TCP 514. Optionally poll the Aruba Orchestrator API on a 5-minute schedule for structured tunnel and application metrics. Alert on tunnel DOWN / DEGRADED states and on WAN-optimisation bypass events that indicate Boost has gone idle.

## SPL

```spl
index=sdwan sourcetype="aruba:edgeconnect"
| search tunnel_state="DOWN" OR tunnel_state="DEGRADED"
| stats count by appliance_name, tunnel_name, tunnel_state, peer_name
| sort - count
```

## Visualization

Status grid (per-appliance tunnel health), Table (degraded tunnels sorted by event count), Line chart (WAN-optimisation savings over time, useful for capacity-planning conversations).

## Known False Positives

**Scheduled BIO failover testing.** Quarterly business-impact tests intentionally take a primary transport DOWN to validate failover. Suppress alerts during announced test windows.

**Boost idle on small flows.** The WAN-optimisation engine intentionally bypasses very small flows (UDP DNS, ICMP). Filter the bypass alert on per-minute byte volume so it does not fire on a healthy steady state of bypass-eligible traffic.

**Cross-region tunnel ping-time variance.** Tunnels spanning multiple continents legitimately oscillate between OK and DEGRADED on minute-level granularity. Use a 5-minute median, not a 1-minute snapshot, for the alert threshold.

## References

- [HPE Aruba EdgeConnect SD-WAN](https://www.arubanetworks.com/products/sd-wan/)
- [Aruba Orchestrator administration guide](https://www.arubanetworks.com/techdocs/Orchestrator/Default.htm)
