---
id: "5.13.44"
title: "Client Roaming Event Analysis"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.44 · Client Roaming Event Analysis

## Description

Tracks wireless client roaming events to identify devices with excessive roaming or slow roam times that degrade real-time application performance.

## Value

Excessive or slow roaming disrupts voice and video calls. Identifying problematic clients and areas enables AP placement and configuration optimization.

## Implementation

Enable the `client` input in the Cisco Catalyst TA pointing to `index=catalyst`. The TA polls client detail data from the Catalyst Center Intent API every 60 minutes. Key fields: `macAddress`, `connectionType`, `ssid`, `roamDuration`, and any per-event roam count fields your TA maps into the data model.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:client (Catalyst Center client data; wireless fields roam_count or roaming metrics, ssid, macAddress, roamDuration).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable the `client` input in the Cisco Catalyst TA pointing to `index=catalyst`. The TA polls client detail data from the Catalyst Center Intent API every 60 minutes. Key fields: `macAddress`, `connectionType`, `ssid`, `roamDuration`, and any per-event roam count fields your TA maps into the data model.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:client" connectionType="WIRELESS" | stats count as roam_count avg(roamDuration) as avg_roam_ms by macAddress, ssid | where roam_count > 3 | eval avg_roam_ms=round(avg_roam_ms,0) | sort -avg_roam_ms | head 20
```

Understanding this SPL

**Client Roaming Event Analysis** — Excessive or slow roaming disrupts voice and video calls. Identifying problematic clients and areas enables AP placement and configuration optimization.

**Pipeline walkthrough**

• Limits results to wireless clients to study mobility behavior on Wi-Fi only.
• `stats` treats each event row as a roaming-related sample, counting events per `macAddress` and `ssid` and averaging `roamDuration` where the field is populated (adjust the search if the TA provides explicit roam event types).
• `where roam_count > 3` keeps endpoints with noisy roaming for investigation.
• `eval` rounds average roam time for display; `sort` and `head` return the 20 slowest average roamers.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions as required. Consider visualizations: Table (macAddress, ssid, roam_count, avg_roam_ms), time series of roam events if timechart added in a follow-on panel, top-N list of slowest roamers.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:client" connectionType="WIRELESS" | stats count as roam_count avg(roamDuration) as avg_roam_ms by macAddress, ssid | where roam_count > 3 | eval avg_roam_ms=round(avg_roam_ms,0) | sort -avg_roam_ms | head 20
```

## Visualization

Table (macAddress, ssid, roam_count, avg_roam_ms), time series of roam events if timechart added in a follow-on panel, top-N list of slowest roamers.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
