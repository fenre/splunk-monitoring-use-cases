<!-- AUTO-GENERATED from UC-5.5.2.json — DO NOT EDIT -->

---
id: "5.5.2"
title: "Site Availability"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.5.2 · Site Availability

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We keep an eye on how our wide-area links and SD-WAN paths are behaving so we spot a bad circuit or policy issue before branch users lose voice, video, or critical apps.*

---

## Description

Edge device offline = remote site disconnected from the network.

## Value

Network operations teams maintain a real-time view of SD-WAN site availability across the enterprise, immediately identifying sites that are completely down or running with reduced redundancy.

## Implementation

Poll vManage device inventory API. Alert when any edge device becomes unreachable. Include site name and location.

## Detailed Implementation

### Prerequisites
- Cisco Catalyst Add-on for Splunk (TA_cisco_catalyst, Splunkbase 7538) polling vManage API for device status. The `/dataservice/device` and `/dataservice/system/device/vedges` endpoints provide device reachability, control connection status, and site health.
- Data in `index=sdwan` with `sourcetype=cisco:sdwan:device` or `cisco:sdwan:system`. Key fields: `site_id`, `system_ip`, `device_type` (vedge/cedge), `reachability` (reachable/unreachable), `personality` (vedge/vsmart/vmanage/vbond), `board_serial`.
- Build `sdwan_sites.csv` lookup (see UC-5.5.1) and `sdwan_devices.csv`: `system_ip,hostname,device_model,site_id,role` (e.g., `10.0.0.1,branch-chi-edge1,C8300-1N4T,200,edge`).
- Site availability = all edge devices at a site are reachable and have active control connections to vSmart. A site with one edge unreachable may still be available (if dual-router); a site with all edges unreachable is completely down.

### Step 1 — Configure data collection
Verify device status data:
```spl
index=sdwan sourcetype="cisco:sdwan:device" earliest=-15m
| stats count by reachability, device_type
```
You should see most devices as "reachable". Unreachable devices are currently offline.

### Step 2 — Create the search and alert

**Primary search — Site availability status:**
```spl
index=sdwan sourcetype="cisco:sdwan:device" earliest=-15m
| where device_type IN ("vedge", "cedge")
| stats count as total_edges count(eval(reachability="reachable")) as up_edges by site_id
| eval down_edges=total_edges - up_edges
| eval site_status=case(up_edges==0, "DOWN", up_edges < total_edges, "DEGRADED", 1==1, "UP")
| lookup sdwan_sites.csv site_id OUTPUT site_name region tier
| eval site_label=if(isnotnull(site_name), site_name, "Site-".site_id)
| where site_status!="UP"
| sort site_status, tier
```

#### Understanding this SPL: Calculates site availability by checking how many edge devices at each site are reachable. A "DOWN" site has no reachable edges — complete outage. "DEGRADED" means some edges are down — reduced capacity but still connected. Sorting by `tier` ensures Tier1 (headquarters, data centers) sites appear first.

**Site availability trending:**
```spl
index=sdwan sourcetype="cisco:sdwan:device" device_type IN ("vedge", "cedge") earliest=-7d
| bin _time span=5m
| stats count(eval(reachability="reachable")) as up count(eval(reachability="unreachable")) as down by _time, site_id
| eval total=up+down
| eval avail_pct=round(100*up/total, 1)
| lookup sdwan_sites.csv site_id OUTPUT site_name
| timechart span=5m avg(avail_pct) by site_name
```

**Device-level reachability detail:**
```spl
index=sdwan sourcetype="cisco:sdwan:device" reachability="unreachable" earliest=-1h
| lookup sdwan_devices.csv system_ip OUTPUT hostname device_model role
| lookup sdwan_sites.csv site_id OUTPUT site_name tier
| table _time, site_name, tier, hostname, system_ip, device_model, role
| sort tier, site_name
```

### Step 3 — Validate
(a) In vManage: Monitor > Network > check device health and site status. Compare with Splunk results.
(b) During a planned maintenance (device reboot), verify the device shows as unreachable in Splunk during the reboot window.
(c) Verify that dual-edge sites show "DEGRADED" (not "DOWN") when one edge is rebooted.

### Step 4 — Operationalize
Dashboard ("SD-WAN — Site Availability"):
- Row 1 — Single-value tiles: "Sites UP", "Sites DEGRADED", "Sites DOWN", "Unreachable devices".
- Row 2 — Map visualization: sites plotted on a map with status color coding.
- Row 3 — Down/degraded site table: site, tier, region, total edges, up edges, status.
- Row 4 — 7-day availability trending per site.

Alerting:
- Critical (Tier1 site DOWN): page NOC immediately.
- Critical (any site DOWN for > 5 minutes): page NOC.
- High (Tier1 site DEGRADED): alert — reduced redundancy at critical site.
- Warning (any site DEGRADED): alert for investigation.

Runbook:
1. **Site completely DOWN**: Check WAN circuits at the site (ISP status, physical layer). If all circuits are down, dispatch field technician. If circuits are up but edge devices unreachable, check edge device power and boot status.
2. **Site DEGRADED (one edge down)**: Check the specific device — reboot stuck, software crash, or hardware failure. The remaining edge handles traffic, but no redundancy.

### Step 5 — Troubleshooting

- **Device shows unreachable in Splunk but works in vManage** — Data polling interval mismatch. The TA may poll every 5 minutes; vManage shows real-time status. If the device recovered between polls, it may show unreachable in the last polled data. Check the `_time` field.

- **All devices unreachable** — Check vManage itself. If vManage is down, the TA can't poll API data. Monitor vManage cluster health (UC-5.5.18).

- **Site shows DOWN but users report connectivity** — The edge device may have lost its control connection to vManage (data plane still works). This means the device can't receive policy updates but existing tunnels continue. Check control connection status separately.

## SPL

```spl
index=sdwan sourcetype="cisco:sdwan:device"
| where reachability!="reachable"
| table _time site_id hostname system_ip reachability | sort -_time
```

## Visualization

Map (site locations with status), Table, Status grid.

## Known False Positives

Tunnels may renegotiate during ISP maintenance, BFD timer changes, planned controller upgrades, or policy pushes; short blips may look like failures when the business path is still acceptable.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
