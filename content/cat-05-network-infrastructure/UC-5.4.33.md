<!-- AUTO-GENERATED from UC-5.4.33.json — DO NOT EDIT -->

---
id: "5.4.33"
title: "AP Health and Radio Status Monitoring (HPE Aruba)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.4.33 · AP Health and Radio Status Monitoring (HPE Aruba)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We watch ap health and radio status monitoring (hpe aruba) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Aruba APs report radio status (up/down per band), CPU/memory utilization, and uptime via controller syslog and Aruba Central API. A radio stuck in "down" state creates a coverage hole on that band. Monitor per-radio health across the fleet to proactively address failing hardware and capacity issues.

## Value

Network operations teams monitor Aruba AP radio status, CPU, and memory per band and AP group to detect down radios creating coverage gaps and overloaded APs before users report connectivity issues.

## Implementation

Forward Mobility Controller / gateway syslog to Splunk with the Aruba TA (field aliases for `ap_name`, per-radio operational state, CPU/memory, uptime). Optionally poll Aruba Central for AP inventory and merge with syslog for sites without local controllers. Alert on any radio not `up`, sustained high CPU/memory, or APs with abnormal uptime resets.

## Detailed Implementation

### Prerequisites
- Aruba Networks Add-on for Splunk (Splunkbase 4668) installed, configured to receive syslog from Aruba Mobility Controllers (MC) or Aruba Instant APs. Data in `index=network` with `sourcetype=aruba:syslog`. Key fields from TA: `ap_name`, `ap_mac`, `radio_oper_status`, `radio_band` (2.4 GHz / 5 GHz / 6 GHz), `cpu_utilization_pct`, `memory_utilization_pct`, `uptime_seconds`, `ap_group`, `controller_name`.
- Optionally, poll Aruba Central REST API (`/monitoring/v2/aps`) for AP inventory, health scores, and firmware data. Ingest via HEC as `sourcetype=aruba:central`.
- Create `aruba_ap_inventory.csv` lookup: `ap_name`, `ap_mac`, `model`, `site`, `building`, `floor`, `ap_group`, `expected_bands` (e.g., "2.4,5" or "2.4,5,6E").

### Step 1 — Configure data collection
Configure syslog on Aruba Mobility Controller:
```
(Aruba-MC) # logging <splunk_syslog_ip> severity informational facility local0
(Aruba-MC) # logging level system informational
(Aruba-MC) # logging level wireless informational
```
For Aruba Instant, under Configuration > System > General > Syslog server, add the Splunk syslog receiver IP and set severity to Informational.

Verify data in Splunk:
```spl
index=network sourcetype="aruba:syslog" earliest=-4h
| where isnotnull(ap_name) OR isnotnull(ap_mac)
| stats count by ap_name, controller_name
| head 20
```

### Step 2 — Create the search and alert

**Primary search — AP radio health with coverage gap detection:**
```spl
index=network sourcetype="aruba:syslog" earliest=-15m
| eval ap=coalesce(ap_name, caller_ap_name, device_name, ap_mac)
| eval radio_st=coalesce(radio_oper_status, radio_status, oper_status)
| eval band=coalesce(radio_band, freq_band, band)
| bin _time span=5m
| stats latest(radio_st) as radio_state latest(cpu_utilization_pct) as cpu_pct latest(memory_utilization_pct) as mem_pct latest(uptime_seconds) as uptime_sec by ap, band, ap_group, controller_name
| lookup aruba_ap_inventory.csv ap_name as ap OUTPUT site, building, floor, model
| eval uptime_days=round(uptime_sec/86400, 1)
| eval issue=mvappend(if(like(lower(radio_state), "%down%") OR like(lower(radio_state), "%off%"), "Radio DOWN on ".band, null()), if(cpu_pct > 85, "CPU ".cpu_pct."%", null()), if(mem_pct > 85, "Memory ".mem_pct."%", null()), if(uptime_days < 0.01, "Just rebooted", null()))
| where isnotnull(issue)
| eval severity=case(like(lower(radio_state), "%down%"), "HIGH", cpu_pct > 95 OR mem_pct > 95, "HIGH", cpu_pct > 85 OR mem_pct > 85, "MEDIUM", 1==1, "LOW")
| table ap, model, site, building, floor, band, radio_state, cpu_pct, mem_pct, uptime_days, issue, severity
| sort severity, ap, band
```

