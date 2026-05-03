<!-- AUTO-GENERATED from UC-5.1.33.json — DO NOT EDIT -->

---
id: "5.1.33"
title: "Half-Duplex Negotiation Anomaly"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.33 · Half-Duplex Negotiation Anomaly

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Fault

*We help you know early when something looks wrong with half-duplex negotiation anomaly so the team can act before it grows into a bigger outage.*

---

## Description

Half/full duplex mismatches causing performance degradation.

## Value

Network engineers detect half-duplex negotiation anomalies on active interfaces, a condition that should not exist in modern networks and causes collisions and poor performance.

## Implementation

Poll EtherLike-MIB dot3StatsDuplexStatus; ingest syslog for duplex mismatch messages. Alert on half-duplex on gigabit uplinks or explicit mismatch events.

## Detailed Implementation

### Prerequisites
* Half-duplex negotiation data from SNMP or syslog. Extends UC-5.1.17 with automated detection of half-duplex as an anomaly. Key: dot3StatsDuplexStatus OID or `show interface status`.
* Half-duplex should not exist in modern networks. Any interface negotiating half-duplex is a misconfiguration or hardware issue causing collisions and poor performance.

### Step 1 — - Configure data collection
```
# Same as UC-5.1.17 -- SNMP polling for duplex status
# dot3StatsDuplexStatus (.1.3.6.1.2.1.10.7.2.1.19)
# Regularly poll all interface statuses
```
Verify:
```spl
index=network earliest=-4h
| eval duplex=coalesce(dot3StatsDuplexStatus, duplex_mode, duplex)
| where duplex="2" OR match(duplex, "(?i)half")
| stats count by host, ifName
```

### Step 2 — - Create the search and alert

**Primary search -- Half-duplex anomaly detection:**
```spl
index=network earliest=-4h
| eval duplex=coalesce(dot3StatsDuplexStatus, duplex_mode, duplex)
| eval speed=coalesce(ifSpeed, speed, link_speed)
| eval interface=coalesce(ifName, interface, port)
| eval device=coalesce(host, device_name)
| where duplex="2" OR match(duplex, "(?i)half")
| eval oper_status=coalesce(ifOperStatus, admin_status)
| where oper_status="1" OR match(oper_status, "(?i)up")
| stats count latest(_time) as last_seen by device, interface, speed
| eval severity="WARNING -- half-duplex detected on active interface"
| eval last_seen_time=strftime(last_seen, "%Y-%m-%d %H:%M:%S")
| table device, interface, speed, last_seen_time, severity
| sort device, interface
```

### Step 3 — - Validate
(a) CLI: `show interface status` -- check for any "a-half" or "half" interfaces.
(b) Check remote end: `show cdp neighbor <intf> detail` -- verify remote side duplex.
(c) CLI: `show interface <intf> | include collisions` -- check collision counters.

### Step 4 — - Operationalize
Dashboard ("Network -- Duplex Anomalies"):
* Row 1 -- Single-value: "Half-duplex interfaces", "Devices affected".
* Row 2 -- Half-duplex interface list.

Alert: Warning (any active half-duplex interface): fix immediately.

### Step 5 — - Troubleshooting

* **Fix half-duplex** -- Set both ends to auto-negotiate: `speed auto` / `duplex auto`. Or hardcode both to same speed and full-duplex. Never mix hardcoded and auto.

* **Connected device forces half-duplex** -- Old or misconfigured device (printer, legacy equipment). Hardcode both sides to 100/full or 10/full as appropriate for the device capability.

* **Collisions on half-duplex** -- Expected behavior. Half-duplex uses CSMA/CD. Fix by converting to full-duplex.

## SPL

```spl
index=network (sourcetype=snmp:interface OR sourcetype="cisco:ios") ("duplex" OR "Duplex" OR "dot3StatsDuplexStatus" OR "halfDuplex" OR "fullDuplex")
| rex "duplex mismatch|(?<duplex_status>halfDuplex|fullDuplex|unknown)"
| where match(_raw,"mismatch|halfDuplex") OR duplex_status="halfDuplex"
| stats count by host, ifDescr, duplex_status
| table host ifDescr duplex_status count
```

## Visualization

Table (host, interface, duplex), Status grid, Single value.

## Known False Positives

Intermittent autonegotiation blips and cable wiggles during moves can look like a mismatch—verify with a sustained port test.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
