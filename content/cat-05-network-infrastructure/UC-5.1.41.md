<!-- AUTO-GENERATED from UC-5.1.41.json — DO NOT EDIT -->

---
id: "5.1.41"
title: "VLAN Configuration Mismatches and Tagging Violations (Meraki MS)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.41 · VLAN Configuration Mismatches and Tagging Violations (Meraki MS)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We help you know early when something looks wrong with vlan configuration mismatches and tagging violations so the team can act before it grows into a bigger outage.*

---

## Description

Detects VLAN configuration errors and tagging violations that disrupt network segmentation.

## Value

Network engineers detect Meraki MS VLAN configuration mismatches including access ports on default VLAN 1 and unrestricted trunk ports, ensuring proper network segmentation.

## Implementation

Monitor VLAN-related error events. Cross-reference with API device VLAN config.

## Detailed Implementation

### Prerequisites
* Meraki MS VLAN configuration data from Dashboard API. Data in `index=meraki` with `sourcetype=meraki:api:switch:ports`. Key fields: `vlan`, `type` (access/trunk), `allowedVlans`, `portId`.
* VLAN mismatches: access port on wrong VLAN, trunk port missing required VLANs, native VLAN inconsistency between connected switches. These cause connectivity issues and potential security exposure.

### Step 1 — - Configure data collection
```
# API: GET /devices/{serial}/switch/ports
# Returns VLAN assignment, trunk allowed VLANs, native VLAN
```
Verify:
```spl
index=meraki sourcetype="meraki:api:switch:ports" earliest=-4h
| stats dc(portId) by host, vlan
```

### Step 2 — - Create the search and alert

**Primary search -- VLAN configuration mismatch detection:**
```spl
index=meraki sourcetype="meraki:api:switch:ports" earliest=-4h
| eval port=coalesce(portId, port_id)
| eval port_type=coalesce(type, port_type)
| eval port_vlan=tonumber(coalesce(vlan, access_vlan))
| eval device=coalesce(serial, host)
| lookup meraki_networks.csv serial AS device OUTPUT network_name
| eval issue=case(
    port_type="access" AND (isnull(port_vlan) OR port_vlan=1), "Access port on default VLAN 1",
    port_type="trunk" AND match(allowedVlans, "(?i)all"), "Trunk allows ALL VLANs (not restricted)",
    1==1, null())
| where isnotnull(issue)
| stats count as ports values(port) as affected_ports by network_name, device, issue
| eval severity=case(
    match(issue, "(?i)VLAN 1"), "WARNING -- ".ports." access ports on default VLAN 1",
    match(issue, "(?i)ALL VLANs"), "INFO -- trunk ports not restricted",
    1==1, "INFO")
| sort severity, -ports
```

### Step 3 — - Validate
(a) Dashboard: Switch > Switch ports -- check VLAN assignments per port.
(b) Verify intended VLAN design against actual configuration.
(c) Check trunk allowed VLANs against required VLANs.

### Step 4 — - Operationalize
Dashboard ("Meraki MS -- VLAN Configuration"):
* Row 1 -- Single-value: "Ports on VLAN 1", "Unrestricted trunks".
* Row 2 -- VLAN mismatch table.

### Step 5 — - Troubleshooting

* **Access port on wrong VLAN** -- Update VLAN assignment in Dashboard: Switch > Switch ports. Verify DHCP scope matches new VLAN.

* **Trunk allows all VLANs** -- Restrict to required VLANs only: Dashboard > Switch ports > VLAN configuration > Allowed VLANs. This reduces broadcast domain scope.

* **VLAN tagging violation** -- 802.1Q tagged frames on an access port. Check if connected device is sending tagged frames (e.g., IP phone with voice VLAN).

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*VLAN*"
| stats count as vlan_error_count by switch_name, vlan_id
| where vlan_error_count > 5
```

## Visualization

Table of VLAN issues; timeline of configuration changes; network diagram with VLAN details.

## Known False Positives

VLAN work during moves, adds, and wireless SSID changes is expected. Exclude staging fabrics and change windows you already know about.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
