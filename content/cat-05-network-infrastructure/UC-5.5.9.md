<!-- AUTO-GENERATED from UC-5.5.9.json — DO NOT EDIT -->

---
id: "5.5.9"
title: "Application Routing Decisions"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.5.9 · Application Routing Decisions

## Description

Validates that SD-WAN policies are steering traffic correctly. Detects policy misconfigurations that route real-time traffic over suboptimal paths.

## Value

Validates that SD-WAN policies are steering traffic correctly. Detects policy misconfigurations that route real-time traffic over suboptimal paths.

## Implementation

Collect flow and app-route data from vManage. Verify voice/video uses MPLS, web traffic uses Internet. Alert when critical apps route over non-preferred transports.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), Cisco vManage API.
• Ensure the following data sources are available: `sourcetype=cisco:sdwan:approute`, `sourcetype=cisco:sdwan:flow`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect flow and app-route data from vManage. Verify voice/video uses MPLS, web traffic uses Internet. Alert when critical apps route over non-preferred transports.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="cisco:sdwan:flow"
| stats sum(octets) as bytes by app_name, local_color, remote_system_ip
| eval MB=round(bytes/1048576,1)
| sort -MB
| head 50
```

Understanding this SPL

**Application Routing Decisions** — Validates that SD-WAN policies are steering traffic correctly. Detects policy misconfigurations that route real-time traffic over suboptimal paths.

Documented **Data sources**: `sourcetype=cisco:sdwan:approute`, `sourcetype=cisco:sdwan:flow`. **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), Cisco vManage API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: cisco:sdwan:flow. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="cisco:sdwan:flow". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by app_name, local_color, remote_system_ip** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **MB** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Limits the number of rows with `head`.


Step 3 — Validate
In Cisco vManage, open the monitor or reporting screen that matches this signal (device, tunnel, interface, certificate, flow, or application route) and compare site names, device IPs, and KPIs to the Splunk results for the same range.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Sankey diagram (app → transport), Table (app, path, volume), Pie chart.

## SPL

```spl
index=network sourcetype="cisco:sdwan:flow"
| stats sum(octets) as bytes by app_name, local_color, remote_system_ip
| eval MB=round(bytes/1048576,1)
| sort -MB
| head 50
```

## CIM SPL

```spl
| tstats `summariesonly` sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.app span=1h
| where bytes>0
| sort -bytes
```

## Visualization

Sankey diagram (app → transport), Table (app, path, volume), Pie chart.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
