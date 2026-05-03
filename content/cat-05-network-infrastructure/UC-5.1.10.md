<!-- AUTO-GENERATED from UC-5.1.10.json — DO NOT EDIT -->

---
id: "5.1.10"
title: "VLAN Configuration Changes"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.1.10 · VLAN Configuration Changes

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Configuration, Compliance

*We flag when someone creates or removes VLANs on a device, because that can open holes in your segmentation if it was not planned.*

---

## Description

VLAN changes affect segmentation. Unauthorized changes can bypass security controls.

## Value

Network engineers track VLAN configuration changes including additions, deletions, and trunk modifications to detect unauthorized changes and correlate with connectivity incidents.

## Implementation

Forward syslog. Alert on VLAN creation/deletion. Correlate with change tickets.

## Detailed Implementation

### Prerequisites
* VLAN configuration change syslog messages. Data in `index=network` with `sourcetype=cisco:ios` or vendor-specific sourcetypes. Key events: VLAN added/deleted/modified, trunk allowed VLAN changes, access VLAN assignments.
* VLAN changes affect layer-2 segmentation and can cause widespread connectivity issues if incorrect. Unauthorized VLAN changes may indicate configuration drift or security bypass attempts.

### Step 1 — - Configure data collection
```
# Cisco IOS -- VLAN changes logged via config change logging
archive
 log config
  logging enable
  notify syslog contenttype plaintext

# VTP events: %SW_VLAN-6-VTP_DOMAIN_CHG, %SW_VLAN-4-VTP_USER_NOTIFICATION
```
Verify:
```spl
index=network earliest=-30d
| where match(_raw, "(?i)VLAN|vlan.*add|vlan.*delete|vlan.*change|switchport|VTP|trunk.*allow")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- VLAN configuration change tracking:**
```spl
index=network earliest=-24h
| where match(_raw, "(?i)VLAN|vlan.*add|vlan.*delete|vlan.*modif|switchport.*access.*vlan|switchport.*trunk.*allowed|VTP")
| rex field=_raw "(?i)vlan\s+(?<vlan_id>\d+)"
| eval device=coalesce(host, device_name)
| eval change_type=case(
    match(_raw, "(?i)add|create|new"), "VLAN_ADDED",
    match(_raw, "(?i)delet|remov"), "VLAN_DELETED",
    match(_raw, "(?i)modif|change|rename"), "VLAN_MODIFIED",
    match(_raw, "(?i)switchport.*access"), "ACCESS_VLAN_CHANGE",
    match(_raw, "(?i)trunk.*allowed"), "TRUNK_ALLOWED_CHANGE",
    match(_raw, "(?i)VTP"), "VTP_EVENT",
    1==1, "VLAN_EVENT")
| stats count as events values(vlan_id) as vlans dc(vlan_id) as unique_vlans by device, change_type
| eval severity=case(
    change_type="VLAN_DELETED", "WARNING -- VLAN(s) deleted",
    change_type="VTP_EVENT", "WARNING -- VTP event detected",
    events > 10, "INFO -- high VLAN change volume",
    1==1, "INFO")
| table device, change_type, events, unique_vlans, vlans, severity
| sort severity, -events
```

### Step 3 — - Validate
(a) CLI: `show vlan brief` -- verify current VLAN configuration.
(b) CLI: `show vtp status` -- check VTP mode and revision number.
(c) Cross-reference changes with change management tickets.

### Step 4 — - Operationalize
Dashboard ("Network -- VLAN Changes"):
* Row 1 -- Single-value: "VLAN changes (24h)", "VLANs added", "VLANs deleted".
* Row 2 -- VLAN change event table.

Alert: Warning (VLAN deleted): verify intentional change.

### Step 5 — - Troubleshooting

* **Accidental VLAN deletion** -- Impacts all ports assigned to that VLAN (ports move to "inactive" state). Restore: recreate VLAN and rename. Check `show interfaces status` for inactive ports.

* **VTP propagation issue** -- VTP revision number mismatch can cause VLAN database overwrite. Verify VTP mode (server/client/transparent) and domain name match. Consider VTP transparent mode for safety.

* **Trunk pruning incorrect** -- Allowed VLAN changes on trunks can isolate segments. Verify: `show interfaces trunk` to check allowed VLANs match requirements.

## SPL

```spl
index=network sourcetype="cisco:ios" "%VLAN_MANAGER-6-VLAN_CREATE" OR "%VLAN_MANAGER-6-VLAN_DELETE"
| table _time host _raw | sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.command All_Changes.action span=1h
| sort -count
```

## Visualization

Table, Timeline.

## Known False Positives

Authorized changes during change windows, scheduled compliance pushes, or device decommissioning will trigger this. Correlate to tickets before escalating.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
