<!-- AUTO-GENERATED from UC-5.13.60.json — DO NOT EDIT -->

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

Step 1 — Data source (Catalyst Center Assurance)
The Intent API `GET /dna/intent/api/v1/device-health` is polled by the TA; `sourcetype=cisco:dnac:devicehealth` includes wired and wireless devices. Filter in SPL with `deviceType` values your controller uses for access points, commonly `Unified AP` or `ACCESS_POINT` (run `| top deviceType` in your tenant).

Step 2 — Search

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" deviceType="Unified AP" OR deviceType="ACCESS_POINT" | stats latest(overallHealth) as health_score latest(reachabilityHealth) as reachability count as poll_count by deviceName, siteId | eval ap_status=case(reachability="Unreachable","Down",health_score<50,"Degraded",1==1,"Healthy") | sort health_score
```

Step 3 — Validate
• Confirm AP models sit under the expected `deviceType` string; add new strings to the `OR` list as Cisco adds platform families. Compare `health_score` to **Assurance > Device health** in Catalyst Center in the same poll window.

Step 4 — Operationalize
• NOC dashboard; alert on repeated **Down/Degraded** (for example 2+ consecutive bad polls) to avoid one-off flaps.

Step 5 — Troubleshooting
• **No APs in results:** `deviceType` filter too narrow — list raw values. **All healthy but users complain:** this UC is controller-reported; use wireless RF and client UCs for airtime and client experience.
• **Stale `poll_count`:** increase time range; confirm the `devicehealth` input interval in **Inputs** and no **ERROR** in `splunkd.log` for that stanza on the input host.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" deviceType="Unified AP" OR deviceType="ACCESS_POINT" | stats latest(overallHealth) as health_score latest(reachabilityHealth) as reachability count as poll_count by deviceName, siteId | eval ap_status=case(reachability="Unreachable","Down",health_score<50,"Degraded",1==1,"Healthy") | sort health_score
```

## Visualization

Table (deviceName, siteId, health_score, ap_status), single value of degraded or down APs, time chart of health_score.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
