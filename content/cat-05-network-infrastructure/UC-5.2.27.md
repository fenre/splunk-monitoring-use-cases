<!-- AUTO-GENERATED from UC-5.2.27.json — DO NOT EDIT -->

---
id: "5.2.27"
title: "NAT Pool Usage and Exhaustion Alerts (Meraki MX)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.27 · NAT Pool Usage and Exhaustion Alerts (Meraki MX)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity

*We check how full shared public address pools are on the small office so new guests and new sites do not run out of outbound space.*

---

## Description

Monitors NAT pool utilization to prevent address exhaustion that could block outbound traffic.

## Value

Operations teams detect Meraki MX NAT port exhaustion events, identifying when outbound connection capacity is reached and investigating top connection consumers.

## Implementation

Query appliance API for NAT pool metrics. Alert on >80% utilization.

## Detailed Implementation

### Prerequisites
* Meraki MX NAT logs via syslog or API. Data in `index=meraki` with `sourcetype=meraki:events`. Key events: NAT translations, port exhaustion warnings.
* Meraki MX uses PAT (Port Address Translation) by default. All internal traffic is NATed to the WAN IP. With many users and applications, the port pool (65K ports per WAN IP) can be exhausted.

### Step 1 — - Configure data collection
Verify NAT events:
```spl
index=meraki sourcetype="meraki:events" earliest=-4h
| where match(_raw, "(?i)NAT|port.*exhaust|translation|SNAT")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- NAT pool usage monitoring:**
```spl
index=meraki sourcetype="meraki:events" earliest=-4h
| where match(_raw, "(?i)NAT|port.*exhaust|translation.*fail|SNAT.*fail|no.*available.*port")
| eval nat_event=case(match(_raw, "(?i)exhaust|no.*available|pool.*full"), "NAT_EXHAUSTED", match(_raw, "(?i)fail"), "NAT_FAILURE", match(_raw, "(?i)warning|threshold|high"), "NAT_WARNING", 1==1, "NAT_EVENT")
| stats count as events latest(_time) as last_event by host, nat_event
| eval severity=case(nat_event="NAT_EXHAUSTED", "CRITICAL -- NAT port exhaustion", nat_event="NAT_FAILURE" AND events > 50, "HIGH -- NAT failures", 1==1, "WARNING")
| where severity != "WARNING" OR events > 10
| sort severity, -events
```

### Step 3 — - Validate
(a) Dashboard: Security & SD-WAN > Addressing & VLANs -- check WAN IP and NAT mode.
(b) Monitor concurrent connections during peak hours.
(c) Check if 1:1 NAT rules are consuming dedicated IPs.

### Step 4 — - Operationalize
Dashboard ("Meraki MX -- NAT Health"):
* Row 1 -- Single-value: "NAT exhaustion events", "NAT failures".
* Row 2 -- NAT event timeline.

Alerting:
* Critical (NAT exhaustion): outbound connections failing.

### Step 5 — - Troubleshooting

* **NAT exhaustion** -- Too many concurrent outbound connections for available ports. Options: (1) configure additional WAN IPs for NAT, (2) identify and reduce connections from top users/applications, (3) check for infected hosts creating many outbound connections.

* **NAT with multiple WAN uplinks** -- Meraki distributes NAT across uplinks. If one uplink has more capacity, ensure traffic distribution is balanced.

* **1:1 NAT issues** -- 1:1 NAT maps an internal IP to a dedicated public IP. Verify no conflicts with port-forwarding rules.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" nat_pool_usage=*
| stats max(nat_pool_usage) as peak_nat_usage, count by nat_pool_id
| eval nat_capacity_pct=round(peak_nat_usage*100/254, 2)
| where nat_capacity_pct > 80
```

## Visualization

Gauge of NAT pool usage; capacity timeline; pool exhaustion alert dashboard.

## Known False Positives

New sites, guest Wi-Fi, and more endpoints can use more public NAT than last month without an exhaustion emergency.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
