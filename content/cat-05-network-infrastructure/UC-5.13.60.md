---
id: "5.13.60"
title: "Access Point Health and Availability"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.60 · Access Point Health and Availability

## Description

Monitors the health and availability of wireless access points using Catalyst Center device health data, filtered to AP device types.

## Value

Access points are the wireless user's connection to the network. AP failures immediately affect user connectivity. Proactive health monitoring prevents wireless outages.

## Implementation

This UC uses the standard `devicehealth` input (already enabled for UC-5.13.1). Access points appear as `deviceType="Unified AP"` or `"ACCESS_POINT"` in the device health data. No additional input is needed. Data path: Catalyst Center Intent API `GET /dna/intent/api/v1/device-health` → TA poller → `index=catalyst` `sourcetype=cisco:dnac:devicehealth`.

## Detailed Implementation

Prerequisites
• `Cisco Catalyst Add-on for Splunk` (7538) installed; `devicehealth` input enabled to `index=catalyst` (see UC-5.13.1).

Step 1 — Data source (standard TA path)
The Intent API `GET /dna/intent/api/v1/device-health` is polled by the TA; `sourcetype=cisco:dnac:devicehealth` includes wired and wireless devices. Filter in SPL using `deviceType` values Catalyst Center populates for APs, commonly `Unified AP` or `ACCESS_POINT` (verify a `| top deviceType` in your tenant).

Step 2 — Search

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" deviceType="Unified AP" OR deviceType="ACCESS_POINT" | stats latest(overallHealth) as health_score latest(reachabilityHealth) as reachability count as poll_count by deviceName, siteId | eval ap_status=case(reachability="Unreachable","Down",health_score<50,"Degraded",1==1,"Healthy") | sort health_score
```

Step 3 — Validate
Confirm AP models appear under the expected `deviceType` string; if your deployment uses a different value, add it to the OR list.

Step 4 — Operationalize
Dashboard for NOC; alert when `ap_status` is Down or Degraded above a threshold. No custom API polling required for this UC.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" deviceType="Unified AP" OR deviceType="ACCESS_POINT" | stats latest(overallHealth) as health_score latest(reachabilityHealth) as reachability count as poll_count by deviceName, siteId | eval ap_status=case(reachability="Unreachable","Down",health_score<50,"Degraded",1==1,"Healthy") | sort health_score
```

## Visualization

Table (deviceName, siteId, health_score, ap_status), single value of degraded or down APs, time chart of health_score.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
