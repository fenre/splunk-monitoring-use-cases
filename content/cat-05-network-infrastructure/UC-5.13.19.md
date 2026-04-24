---
id: "5.13.19"
title: "Network Health by Site (Area/Building)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.19 · Network Health by Site (Area/Building)

## Description

Compares network health scores across Catalyst Center sites to identify locations with the worst performance and prioritize remediation.

## Value

Not all sites are equal. Comparing health across sites reveals which locations need immediate attention and which are performing well.

## Implementation

Build on UC-5.13.16 with per-site `siteId` in each network health event. If your feed is global only, re-pull site-level API metrics or merge with a site mapping from device health. Enrich the table with building names from a `lookup` for executive readability.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:networkhealth (Catalyst Center network health summary).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Build on UC-5.13.16 with per-site `siteId` in each network health event. If your feed is global only, re-pull site-level API metrics or merge with a site mapping from device health. Enrich the table with building names from a `lookup` for executive readability.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:networkhealth" | stats latest(healthScore) as health_score latest(goodCount) as good latest(badCount) as bad by siteId | eval total=good+bad | eval healthy_pct=round(good*100/total,1) | sort health_score | head 20
```

Understanding this SPL

**Network Health by Site (Area/Building)** — Not all sites are equal. Comparing health across sites reveals which locations need immediate attention and which are performing well.

Documented **Data sources**: index=catalyst, sourcetype cisco:dnac:networkhealth (Catalyst Center network health summary). **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: catalyst; **sourcetype**: cisco:dnac:networkhealth. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• `stats` groups by `siteId`, using `latest` on the score and count fields so the row reflects the most recent Catalyst Center view for that campus in the time window.
• `eval total` and `healthy_pct` translate raw good/bad counts to a percentage, assuming those counts partition the same population (adjust if the API ever reports partial inventory).
• `sort` ascending on `health_score` plus `head 20` shows the 20 neediest sites for targeted war-room work alongside UC-5.13.5/13 client-site trends.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (top 20 sites, health_score, good/bad, healthy_pct), bar chart, optional map of sites if geo is joined via CMDB export.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:networkhealth" | stats latest(healthScore) as health_score latest(goodCount) as good latest(badCount) as bad by siteId | eval total=good+bad | eval healthy_pct=round(good*100/total,1) | sort health_score | head 20
```

## Visualization

Table (top 20 sites, health_score, good/bad, healthy_pct), bar chart, optional map of sites if geo is joined via CMDB export.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
