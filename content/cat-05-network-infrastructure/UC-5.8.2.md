<!-- AUTO-GENERATED from UC-5.8.2.json — DO NOT EDIT -->

---
id: "5.8.2"
title: "Meraki Organization Monitoring"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.8.2 · Meraki Organization Monitoring

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We help you see when Meraki gear goes offline or unhealthy across sites so the team can fix it before everyone loses the network in that building.*

---

## Description

Tracks Meraki device status across all networks and organizations from a single pane.

## Value

Network operations teams maintain a unified view of Meraki device health across all organizations and networks, detecting site outages (offline MX), degraded coverage (offline APs), and alerting conditions with offline duration tracking.

## Implementation

Configure Meraki API integration (API key + org ID). Poll device statuses. Forward syslog for events. Dashboard showing organization-wide health.

## Detailed Implementation

### Prerequisites
- Cisco Meraki Add-on for Splunk (Splunk_TA_cisco_meraki, Splunkbase 5580) installed and configured with Meraki Dashboard API key and organization ID. The TA polls the Meraki Dashboard API for device status, network health, and organization-level events.
- Data in `index=meraki` (or `index=network`) with sourcetypes: `meraki:api:devices` (device inventory/status), `meraki:api:organization` (org-level data), `meraki:events` (event log via syslog/API). Key fields: `network` (network name), `serial`, `model`, `status` (online/offline/alerting/dormant), `lanIp`, `publicIp`, `tags`, `firmware`, `name` (device name).
- Additionally, Meraki devices can forward syslog directly to a Splunk syslog receiver. Syslog data arrives as `sourcetype=meraki` or `meraki:events` and provides real-time event data (client connections, security events, URL filtering).
- Build `meraki_networks.csv` lookup: `network,site_name,address,tier,network_type` (e.g., `Branch-Chicago,Chicago Office,123 Main St,Tier2,combined`). Build `meraki_device_roles.csv` lookup: `model_prefix,device_type` (e.g., `MX,security_appliance`, `MR,wireless_ap`, `MS,switch`, `MV,camera`, `MT,sensor`).

### Step 1 — Configure data collection
Verify device status data:
```spl
index=meraki sourcetype="meraki:api:devices" earliest=-1h
| stats count by status
```
Healthy output: majority "online", some "offline" (expected for spare/staging devices), and few "alerting". If no data: check API key permissions (Organization > Full), verify org ID, check `_internal` for TA errors.

Verify event log data:
```spl
index=meraki (sourcetype="meraki:events" OR sourcetype="meraki") earliest=-1h
| stats count by sourcetype, network
```

### Step 2 — Create the search and alert

**Primary search — Organization-wide device health:**
```spl
index=meraki sourcetype="meraki:api:devices" earliest=-15m
| dedup serial sortby -_time
| eval device_type=case(match(model, "^MX"), "Security Appliance", match(model, "^MR"), "Wireless AP", match(model, "^MS"), "Switch", match(model, "^MV"), "Camera", match(model, "^MT"), "Sensor", 1==1, "Other")
| stats count as total count(eval(status="online")) as online count(eval(status="offline")) as offline count(eval(status="alerting")) as alerting by network, device_type
| eval health_pct=round(100*online/total, 1)
| lookup meraki_networks.csv network OUTPUT site_name tier
| eval site_label=if(isnotnull(site_name), site_name, network)
| where offline > 0 OR alerting > 0
| sort tier, -offline
```

#### Understanding this SPL: Meraki devices report status through the Dashboard API: "online" (functioning normally), "offline" (unreachable — power, circuit, or hardware issue), "alerting" (online but with a problem — high utilization, connectivity issue), "dormant" (configured but never connected). Grouping by `device_type` helps prioritize: an offline MX (security appliance/gateway) means the entire site may be down; an offline MR (wireless AP) affects only a coverage area.

**Site availability summary:**
```spl
index=meraki sourcetype="meraki:api:devices" earliest=-15m
| dedup serial sortby -_time
| where match(model, "^MX")
| stats count(eval(status="online")) as mx_online count(eval(status!="online")) as mx_down by network
| eval site_status=case(mx_down > 0 AND mx_online=0, "SITE_DOWN", mx_down > 0, "DEGRADED", 1==1, "UP")
| lookup meraki_networks.csv network OUTPUT site_name tier
| where site_status!="UP"
| sort site_status, tier
```

**Device offline duration tracking:**
```spl
index=meraki sourcetype="meraki:api:devices" status="offline" earliest=-24h
| stats earliest(_time) as first_offline latest(_time) as last_seen by serial, name, model, network
| eval offline_hours=round((now() - first_offline)/3600, 1)
| lookup meraki_networks.csv network OUTPUT site_name tier
| where offline_hours > 1
| sort -offline_hours
```

### Step 3 — Validate
(a) In Meraki Dashboard: Organization > Monitor > Overview. Compare online/offline device counts per network with Splunk results.
(b) Power-cycle a test device and verify the status change appears in Splunk within the polling interval (typically 5-15 minutes).
(c) Verify network mapping: spot-check 10 networks in the `meraki_networks.csv` lookup against Meraki Dashboard.

### Step 4 — Operationalize
Dashboard ("Meraki — Organization Health"):
- Row 1 — Single-value tiles: "Devices online", "Devices offline", "Devices alerting", "Site health %".
- Row 2 — Network status table: site, device types, online/offline/alerting counts, health %.
- Row 3 — Site availability: MX-based site status (UP/DEGRADED/DOWN).
- Row 4 — Offline device detail: device name, model, network, offline duration.

Alerting:
- Critical (MX offline at any site — site potentially down): page NOC.
- High (> 3 devices offline at a single site): investigate circuit or power issue.
- Warning (any device offline > 1 hour): ticket for investigation.

### Step 5 — Troubleshooting

- **All devices show "offline"** — Check Meraki cloud connectivity. If the Meraki Dashboard itself is down, all devices report offline via API. Check status.meraki.com.

- **Device status oscillates between online/offline** — Usually caused by intermittent uplink issues. Check the Meraki Dashboard event log for the specific device. If the MX has cellular backup, check if it's failing over.

- **Syslog data arrives but API data doesn't** — API and syslog are independent data paths. API issues (invalid key, org ID, rate limits) don't affect syslog. Check TA configuration separately from syslog receiver configuration.

## SPL

```spl
index=network sourcetype="meraki:api"
| stats count by network, status | eval is_offline=if(status="offline",1,0)
| where is_offline > 0
```

## Visualization

Map (device locations), Table, Status grid, Single value (offline count).

## Known False Positives

Meraki maintenance windows, cellular backup failovers, and brief cloud API hiccups can look like outages; match counts to the dashboard map before paging.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
