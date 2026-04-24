---
id: "5.13.18"
title: "Network Health Degradation Alerting"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.13.18 · Network Health Degradation Alerting

## Description

Triggers alerts when the network health score drops below acceptable thresholds or when the count of unhealthy devices exceeds limits.

## Value

A network health score below 70 typically indicates multiple concurrent issues. Alerting on this composite metric catches systemic problems that individual device alerts might miss.

## Implementation

Requires UC-5.13.16 running so composite scores and counts are flowing. Save as a 15–30 minute alert with a non-zero trigger. Tune 70/5/percent math for your org; some campuses are noisier and need higher bad-count headroom, while others are stricter on percentage.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:networkhealth (Catalyst Center network health summary).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Requires UC-5.13.16 running so composite scores and counts are flowing. Save as a 15–30 minute alert with a non-zero trigger. Tune 70/5/percent math for your org; some campuses are noisier and need higher bad-count headroom, while others are stricter on percentage.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:networkhealth" | stats latest(healthScore) as health_score latest(badCount) as unhealthy_devices latest(totalCount) as total_devices by _time | where health_score < 70 OR unhealthy_devices > 5 | eval unhealthy_pct=round(unhealthy_devices*100/total_devices,1) | table _time health_score unhealthy_devices total_devices unhealthy_pct
```

Understanding this SPL

**Network Health Degradation Alerting** — A network health score below 70 typically indicates multiple concurrent issues. Alerting on this composite metric catches systemic problems that individual device alerts might miss.

Documented **Data sources**: index=catalyst, sourcetype cisco:dnac:networkhealth (Catalyst Center network health summary). **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: catalyst; **sourcetype**: cisco:dnac:networkhealth. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• `stats` by `_time` assembles a whole-network snapshot: composite `healthScore`, the bad count, and total managed inventory size from the last samples in the window.
• `where` enforces a dual test on absolute score and absolute bad count so a soft score alone cannot miss a many-device incident that still sits numerically in the 70s in small fleets.
• `eval` plus `table` show `unhealthy_pct` for SLO text in tickets and to compare incident severity to UC-5.13.1 device-level work queues.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of alert rows with unhealthy_pct, single value of worst recent health_score, link to a dynamic drilldown to UC-5.13.1/3.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:networkhealth" | stats latest(healthScore) as health_score latest(badCount) as unhealthy_devices latest(totalCount) as total_devices by _time | where health_score < 70 OR unhealthy_devices > 5 | eval unhealthy_pct=round(unhealthy_devices*100/total_devices,1) | table _time health_score unhealthy_devices total_devices unhealthy_pct
```

## Visualization

Table of alert rows with unhealthy_pct, single value of worst recent health_score, link to a dynamic drilldown to UC-5.13.1/3.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
