<!-- AUTO-GENERATED from UC-5.13.18.json — DO NOT EDIT -->

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
• Cisco Catalyst Add-on for Splunk (Splunkbase 7538) with the **networkhealth** modular input writing sourcetype `cisco:dnac:networkhealth` to `index=catalyst` (this is the **Assurance summary** feed, not per-device `cisco:dnac:devicehealth`).
• UC-5.13.16 should already prove summary events with `healthScore`, `badCount`, and `totalCount` in Search before you page anyone.
• Agree on **thresholds** (example **<70** and **>5** unhealthy) with NOC; document exceptions for small fleets where one bad device is a high percentage but not an enterprise incident.
• `docs/implementation-guide.md` for credential storage and the forwarder/SH that runs the **networkhealth** input.

Step 1 — Configure data collection
• **Intent API:** `GET /dna/intent/api/v1/network-health` (Assurance top-level network summary).
• **TA input name:** **networkhealth**; sourcetype `cisco:dnac:networkhealth`, index `catalyst`.
• **Default interval:** **900 seconds**; align alert schedule with **poll cadence** so you do not alert on a partially ingested window.
• **Key fields:** `healthScore` (0–100), `badCount`, `totalCount`—confirm names match your TA version on a single raw event.

Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:networkhealth" | stats latest(healthScore) as health_score latest(badCount) as unhealthy_devices latest(totalCount) as total_devices by _time | where health_score < 70 OR unhealthy_devices > 5 | eval unhealthy_pct=round(unhealthy_devices*100/total_devices,1) | table _time health_score unhealthy_devices total_devices unhealthy_pct
```

Understanding this SPL (dual gate, time bucketing)
• **`where health_score < 70 OR unhealthy_devices > 5`** catches a **softer score** and a **count-based** “many devices are bad” pattern; tune **70** and **5** to your headcount and risk appetite.
• **`stats` by `_time`:** if multiple events share a timestamp, consider **`| dedup _time |`** first or collapse to the **last poll** in the window; otherwise you may get duplicate table rows in tests.
• **`unhealthy_pct`** helps ticket text; guard **`total_devices=0`** in a v2 to avoid division noise during Assurance initialization.

**Pipeline walkthrough**
• `latest()` picks the most recent Assured summary fields per time key.
• The filter and percent roll up a single operational story for a war-room view alongside **UC-5.13.1** and **UC-5.13.3** for device detail.

Step 3 — Validate
• Compare firing rows to **Catalyst Center > Assurance > Network health** for the same **controller scope** and **15–30 minute** window.
• During a **staged** incident (half the campuses upgraded), expect **unhealthy_devices** to rise—confirm the alert still matches leadership’s definition of “degraded.”
• Run **`| timechart count`** on `cisco:dnac:networkhealth` to catch silent ingest gaps before relying on the alert in production.

Step 4 — Operationalize (alerting)
• **Schedule:** every **15–30 minutes** with a **Last 30–45 minutes** window to overlap at least one **900s** poll and reduce edge misses.
• **Trigger:** number of results **> 0**; optional **throttle** on composite score bands so one long bridge outage does not re-page every 15 minutes—track one parent incident in ITSM instead.
• **Actions:** include **`unhealthy_pct`**, link to the **Catalyst** Assurance summary and drill to **device health** (UC-5.13.1) for device-level work queues.

Step 5 — Troubleshooting
• **No `cisco:dnac:networkhealth` data:** enable the **networkhealth** input, re-check **base URL** and **API role**, and confirm index routing.
• **All-clear in Splunk but UI is red:** wrong **Catalyst** instance in the add-on, **virtual domain** scope mismatch, or **stale** credentials—re-auth and compare raw JSON to the UI.
• **Alert never clears:** `totalCount` or **bad** counts may be **stale**; restart the modular input after TA upgrades and re-validate `fieldsummary` for numeric fields.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:networkhealth" | stats latest(healthScore) as health_score latest(badCount) as unhealthy_devices latest(totalCount) as total_devices by _time | where health_score < 70 OR unhealthy_devices > 5 | eval unhealthy_pct=round(unhealthy_devices*100/total_devices,1) | table _time health_score unhealthy_devices total_devices unhealthy_pct
```

## Visualization

Table of alert rows with unhealthy_pct, single value of worst recent health_score, link to a dynamic drilldown to UC-5.13.1/3.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
