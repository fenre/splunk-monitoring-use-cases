---
id: "5.13.62"
title: "Wireless Channel Utilization and Interference"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.62 · Wireless Channel Utilization and Interference

## Description

Monitors wireless channel utilization and interference levels across access points and frequency bands to identify RF contention and capacity issues.

## Value

High channel utilization and interference directly cause poor wireless performance. Monitoring these metrics enables proactive RF optimization and AP density planning.

## Implementation

Channel utilization and interference data requires polling the Catalyst Center wireless-specific APIs.

API endpoints:
• `GET /dna/intent/api/v1/device-detail?searchBy=macAddress&identifier=<ap_mac>` — per-AP detail including RF metrics
• `GET /dna/intent/api/v2/data/device-health` — aggregated wireless metrics

Create a custom scripted input:

```ini
[script://$SPLUNK_HOME/etc/apps/TA_catalyst_wireless/bin/collect_wireless_rf.py]
interval = 900
sourcetype = cisco:dnac:wireless:rf
index = catalyst
disabled = 0
```

The script should poll AP detail for each access point and extract: `apName`, `band` (2.4GHz, 5GHz, 6GHz), `channel`, `channelUtilization`, `interferencePercentage`, `txPower`, `clientCount`. Use `POST /dna/system/api/v1/auth/token` to authenticate. Prefer discovering AP MACs from the TA’s `devicehealth` (UC-5.13.1) or inventory API to drive the per-AP loop. Recommended sourcetype: `cisco:dnac:wireless:rf`.

## Detailed Implementation

Prerequisites
• AP inventory from `cisco:dnac:devicehealth` (UC-5.13.60) to obtain AP names/MACs for iteration.
• Custom app `TA_catalyst_wireless` (or similar) on the forwarder with credentials in the Splunk credential store.

Step 1 — API workflow
1. `POST /dna/system/api/v1/auth/token` — store token for 15–30 minute reuse if supported.
2. For each managed AP, call `GET /dna/intent/api/v1/device-detail?searchBy=macAddress&identifier=<ap_mac>` (or bulk device-health v2) and map JSON fields to: `apName`, `band`, `channel`, `channelUtilization`, `interferencePercentage`, `txPower`, `clientCount`.
3. If the API returns multiple radios, emit one event per (apName, band, channel) for granular SPL.
4. Throttle: `interval=900` limits API load; increase carefully per Cisco rate limits.

```ini
[script://$SPLUNK_HOME/etc/apps/TA_catalyst_wireless/bin/collect_wireless_rf.py]
interval = 900
sourcetype = cisco:dnac:wireless:rf
index = catalyst
disabled = 0
```

**props.conf (optional):** `KV_MODE=json` or `SHOULD_LINEMERGE = false` if you emit one JSON object per line.

Step 2 — Search

```spl
index=catalyst sourcetype="cisco:dnac:wireless:rf" | stats avg(channelUtilization) as avg_util avg(interferencePercentage) as avg_interference by apName, band, channel | eval util_status=case(avg_util>80,"Overloaded",avg_util>60,"High",1==1,"Normal") | sort -avg_util
```

Step 3 — Validate
Spot-check against Catalyst Center wireless assurance / RF view for a single AP and band.

Step 4 — Operationalize
Capacity planning: alert when `util_status=Overloaded` for sustained windows; work with wireless engineers on channel/power changes or extra APs.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:wireless:rf" | stats avg(channelUtilization) as avg_util avg(interferencePercentage) as avg_interference by apName, band, channel | eval util_status=case(avg_util>80,"Overloaded",avg_util>60,"High",1==1,"Normal") | sort -avg_util
```

## Visualization

Heatmap or table of `avg_util` by `apName` and `band`, bar chart of top overloaded channels, line chart of utilization over time.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
