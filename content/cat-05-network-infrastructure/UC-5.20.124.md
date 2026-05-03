<!-- AUTO-GENERATED from UC-5.20.124.json — DO NOT EDIT -->

---
id: "5.20.124"
title: "IPv6 Stateless Address Autoconfiguration (SLAAC) Monitoring and Anomaly Detection"
status: "verified"
criticality: "high"
splunkPillar: "Platform"
---

# UC-5.20.124 · IPv6 Stateless Address Autoconfiguration (SLAAC) Monitoring and Anomaly Detection

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Platform &middot; **Type:** Availability, Security &middot; **Wave:** Walk &middot; **Status:** Verified

*When a new device joins the network, it automatically picks up a new-format address (IPv6) by listening to the router's announcements. But first, it checks to make sure nobody else already has that same address (DAD). We monitor this process to make sure addresses are being handed out correctly and nobody is blocking new devices from getting their addresses.*

---

## Description

Monitors SLAAC (RFC 4862) operations for anomalies: DAD failures (possible DoS attack or genuine conflicts), conflicting prefix advertisements from multiple routers, prefix lifetime expirations, and M/O flag inconsistencies that cause addressing failures.

## Value

SLAAC is how most IPv6 hosts get their addresses. When SLAAC fails, hosts cannot communicate over IPv6. DAD failures can indicate an active attack where an attacker responds to all DAD probes, preventing legitimate hosts from configuring addresses. Prefix conflicts from multiple routers create split addressing that is extremely difficult to troubleshoot.

## Implementation

Monitor RA advertisements for prefix consistency. Track DAD outcomes. Alert on DAD failures and prefix conflicts.

## Detailed Implementation

### Prerequisites
- Router NDP logging enabled.

### Step 1 — Configure SLAAC monitoring
NDP events are logged by default at informational level. Ensure syslog captures these events.

### Step 2 — Create monitoring searches

**DAD failure detection:**
```spl
index=network "DAD" AND ("fail" OR "duplicate" OR "conflict") earliest=-24h
| stats count as failures by host
| where failures > 3
```

**Prefix consistency check:**
```spl
index=network "RA" AND "prefix" earliest=-1h
| rex field=_raw "prefix\s*(?<prefix>[0-9a-fA-F:/]+)"
| stats dc(host) as advertising_routers values(host) as routers by prefix
| where advertising_routers > 1
```

### Step 3 — Validate
Join a new host to a SLAAC-enabled VLAN. Verify it receives an address via SLAAC and that the event appears in Splunk.

### Step 4 — Operationalize
**Dashboard:** SLAAC health by VLAN. **Alert:** DAD failure — high. Prefix conflict — high.

### Step 5 — Troubleshooting
- DAD failures: Check for devices with statically assigned addresses that conflict with SLAAC assignments.
- Prefix conflicts: Verify only one router is advertising prefixes on each segment, or that all routers advertise the same prefixes.

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe") earliest=-24h
  ("%IPV6_ND" OR "%DHCPV6" OR "SLAAC" OR "DAD" OR "autoconfig" OR "prefix")
| eval slaac_event=case(
    match(_raw, "(?i)DAD.*fail|duplicate.*address|DAD.*conflict"), "DAD_FAILURE",
    match(_raw, "(?i)prefix.*conflict|prefix.*mismatch"), "PREFIX_CONFLICT",
    match(_raw, "(?i)lifetime.*expired|prefix.*deprecated"), "PREFIX_EXPIRED",
    match(_raw, "(?i)SLAAC|autoconfig"), "SLAAC_EVENT",
    1=1, "OTHER")
| stats count as events by host, slaac_event
| eval severity=case(
    slaac_event="DAD_FAILURE", "HIGH — DAD failures detected — possible attack or genuine duplicate",
    slaac_event="PREFIX_CONFLICT", "HIGH — conflicting prefixes from multiple routers",
    slaac_event="PREFIX_EXPIRED", "MEDIUM — prefix lifetime expired — hosts losing addresses",
    1=1, null())
| where isnotnull(severity)
| sort -events
```

## Visualization

(1) Table: SLAAC events by type. (2) Single-value: DAD failures. (3) Timechart: SLAAC events. (4) Status: prefix consistency.

## Known False Positives

**VM migration.** When VMs migrate (vMotion), the new location may trigger DAD for the existing address. Brief DAD events during migration are normal.

**VRRP/HSRP.** Redundancy protocols may briefly cause duplicate addresses during failover.

## References

- [RFC 4862 — IPv6 Stateless Address Autoconfiguration](https://www.rfc-editor.org/rfc/rfc4862)
- [RFC 4861 — Neighbor Discovery for IP version 6](https://www.rfc-editor.org/rfc/rfc4861)
