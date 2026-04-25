<!-- AUTO-GENERATED from UC-5.13.75.json — DO NOT EDIT -->

---
id: "5.13.75"
title: "ITSI Service Modeling for Catalyst Center"
criticality: "high"
splunkPillar: "IT Operations"
---

# UC-5.13.75 · ITSI Service Modeling for Catalyst Center

## Description

Creates an ITSI service model for Catalyst Center infrastructure with KPIs derived from device health, client health, network health, and issue data, enabling service-centric monitoring and correlation.

## Value

ITSI service modeling transforms per-device/per-sourcetype monitoring into business-service health, enabling correlation across all Catalyst Center data streams and integration with IT service management.

## Implementation

Create an ITSI service for Catalyst Center with the following KPI base searches:

1. **Device Health KPI:** `index=catalyst sourcetype="cisco:dnac:devicehealth" | stats avg(overallHealth) as device_health count(eval(overallHealth<50)) as unhealthy_devices`
2. **Client Health KPI:** `index=catalyst sourcetype="cisco:dnac:clienthealth" | stats avg(scoreDetail{}.scoreCategory.value) as client_health`
3. **Network Health KPI:** `index=catalyst sourcetype="cisco:dnac:networkhealth" | stats latest(healthScore) as network_health`
4. **Issue Volume KPI:** `index=catalyst sourcetype="cisco:dnac:issue" (priority="P1" OR priority="P2") status!="RESOLVED" | stats count as critical_issues`
5. **Compliance KPI:** `index=catalyst sourcetype="cisco:dnac:compliance" complianceStatus="NON_COMPLIANT" | stats count as non_compliant_devices`

Configure entity types: Network Device (matched on `deviceName`), Site (matched on `siteId`).

Set thresholds: Green (device_health>75, critical_issues=0), Yellow (device_health 50-75 OR critical_issues 1-3), Red (device_health<50 OR critical_issues>3).

## Detailed Implementation

Prerequisites
• Splunk ITSI installed and licensed; service admin access.
• UC-5.13.1, 5.13.9, 5.13.16, 5.13.21 feeding the listed sourcetypes into `index=catalyst`.

Step 1 — Create the service
- **Configuration** → **Services** → **Service_template** or new service: name e.g. “Catalyst Center – Network Assurance”.
- Set **Importance** and **Team** per your org; link to business services (Campus Access, WAN Edge) as parent/child if modeled.

Step 2 — KPI base searches (paste into each KPI’s base search; set search mode to **Generic** or **Ad hoc** per ITSI version)
- **Device Health** — poll `cisco:dnac:devicehealth`; use `avg(overallHealth)` and unhealthy count as separate KPIs or one combined with thresholding on `device_health`.
- **Client Health** — `cisco:dnac:clienthealth` may store scores in nested JSON; if `scoreDetail{}.scoreCategory.value` does not parse in your version, replace with `spath` or a known numeric field from your sample event (e.g. `healthScore`).
- **Network Health** — `latest(healthScore)` from `cisco:dnac:networkhealth` per site or global as you prefer.
- **Critical issues** — filter `cisco:dnac:issue` for P1/P2 and not RESOLVED.
- **Compliance** — count `NON_COMPLIANT` from `cisco:dnac:compliance`.

Step 3 — Entities
- **Entity type** “Network Device”: field `deviceName` (or `deviceId` if unique). **Site:** `siteId` with optional lookup to human-readable site name.
- Enable **Entity rules** to auto-attach devices from search results.

Step 4 — Thresholding and episodes
- Map Green/Yellow/Red as in the short implementation; enable **Episode action** rules to page on Red and open ServiceNow when linked.

Step 5 — Validation SPL (ITSI summary)

```spl
| from datamodel:"ITSI_KPI_Summary" | where service_name="*Catalyst Center*" | stats latest(kpi_urgency) as urgency latest(alert_level) as alert_level by service_name, kpiid, itsi_kpi_id | sort -urgency
```

Note: Field names (`kpi_urgency`, `alert_level`) may vary by ITSI version — use **Lookup** on the ITSI Summary index or the content pack’s data model definition in your build.

## SPL

```spl
| from datamodel:"ITSI_KPI_Summary" | where service_name="*Catalyst Center*" | stats latest(kpi_urgency) as urgency latest(alert_level) as alert_level by service_name, kpiid, itsi_kpi_id | sort -urgency
```

## Visualization

ITSI Service Analyzer deep dive; glass table with KPI tiles; Episode Review for correlated episodes; optional deep link to Splunk dashboards for raw SPL drilldown.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