**Fleet health summary:**
```spl
index=network sourcetype="aruba:syslog" earliest=-15m
| eval ap=coalesce(ap_name, caller_ap_name, device_name, ap_mac)
| eval radio_st=coalesce(radio_oper_status, radio_status, oper_status)
| stats latest(radio_st) as radio_state by ap, ap_group
| eval is_healthy=if(NOT (like(lower(radio_state), "%down%") OR like(lower(radio_state), "%off%")), 1, 0)
| stats sum(is_healthy) as healthy count as total by ap_group
| eval health_pct=round(100*healthy/total, 1)
| sort health_pct
```

### Step 3 — Validate
(a) Identify an AP with a known issue (e.g., disabled radio) in the Aruba controller: `show ap radio-summary ap-name <AP>`. Verify it appears in the search with "Radio DOWN".
(b) Check CPU/memory: `show ap debug system-status ap-name <AP>` — compare values with Splunk.
(c) Compare AP count in Splunk with `show ap database` on the controller. If APs are missing from Splunk, check syslog forwarding configuration.

### Step 4 — Operationalize
Dashboard ("Aruba — AP Fleet Health"):
- Row 1 — Single-value tiles: "Total APs", "Radios DOWN", "High CPU APs", "Fleet Health %".
- Row 2 — Unhealthy AP detail table with site/building/floor context and specific issue.
- Row 3 — Per-AP-group health summary.

Alerting:
- High (radio DOWN for > 10 minutes): coverage gap — investigate AP hardware or config.
- Warning (CPU > 90% sustained > 15 min): AP overloaded — possible DDoS or excessive clients.
- Info (AP rebooted / uptime < 1 day): track stability issues.

### Step 5 — Troubleshooting

- **Radio shows DOWN but AP is online** — The radio may be admin-disabled. Check: `show ap radio-summary ap-name <AP>`. If admin state is "Disabled", this is intentional (e.g., 2.4 GHz disabled for band steering). Exclude admin-disabled radios from alerts.

- **High CPU on specific AP model** — Some older AP models (AP-303, AP-315) have limited CPU for high client counts. Check client count: `show ap association ap-name <AP>`. Consider upgrading to AP-505/AP-535.

- **No syslog from APs** — Aruba APs send logs to the Mobility Controller, which then forwards via syslog. Ensure syslog is configured on the MC, not on individual APs. For Aruba Instant, each AP sends syslog directly.

## SPL

```spl
index=network sourcetype="aruba:syslog"
| eval ap=coalesce(ap_name, caller_ap_name, device_name, ap_mac)
| eval radio_st=coalesce(radio_oper_status, radio_status, oper_status)
| eval band=coalesce(radio_band, freq_band, band)
| bin _time span=5m
| stats latest(radio_st) as radio_state, latest(cpu_utilization_pct) as cpu_pct, latest(memory_utilization_pct) as mem_pct, latest(uptime_seconds) as uptime_sec by ap, band, ap_group, controller_name
| where like(lower(radio_state), "%down%") OR like(lower(radio_state), "%off%") OR cpu_pct>85 OR mem_pct>85
| sort ap_group ap band
```

## Visualization

Table (AP, band, radio state, CPU, memory, uptime), Single value (APs with down radios), Timechart (unhealthy AP count), Map or site breakdown (by `ap_group` / zone).

## Known False Positives

Wireless metrics move with user behavior, maintenance, and nearby RF; we tune alerts around change windows and known busy hours so normal days do not page the team.

## References

- [Splunkbase app 4668](https://splunkbase.splunk.com/app/4668)
