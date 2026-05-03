<!-- AUTO-GENERATED from UC-5.1.49.json — DO NOT EDIT -->

---
id: "5.1.49"
title: "Port Access Control List (ACL) Hits and Block Events (Meraki MS)"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.1.49 · Port Access Control List (ACL) Hits and Block Events (Meraki MS)

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Security

*We help you know early when something looks wrong with port access control list so the team can act before it grows into a bigger outage.*

---

## Description

Tracks ACL rule hits to monitor policy enforcement and identify anomalous traffic.

## Value

Security teams analyze Meraki MS ACL deny events to validate access control policy effectiveness and detect scanning or unauthorized access attempts blocked at the switch layer.

## Implementation

Monitor ACL deny/block events from syslog. Track frequently blocked source/destinations.

## Detailed Implementation

### Prerequisites
* Meraki MS ACL hit events from syslog. Data in `index=meraki` with `sourcetype=meraki:events`. Key events: ACL deny hits, ACL permit hits (if logging enabled), Layer 3 switch ACL blocks.
* Meraki MS ACLs: configured in Dashboard > Switch > Access policies or per-port ACLs. Layer 3 routing ACLs on L3 switches control inter-VLAN traffic.

### Step 1 — - Configure data collection
```
# Meraki Dashboard > Switch > Access policies
# Configure ACLs with logging
# Syslog: enable Event log
```
Verify:
```spl
index=meraki sourcetype="meraki:events" earliest=-24h
| where match(_raw, "(?i)ACL|access.*list|access.*control|denied.*by.*policy|blocked")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- ACL hits and block events:**
```spl
index=meraki sourcetype="meraki:events" earliest=-4h
| where match(_raw, "(?i)ACL|access.*list|access.*control|denied.*by.*policy|blocked")
| eval device=coalesce(serial, host)
| lookup meraki_networks.csv serial AS device OUTPUT network_name
| eval src=coalesce(src, src_ip)
| eval dst=coalesce(dest, dest_ip, dst)
| eval action=if(match(_raw, "(?i)deny|block|drop"), "DENY", "PERMIT")
| where action="DENY"
| stats count as hits dc(src) as unique_sources dc(dst) as unique_targets by network_name, device
| eval severity=case(
    hits > 500, "WARNING -- high ACL deny rate",
    unique_sources > 20, "INFO -- denies from many sources",
    1==1, "INFO")
| where severity != "INFO"
| sort severity, -hits
```

### Step 3 — - Validate
(a) Dashboard: Switch > Access policies -- check ACL rules.
(b) Verify denied traffic is expected (security policy) vs unexpected (misconfiguration).
(c) Check for legitimate traffic being blocked.

### Step 4 — - Operationalize
Dashboard ("Meraki MS -- ACL Events"):
* Row 1 -- Single-value: "ACL denies (4h)", "Unique blocked sources".
* Row 2 -- ACL deny event table.

### Step 5 — - Troubleshooting

* **Legitimate traffic blocked** -- Review ACL rules. Add explicit permit before deny for required traffic flows.

* **High deny rate from single source** -- Possible scanning or misconfigured application. Investigate source device.

* **ACL not effective** -- Verify ACL is applied to correct port or VLAN interface. Check rule order (first match wins).

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*ACL*" action="block"
| stats count as block_count by switch_name, src_mac, dest_mac
| sort - block_count
```

## Visualization

Table of blocked traffic; timeline of ACL hits; top blocked addresses chart.

## Known False Positives

New security baselines, pen tests, and mis-pointed app VIPs can spike denies. Weed out scanners and approved tests via subnet lookup.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
