<!-- AUTO-GENERATED from UC-5.1.43.json — DO NOT EDIT -->

---
id: "5.1.43"
title: "DHCP Snooping Violations (Meraki MS)"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.1.43 · DHCP Snooping Violations (Meraki MS)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Security

*We help you know early when something looks wrong with dhcp snooping violations so the team can act before it grows into a bigger outage.*

---

## Description

Detects unauthorized DHCP servers and spoofing attempts that disrupt network address allocation.

## Value

Security teams detect rogue DHCP servers and DHCP snooping violations on Meraki MS switches, preventing unauthorized DHCP responses that cause IP address conflicts and man-in-the-middle attacks.

## Implementation

Enable DHCP snooping on MS switches. Monitor syslog for violations.

## Detailed Implementation

### Prerequisites
* Meraki MS DHCP snooping violation events from syslog. Data in `index=meraki` with `sourcetype=meraki:events`. Key events: DHCP snooping drops, unauthorized DHCP server detection.
* DHCP snooping: validates DHCP messages on untrusted ports. Blocks rogue DHCP servers from assigning incorrect IP addresses. Meraki MS supports DHCP snooping with trusted ports configured for legitimate DHCP servers.

### Step 1 — - Configure data collection
```
# Meraki Dashboard > Switch > DHCP server policy
# Set policy: Block or Alert on rogue DHCP servers
# Configure trusted DHCP server list
# Syslog: enable Event log
```
Verify:
```spl
index=meraki sourcetype="meraki:events" earliest=-7d
| where match(_raw, "(?i)DHCP.*snoop|rogue.*DHCP|unauthorized.*DHCP|DHCP.*block")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- DHCP snooping violation monitoring:**
```spl
index=meraki sourcetype="meraki:events" earliest=-24h
| where match(_raw, "(?i)DHCP.*snoop|rogue.*DHCP|unauthorized.*DHCP|DHCP.*block|DHCP.*drop|DHCP.*violation")
| eval device=coalesce(serial, host)
| lookup meraki_networks.csv serial AS device OUTPUT network_name
| rex field=_raw "(?i)(?:port|Port)\s+(?<port_id>\d+)"
| rex field=_raw "(?i)(?:MAC|mac).*?(?<rogue_mac>[0-9a-fA-F:]{12,17})"
| eval violation_type=case(
    match(_raw, "(?i)rogue.*server|unauthorized.*server"), "ROGUE_DHCP_SERVER",
    match(_raw, "(?i)drop|block"), "DHCP_DROP",
    1==1, "DHCP_VIOLATION")
| stats count as violations dc(rogue_mac) as unique_rogues values(rogue_mac) as rogue_macs values(port_id) as ports by network_name, device, violation_type
| eval severity=case(
    violation_type="ROGUE_DHCP_SERVER", "CRITICAL -- rogue DHCP server detected",
    violations > 10, "WARNING -- frequent DHCP snooping violations",
    1==1, "INFO")
| where severity != "INFO"
| sort severity, -violations
```

### Step 3 — - Validate
(a) Dashboard: Switch > DHCP server policy -- check policy and trusted server list.
(b) Dashboard: Network-wide > Event log -- filter for DHCP events.
(c) Verify legitimate DHCP servers are in the trusted list.

### Step 4 — - Operationalize
Dashboard ("Meraki MS -- DHCP Snooping"):
* Row 1 -- Single-value: "DHCP violations (24h)", "Rogue DHCP servers".
* Row 2 -- DHCP snooping violation table.

Alert: Critical (rogue DHCP server): investigate immediately.

### Step 5 — - Troubleshooting

* **Rogue DHCP server** -- Unauthorized device responding to DHCP requests. Identify MAC, trace to port. Disable port. Common culprits: misconfigured APs, small routers, VM hypervisors.

* **Legitimate server blocked** -- Add to trusted DHCP server list in Dashboard. Verify MAC and IP match.

* **DHCP snooping too aggressive** -- Review policy. Consider "Alert" mode before "Block" to identify false positives.

**DHCPv6 Considerations:** MS DHCP snooping and trusted-port policies may apply differently to DHCPv6 traffic; confirm Dashboard settings cover both stacks where IPv6 is enabled. DHCPv6 (RFC 8415) is a fundamentally different protocol from DHCPv4, using UDP ports 546/547. Key differences: (1) DHCPv6 does NOT provide default gateway — that comes from Router Advertisements. (2) Message types differ: Solicit/Advertise/Request/Reply instead of Discover/Offer/Request/Ack. (3) DHCPv6 Prefix Delegation (DHCPv6-PD) enables subnet allocation to downstream routers. (4) Syslog patterns differ: look for 'DHCPv6' in messages, not just 'DHCP'. For comprehensive DHCPv6 monitoring, see the IPv6 subcategory (UC-5.20.10, UC-5.20.141).

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*DHCP*Snooping*"
| stats count as violation_count by switch_name, port_id, server_ip
| where violation_count > 0
```

## Visualization

Table of violations; timeline of events; affected port details.

## Known False Positives

New VoIP, cameras, and docked laptops may appear on the wrong access VLAN until you update trusted ports and DHCP helpers.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
