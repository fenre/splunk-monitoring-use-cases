<!-- AUTO-GENERATED from UC-5.2.35.json — DO NOT EDIT -->

---
id: "5.2.35"
title: "Cellular Modem Failover Activation and Usage (Meraki MX)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.35 · Cellular Modem Failover Activation and Usage (Meraki MX)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We mark when a site leans on cellular backup so you know who is on expensive paths and can fix the main line with less guesswork.*

---

## Description

Tracks cellular backup activation to monitor failover effectiveness and cellular data usage.

## Value

NOC teams track Meraki MX cellular modem failover activations and usage duration to monitor backup connectivity effectiveness and manage cellular data costs.

## Implementation

Ingest cellular failover events. Track data consumption.

## Detailed Implementation

### Prerequisites
* Meraki MX cellular modem status events. Data in `index=meraki` with `sourcetype=meraki:events` or `sourcetype=meraki:api:uplinks`. Key fields: `interface` (cellular), `status`, `provider`, `signalStat`, `connectionType` (3G/4G/LTE/5G).
* Meraki MX models with built-in cellular modem (MX67C, MX68CW) or USB cellular dongle. Cellular serves as last-resort WAN backup when WAN1 and WAN2 are both down.

### Step 1 — - Configure data collection
```
# Meraki Dashboard > Security & SD-WAN > SD-WAN & traffic shaping
# Uplink configuration: ensure cellular is configured as failover
# Syslog: enable Events category
```
Verify:
```spl
index=meraki (sourcetype="meraki:events" OR sourcetype="meraki:api:uplinks") earliest=-30d
| where match(_raw, "(?i)cellular|lte|3g|4g|5g|modem")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Cellular failover activation tracking:**
```spl
index=meraki (sourcetype="meraki:events" OR sourcetype="meraki:api:uplinks") earliest=-30d
| where match(_raw, "(?i)cellular") OR interface="cellular"
| eval device=coalesce(serial, host, deviceSerial)
| lookup meraki_networks.csv serial AS device OUTPUT network_name, site_name
| eval cell_status=case(match(_raw, "(?i)active|up|connected"), "ACTIVATED", match(_raw, "(?i)down|disconnect|standby"), "DEACTIVATED", 1==1, "STATUS_CHANGE")
| sort device, _time
| streamstats current=f last(_time) as prev_time last(cell_status) as prev_status by device
| eval duration_min=if(cell_status="DEACTIVATED" AND prev_status="ACTIVATED", round((_time - prev_time)/60, 1), null())
| stats count(eval(cell_status="ACTIVATED")) as activations sum(duration_min) as total_cell_min avg(duration_min) as avg_cell_min max(duration_min) as max_cell_min by device, network_name
| eval avg_cell_min=round(avg_cell_min, 1)
| eval total_cell_hours=round(total_cell_min/60, 1)
| eval severity=case(total_cell_hours > 24, "CRITICAL -- extended cellular usage (>24h in period)", activations > 10, "WARNING -- frequent cellular activations", activations > 0, "INFO -- cellular failover used", 1==1, "OK")
| where severity != "OK"
| sort severity, -total_cell_hours
```

### Step 3 — - Validate
(a) Dashboard: Security & SD-WAN > Uplink status -- verify cellular connection history.
(b) Check carrier data usage against Splunk-reported duration.
(c) Verify SIM activation and data plan limits.

### Step 4 — - Operationalize
Dashboard ("Meraki MX -- Cellular Failover"):
* Row 1 -- Single-value: "Cellular activations (30d)", "Total cellular hours", "Sites using cellular".
* Row 2 -- Cellular activation timeline.

Alert: Critical (cellular active > 4 hours continuously): investigate primary WAN circuits.

### Step 5 — - Troubleshooting

* **Extended cellular usage** -- Primary WAN circuits are down. Check ISP status, circuit provisioning, and physical connectivity. Cellular data costs can escalate rapidly.

* **Cellular signal quality poor** -- Check antenna placement, signal strength (RSSI/RSRP). Consider external antenna or signal booster for remote sites.

* **Data plan exceeded** -- Set up Meraki bandwidth limits for cellular uplink. Restrict to business-critical traffic only during cellular failover.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*cellular*" OR signature="*4G*" OR signature="*LTE*")
| stats count as cellular_events, sum(data_usage_mb) as total_cellular_data by event_type
| where total_cellular_data > 0
```

## Visualization

Cellular usage timeline; failover event table; data usage gauge.

## Known False Positives

Carriers, signal checks, and planned tests can make cellular backup logs busy without a site-down situation.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
