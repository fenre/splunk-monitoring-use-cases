<!-- AUTO-GENERATED from UC-5.4.18.json — DO NOT EDIT -->

---
id: "5.4.18"
title: "Client Device Type Distribution and Compliance (Meraki MR)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.18 · Client Device Type Distribution and Compliance (Meraki MR)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Compliance

*We watch client device type distribution and compliance (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Tracks device types connecting to network for capacity planning, security policy enforcement, and support optimization.

## Value

Wireless operations teams monitor Meraki MR access point fleet health across all sites, tracking online/offline/alerting status to calculate site-level health percentages and detect outages.

## Implementation

Use API clients endpoint to retrieve device OS and type information. Aggregate across network.

## Detailed Implementation

### Prerequisites
- Meraki syslog or API events providing AP status and configuration change data. Data in `index=meraki` with `sourcetype=meraki:events` or `sourcetype=meraki:api:devices`. Key fields: `type` (device status change), `status` (online/offline/alerting), `ap_name`/`serial`, `productType`, `networkId`, `lastReportedAt`.

### Step 1 — Configure data collection
Verify AP status data:
```spl
index=meraki (sourcetype="meraki:api:devices" OR sourcetype="meraki:events") earliest=-4h
| where productType="wireless" OR match(model, "^MR")
| stats latest(status) as current_status latest(_time) as last_seen by ap_name, serial, network
| eval hours_since=round((now() - last_seen)/3600, 1)
```

### Step 2 — Create the search and alert

**Primary search — AP fleet health overview:**
```spl
index=meraki (sourcetype="meraki:api:devices" OR sourcetype="meraki:events") earliest=-1h
| where productType="wireless" OR match(model, "^MR")
| stats latest(status) as current_status latest(_time) as last_seen latest(lanIp) as mgmt_ip latest(model) as model by ap_name, serial, network
| eval hours_since=round((now() - last_seen)/3600, 1)
| eval ap_state=case(current_status="online" AND hours_since < 0.5, "HEALTHY", current_status="alerting", "ALERTING", current_status="offline" OR hours_since > 1, "OFFLINE", 1==1, "UNKNOWN")
| lookup meraki_networks.csv network OUTPUT site_name
| stats count(eval(ap_state="HEALTHY")) as healthy count(eval(ap_state="OFFLINE")) as offline count(eval(ap_state="ALERTING")) as alerting count as total by site_name
| eval health_pct=round(100*healthy/total, 1)
| sort health_pct
```

**AP uptime/downtime tracking:**
```spl
index=meraki (sourcetype="meraki:events" OR sourcetype="meraki:api:devices") earliest=-7d
| where (productType="wireless" OR match(model, "^MR")) AND match(type, "(?i)(up|down|online|offline)")
| eval event=if(match(type, "(?i)(up|online)"), "UP", "DOWN")
| stats count(eval(event="DOWN")) as outages earliest(_time) as first_seen latest(_time) as last_seen by ap_name, serial
| eval monitoring_days=round((last_seen - first_seen)/86400, 1)
| where outages > 0
| sort -outages
```

### Step 3 — Validate
(a) Unplug an AP (test environment) and verify it transitions to OFFLINE within 5-10 minutes.
(b) Compare AP status with Meraki Dashboard: Organization > Monitor > Overview.
(c) Verify all APs are accounted for by comparing the Splunk AP count with the Meraki inventory.

### Step 4 — Operationalize
Dashboard ("Meraki — AP Fleet Health"):
- Row 1 — Single-value: "Total APs", "Online", "Offline", "Fleet Health %".
- Row 2 — Per-site AP health summary.
- Row 3 — AP outage history (7 days).

Alerting:
- Critical (site health < 80%): multiple APs down — possible site-wide issue.
- Warning (AP offline > 1 hour): individual AP failure — dispatch tech.

### Step 5 — Troubleshooting

- **AP shows offline but physically powered** — Check PoE on the switch port, cable integrity, and AP LED status. In Meraki Dashboard: Wireless > Monitor > Access Points > select AP > Live tools > Ping.

- **Many APs offline at same site** — Check upstream switch/PoE budget, UPS status, or network path to Meraki cloud.

- **AP count doesn't match inventory** — Some APs may not be reporting to the API. Check licensing status in Meraki Dashboard.

## SPL

```spl
index=cisco_network sourcetype="meraki:api"
| stats count as device_count by os_type, device_family
| eval pct=round(device_count*100/sum(device_count), 2)
| sort - device_count
```

## Visualization

Pie chart of device types; bar chart by OS; treemap of device distribution; trend sparklines.

## Known False Positives

Wireless metrics move with user behavior, maintenance, and nearby RF; we tune alerts around change windows and known busy hours so normal days do not page the team.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
