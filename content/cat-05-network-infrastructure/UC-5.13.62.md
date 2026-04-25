<!-- AUTO-GENERATED from UC-5.13.62.json — DO NOT EDIT -->

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
• AP inventory from `cisco:dnac:devicehealth` (UC-5.13.60) to obtain AP names or MACs for the poll loop.
• Custom app (for example `TA_catalyst_wireless`) on the **Heavy Forwarder** with Catalyst credentials in the Splunk credential store.

Step 1 — API workflow (Catalyst Center)
1. `POST /dna/system/api/v1/auth/token` and reuse the token for 15–30 minutes when permitted.
2. For each managed AP, call `GET /dna/intent/api/v1/device-detail?searchBy=macAddress&identifier=<ap_mac>` (or a bulk health endpoint your release supports) and map: `apName`, `band`, `channel`, `channelUtilization`, `interferencePercentage`, `txPower`, `clientCount` into `cisco:dnac:wireless:rf`.
3. Emit one event per radio (apName, band, channel) when the response lists multiple interfaces.
4. Default **interval=900** seconds to respect Cisco rate limits; add backoff on HTTP 429.

```ini
[script://$SPLUNK_HOME/etc/apps/TA_catalyst_wireless/bin/collect_wireless_rf.py]
interval = 900
sourcetype = cisco:dnac:wireless:rf
index = catalyst
disabled = 0
```

**props.conf (optional):** `KV_MODE=json` or `SHOULD_LINEMERGE = false` for one JSON line per event.

Step 2 — Search

```spl
index=catalyst sourcetype="cisco:dnac:wireless:rf" | stats avg(channelUtilization) as avg_util avg(interferencePercentage) as avg_interference by apName, band, channel | eval util_status=case(avg_util>80,"Overloaded",avg_util>60,"High",1==1,"Normal") | sort -avg_util
```

Step 3 — Validate
Spot-check a few APs against **Catalyst Center > Wireless** RF or Assurance; align field percent scales (0–1 vs 0–100) in `eval` if your poller normalizes differently.

Step 4 — Operationalize
Alert on **sustained** Overloaded (for example 3 consecutive polls) to avoid one spike during a site survey. Pair with BSSID capacity planning, not a silent ticket storm.

Step 5 — Troubleshooting
• **Empty sourcetype:** script not running, bad token, or no AP list from step 0 — test one MAC by hand in Postman. **Gaps in time:** the loop may skip APs on timeout; batch smaller or add pagination.
• **All zeros:** wrong JSON path for utilization — re-open a raw event in Splunk and correct field names in the script.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:wireless:rf" | stats avg(channelUtilization) as avg_util avg(interferencePercentage) as avg_interference by apName, band, channel | eval util_status=case(avg_util>80,"Overloaded",avg_util>60,"High",1==1,"Normal") | sort -avg_util
```

## Visualization

Heatmap or table of `avg_util` by `apName` and `band`, bar chart of top overloaded channels, line chart of utilization over time.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
