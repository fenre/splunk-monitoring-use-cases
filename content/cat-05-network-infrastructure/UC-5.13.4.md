---
id: "5.13.4"
title: "Device Health by Category (Access/Distribution/Core/Router/Wireless)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.4 · Device Health by Category (Access/Distribution/Core/Router/Wireless)

## Description

Breaks down device health by network role category (access, distribution, core, router, wireless controller), revealing which infrastructure tier is most affected.

## Value

Enables targeted remediation by identifying which tier of the network architecture is contributing most to overall health degradation.

## Implementation

Complete UC-5.13.1 baseline ingestion first, then use this search for role-tier rollups. Ensure `deviceType` is populated in your events; if your naming differs, map values with a lookup. Pin the panel to a dashboard for monthly operations reviews and capacity planning.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:devicehealth (Catalyst Center /dna/intent/api/v1/device-health).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Complete UC-5.13.1 baseline ingestion first, then use this search for role-tier rollups. Ensure `deviceType` is populated in your events; if your naming differs, map values with a lookup. Pin the panel to a dashboard for monthly operations reviews and capacity planning.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" | stats avg(overallHealth) as avg_health count as device_count count(eval(overallHealth<50)) as unhealthy_count by deviceType | eval unhealthy_pct=round(unhealthy_count*100/device_count,1) | sort -unhealthy_pct
```

Understanding this SPL

**Device Health by Category (Access/Distribution/Core/Router/Wireless)** — Enables targeted remediation by identifying which tier of the network architecture is contributing most to overall health degradation.

Documented **Data sources**: index=catalyst, sourcetype cisco:dnac:devicehealth (Catalyst Center /dna/intent/api/v1/device-health). **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: catalyst; **sourcetype**: cisco:dnac:devicehealth. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• `stats` groups by `deviceType`, computing average `overallHealth`, device inventory counts, and how many report health under 50.
• `eval` turns raw counts into `unhealthy_pct` for comparable severity across different fleet sizes per tier.
• `sort -unhealthy_pct` ranks the worst tiers first so you can open UC-5.13.1 drilldowns for specific devices in that type.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (unhealthy_pct or avg_health by deviceType), table with device_count and unhealthy_count, pie chart of tier mix when combined with a fleet summary.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" | stats avg(overallHealth) as avg_health count as device_count count(eval(overallHealth<50)) as unhealthy_count by deviceType | eval unhealthy_pct=round(unhealthy_count*100/device_count,1) | sort -unhealthy_pct
```

## Visualization

Bar chart (unhealthy_pct or avg_health by deviceType), table with device_count and unhealthy_count, pie chart of tier mix when combined with a fleet summary.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
