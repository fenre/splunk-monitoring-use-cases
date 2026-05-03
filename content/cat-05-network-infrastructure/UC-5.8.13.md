<!-- AUTO-GENERATED from UC-5.8.13.json — DO NOT EDIT -->

---
id: "5.8.13"
title: "Network Device Inventory and Change Audit (Meraki)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.8.13 · Network Device Inventory and Change Audit (Meraki)

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Configuration

*We keep an inventory and change feel for Meraki hardware and settings so large moves do not get lost in the day-to-day noise.*

---

## Description

Maintains accurate inventory of network devices and tracks hardware/software changes.

## Value

Network operations teams maintain a real-time Meraki device inventory with change audit trail, tracking device additions, removals, moves, and configuration changes across all networks for operational awareness and compliance.

## Implementation

Query devices API to build current inventory. Track additions/removals.

## Detailed Implementation

### Prerequisites
- Cisco Meraki Add-on for Splunk polling Meraki Dashboard API for device inventory and change events. Data in `index=meraki` with `sourcetype=meraki:api:devices` (inventory) and `sourcetype=meraki:events` (change log). Key fields: `serial`, `name`, `model`, `firmware`, `network`, `tags`, `address`, `lanIp`.
- Meraki change events include: device additions/removals, network creation/deletion, configuration changes (SSID, firewall rules, VLAN), and device moves between networks.

### Step 1 — Configure data collection
Verify inventory and change data:
```spl
(index=meraki sourcetype="meraki:api:devices") OR (index=meraki sourcetype="meraki:events" ("added" OR "removed" OR "moved" OR "changed")) earliest=-24h
| stats count by sourcetype
```

### Step 2 — Create the search and alert

**Primary search — Device inventory changes:**
```spl
index=meraki sourcetype="meraki:events" earliest=-24h
| where match(_raw, "(?i)(device.*added|device.*removed|device.*moved|claim|unclaim)")
| eval change_type=case(match(_raw, "(?i)added|claim"), "ADDED", match(_raw, "(?i)removed|unclaim"), "REMOVED", match(_raw, "(?i)moved"), "MOVED", 1==1, "CHANGED")
| lookup meraki_networks.csv network OUTPUT site_name tier
| stats count by change_type, network, site_name, deviceName, deviceSerial
| sort change_type, -count
```

#### Understanding this SPL: Device inventory changes in Meraki are significant operational events. A device added means new hardware deployed; a device removed could mean decommissioned or stolen; a device moved between networks means a topology change. In a cloud-managed environment, these changes happen through the dashboard and should be tracked for audit compliance.

**Current device inventory snapshot:**
```spl
index=meraki sourcetype="meraki:api:devices" earliest=-1h
| dedup serial sortby -_time
| eval device_type=case(match(model, "^MX"), "Security", match(model, "^MR"), "Wireless", match(model, "^MS"), "Switching", match(model, "^MV"), "Camera", match(model, "^MT"), "Sensor", 1==1, "Other")
| stats count by network, device_type
| chart sum(count) by network device_type
```

**Configuration change audit:**
```spl
index=meraki sourcetype="meraki:events" earliest=-7d
| where match(_raw, "(?i)(ssid|firewall|vlan|settings|configuration|port)")
| lookup meraki_networks.csv network OUTPUT site_name
| stats count as changes values(type) as change_types by network, site_name, adminId
| sort -changes
```

### Step 3 — Validate
(a) Add a test device to a Meraki network (claim) and verify the event appears in Splunk.
(b) Compare the device inventory count in Splunk with Meraki Dashboard: Organization > Inventory.
(c) Make a configuration change (e.g., rename an SSID) and verify it appears in the change audit.

### Step 4 — Operationalize
Dashboard ("Meraki Device & Change Audit"):
- Row 1 — Single-value tiles: "Total devices", "Devices added (24h)", "Devices removed (24h)", "Config changes (7d)".
- Row 2 — Inventory changes table: change type, device, network, site.
- Row 3 — Device inventory by type and network.
- Row 4 — Configuration change audit: network, admin, change types, count.

Alerting:
- High (device removed from production network): investigate — decommission or theft.
- Warning (> 5 config changes in 1 hour by same admin): bulk change — verify intentional.
- Info (new device added): tracking for asset management.

### Step 5 — Troubleshooting

- **Change events missing** — Meraki event log has a retention limit in the API. Ensure the TA polls frequently enough to capture all events before they roll out.

- **Device count mismatch** — `dedup serial` may miss devices with null serial fields (rare). Check for any devices without serial numbers in the raw data.

- **adminId shows API key hash instead of name** — API-driven changes show the API key identifier, not a username. Map API keys to owners in a lookup.

## SPL

```spl
index=cisco_network sourcetype="meraki:api"
| stats count as device_count by device_type, network_id
| append [search index=cisco_network sourcetype="meraki:api" | stats count as org_count]
| fillnull device_count value=0
```

## Visualization

Inventory summary table; device count by type pie chart; change log timeline.

## Known False Positives

Inventory pulls during hardware refresh or RMAs may spike changes; use baselines and change records before treating as unknown gear.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
