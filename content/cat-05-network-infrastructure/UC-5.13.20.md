---
id: "5.13.20"
title: "Network Health Score Anomaly Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.20 · Network Health Score Anomaly Detection

## Description

Applies statistical anomaly detection to the network health score, identifying significant deviations from the historical baseline that may indicate emerging issues.

## Value

Fixed thresholds for network health may not account for normal variations. Anomaly detection catches unusual drops relative to your network's specific baseline.

## Implementation

Requires UC-5.13.16 and enough history for UC-5.13.17 to establish variance. The `eventstats` here runs across the whole result set, so use a long lookback and watch for missing hours that can inflate `stdev`. Consider seasonal baselines in a follow-on if the network’s score drifts with quarters or school terms.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:networkhealth (Catalyst Center network health summary).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Requires UC-5.13.16 and enough history for UC-5.13.17 to establish variance. The `eventstats` here runs across the whole result set, so use a long lookback and watch for missing hours that can inflate `stdev`. Consider seasonal baselines in a follow-on if the network’s score drifts with quarters or school terms.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:networkhealth" | bin _time span=1h | stats avg(healthScore) as health by _time | eventstats avg(health) as baseline stdev(health) as stdev_health | where health < (baseline - 2*stdev_health) AND stdev_health > 0 | eval deviation=round((baseline-health)/stdev_health,1) | sort -deviation
```

Understanding this SPL

**Network Health Score Anomaly Detection** — Fixed thresholds for network health may not account for normal variations. Anomaly detection catches unusual drops relative to your network's specific baseline.

Documented **Data sources**: index=catalyst, sourcetype cisco:dnac:networkhealth (Catalyst Center network health summary). **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: catalyst; **sourcetype**: cisco:dnac:networkhealth. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• `bin` and `stats` reduce raw feeds to a single hourly `health` series so each bucket has one `avg(healthScore)` for the site-wide or global number depending on your data shape.
• `eventstats` over all rows in the search time range computes a global `baseline` and `stdev` of that hourly line—interpret this as a same-window z-score test on the health curve.
• `where` flags hours under two-sigma, suppressing flat or near-zero stdev, and `eval deviation` makes the z-score legible; `sort` points incident commanders to the worst first, then they open UC-5.13.16/18 to confirm the human-facing threshold story.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of anomalous hours with deviation, overlay plot of `health` with a ribbon for baseline minus two sigma, combined alert card.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:networkhealth" | bin _time span=1h | stats avg(healthScore) as health by _time | eventstats avg(health) as baseline stdev(health) as stdev_health | where health < (baseline - 2*stdev_health) AND stdev_health > 0 | eval deviation=round((baseline-health)/stdev_health,1) | sort -deviation
```

## Visualization

Table of anomalous hours with deviation, overlay plot of `health` with a ribbon for baseline minus two sigma, combined alert card.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
