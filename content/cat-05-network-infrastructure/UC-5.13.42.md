---
id: "5.13.42"
title: "Client RSSI/SNR Quality Monitoring (Wireless)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.42 · Client RSSI/SNR Quality Monitoring (Wireless)

## Description

Monitors wireless client signal quality (RSSI and SNR) by SSID and location to identify areas with poor wireless coverage.

## Value

Poor RSSI and SNR directly cause slow connections, dropped sessions, and user complaints. Monitoring these metrics proactively finds coverage gaps.

## Implementation

Enable the `client` input in the Cisco Catalyst TA pointing to `index=catalyst`. The TA polls client detail data from the Catalyst Center Intent API every 60 minutes. Key fields: `macAddress`, `hostType`, `connectionType`, `ssid`, `vlanId`, `location`, `healthScore`, `rssi`, `snr`.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:client (Catalyst Center client data; wireless fields rssi, snr, ssid, location).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable the `client` input in the Cisco Catalyst TA pointing to `index=catalyst`. The TA polls client detail data from the Catalyst Center Intent API every 60 minutes. Key fields: `macAddress`, `hostType`, `connectionType`, `ssid`, `vlanId`, `location`, `healthScore`, `rssi`, `snr`.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:client" connectionType="WIRELESS" | stats avg(rssi) as avg_rssi avg(snr) as avg_snr count as client_count by ssid, location | eval signal_quality=case(avg_rssi>=-65,"Good",avg_rssi>=-75,"Fair",1==1,"Poor") | sort avg_rssi
```

Understanding this SPL

**Client RSSI/SNR Quality Monitoring (Wireless)** — Poor RSSI and SNR directly cause slow connections, dropped sessions, and user complaints. Monitoring these metrics proactively finds coverage gaps.

**Pipeline walkthrough**

• Narrows the feed to wireless clients with `connectionType="WIRELESS"` on the client sourcetype.
• `stats` averages `rssi` and `snr` and counts client events per `ssid` and `location`.
• `eval` maps average RSSI into Good, Fair, or Poor categories for quick interpretation.
• `sort avg_rssi` orders rows from strongest to weakest average signal to spotlight problem areas first.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions as required. Consider visualizations: Table (ssid, location, avg_rssi, avg_snr, signal_quality), heat map or geospatial chart if `location` is normalized, threshold-based alerts on Poor signal_quality.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:client" connectionType="WIRELESS" | stats avg(rssi) as avg_rssi avg(snr) as avg_snr count as client_count by ssid, location | eval signal_quality=case(avg_rssi>=-65,"Good",avg_rssi>=-75,"Fair",1==1,"Poor") | sort avg_rssi
```

## Visualization

Table (ssid, location, avg_rssi, avg_snr, signal_quality), heat map or geospatial chart if `location` is normalized, threshold-based alerts on Poor signal_quality.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
