---
id: "5.13.5"
title: "Device Health by Site Hierarchy"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.13.5 · Device Health by Site Hierarchy

## Description

Aggregates device health scores by Catalyst Center site hierarchy (area, building, floor), identifying locations with systemic network problems.

## Value

Pinpoints which physical locations have the worst network health, enabling site-specific remediation and resource allocation.

## Implementation

Prerequisite: UC-5.13.1 live with `siteId` and device health in `index=catalyst`. Enrich with a site name lookup if only IDs are present. Add this panel to regional operations dashboards; schedule a weekly report for the top 20 sites by unhealthy percentage.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:devicehealth (Catalyst Center /dna/intent/api/v1/device-health).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Prerequisite: UC-5.13.1 live with `siteId` and device health in `index=catalyst`. Enrich with a site name lookup if only IDs are present. Add this panel to regional operations dashboards; schedule a weekly report for the top 20 sites by unhealthy percentage.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" | stats avg(overallHealth) as avg_health count as device_count count(eval(overallHealth<50)) as unhealthy_count by siteId | eval unhealthy_pct=round(unhealthy_count*100/device_count,1) | sort -unhealthy_pct | head 20
```

Understanding this SPL

**Device Health by Site Hierarchy** — Pinpoints which physical locations have the worst network health, enabling site-specific remediation and resource allocation.

Documented **Data sources**: index=catalyst, sourcetype cisco:dnac:devicehealth (Catalyst Center /dna/intent/api/v1/device-health). **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: catalyst; **sourcetype**: cisco:dnac:devicehealth. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• `stats` groups all devices by `siteId` and summarizes average health, population size, and sub-threshold count per site.
• `eval` converts counts to `unhealthy_pct` to compare large campuses against small branches fairly.
• `head 20` after descending sort shows the most problematic sites for focused work orders and on-site support.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (top 20 sites with avg_health, counts, unhealthy_pct), bar chart, choropleth or tile map if you join geo metadata.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" | stats avg(overallHealth) as avg_health count as device_count count(eval(overallHealth<50)) as unhealthy_count by siteId | eval unhealthy_pct=round(unhealthy_count*100/device_count,1) | sort -unhealthy_pct | head 20
```

## Visualization

Table (top 20 sites with avg_health, counts, unhealthy_pct), bar chart, choropleth or tile map if you join geo metadata.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
