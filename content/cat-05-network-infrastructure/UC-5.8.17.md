<!-- AUTO-GENERATED from UC-5.8.17.json — DO NOT EDIT -->

---
id: "5.8.17"
title: "Network Health Score Aggregation and Executive Reporting (Meraki)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.8.17 · Network Health Score Aggregation and Executive Reporting (Meraki)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We roll Meraki health into a simple view leaders can read, not just a wall of device lists.*

---

## Description

Provides high-level network health metric for executive dashboards and trend reporting.

## Value

Network operations teams generate composite network health scores across all Meraki sites for executive reporting, combining device availability and security posture into a single, actionable metric per site.

## Implementation

Aggregate device health scores. Calculate composite network score.

## Detailed Implementation

### Prerequisites
- Meraki Dashboard API providing device status, network health, and performance metrics via Splunk_TA_cisco_meraki. Data in `index=meraki` with sourcetypes: `meraki:api:devices` (device status), `meraki:api:networks` (network info), `meraki:events` (event log).
- A network health score aggregates multiple signals: device availability, client connectivity rates, WAN uplink status, wireless air quality, and security event levels. This is a composite score calculated in Splunk from available Meraki data.

### Step 1 — Configure data collection
Verify multi-signal data availability:
```spl
index=meraki earliest=-1h
| stats count by sourcetype
```
You should see events from device, network, and event sourcetypes.

### Step 2 — Create the search and alert

**Primary search — Composite network health score:**
```spl
index=meraki sourcetype="meraki:api:devices" earliest=-15m
| dedup serial sortby -_time
| eval is_online=if(status="online", 1, 0)
| stats count as total_devices sum(is_online) as online_devices by network
| eval device_health=round(100*online_devices/total_devices, 1)
| join type=left network [search index=meraki sourcetype="meraki:events" earliest=-1h | where match(_raw, "(?i)(security|threat|intrusion|malware)") | stats count as security_events by network]
| eval security_events=coalesce(security_events, 0)
| eval security_score=case(security_events > 50, 50, security_events > 10, 75, security_events > 0, 90, 1==1, 100)
| eval composite_health=round((device_health * 0.6) + (security_score * 0.4), 1)
| lookup meraki_networks.csv network OUTPUT site_name tier
| eval health_rating=case(composite_health > 90, "Excellent", composite_health > 75, "Good", composite_health > 60, "Fair", 1==1, "Poor")
| sort composite_health
```

#### Understanding this SPL: Executive reporting requires a single number per site/network. The composite health score weights device availability (60%) and security posture (40%). A site with all devices online but many security events scores lower than a site with one offline device and no security events — this reflects the reality that security incidents can be more impactful than a single device failure.

**Executive summary dashboard data:**
```spl
index=meraki sourcetype="meraki:api:devices" earliest=-15m
| dedup serial sortby -_time
| eval device_type=case(match(model, "^MX"), "Security", match(model, "^MR"), "Wireless", match(model, "^MS"), "Switching", 1==1, "Other")
| stats count as total count(eval(status="online")) as online by device_type
| eval health_pct=round(100*online/total, 1)
```

**Weekly health trend:**
```spl
index=meraki sourcetype="meraki:api:devices" earliest=-30d
| bin _time span=1d
| eval is_online=if(status="online", 1, 0)
| stats count as total sum(is_online) as online by _time
| eval daily_health=round(100*online/total, 1)
| timechart span=1d avg(daily_health) as "Network Health %"
```

### Step 3 — Validate
(a) Compare device availability percentages with Meraki Dashboard: Organization > Overview.
(b) Verify the composite score reflects actual network state: take down a device and confirm the score decreases appropriately.
(c) Review the weighting factors (60% device, 40% security) with stakeholders — adjust based on organizational priorities.

### Step 4 — Operationalize
Dashboard ("Meraki Executive Summary"):
- Row 1 — Single-value: "Overall Network Health Score" (large, colored by rating).
- Row 2 — Health score by network/site: table with site, health score, rating, device health, security score.
- Row 3 — Device availability by type: security, wireless, switching.
- Row 4 — 30-day health trend line.

Alerting:
- Weekly (scheduled report): executive health summary emailed to leadership.
- Warning (any network health score < 60): attention needed for that site.

### Step 5 — Troubleshooting

- **Health score seems too low** — Check the security event component. A spike in benign security events (e.g., content filtering blocks) can drag down the score. Adjust the security weighting or filter out informational security events.

- **Health score 100% but users report issues** — Device online/offline is a coarse metric. A device can be "online" but performing poorly. For more granularity, add client connection success rate and latency metrics to the composite score.

- **Missing networks** — Some networks may not have any devices (staging networks). Filter out empty networks from the report.

## SPL

```spl
index=cisco_network sourcetype="meraki:api"
| stats avg(health_score) as device_health, count(eval(status="offline")) as offline_count by network_id
| eval network_health=round(device_health - (offline_count*5), 2)
| eval health_status=case(network_health >= 85, "Healthy", network_health >= 70, "Degraded", 1=1, "Critical")
```

## Visualization

Network health gauge; health trend sparkline; status KPI dashboard.

## Known False Positives

Aggregates hide a single bad site; always drill to site-level before exec reporting drives the wrong project priority.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
