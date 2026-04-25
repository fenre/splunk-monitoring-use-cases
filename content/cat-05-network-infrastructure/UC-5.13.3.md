<!-- AUTO-GENERATED from UC-5.13.3.json — DO NOT EDIT -->

---
id: "5.13.3"
title: "Unhealthy Device Detection and Alerting"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.13.3 · Unhealthy Device Detection and Alerting

## Description

Detects devices with health scores below acceptable thresholds or unreachable status, triggering alerts for immediate investigation.

## Value

Ensures that degraded or failing devices are caught within minutes of health score degradation, reducing mean time to detect (MTTD) for network issues.

## Implementation

Install the Cisco Catalyst Add-on for Splunk (Splunkbase 7538) and ensure continuous ingestion of `cisco:dnac:devicehealth` to `index=catalyst`. Save this search as a scheduled alert (for example every 15 minutes) with actions to notify operations when results are non-zero. Tune thresholds if your environment uses stricter SLOs.

## Detailed Implementation

Prerequisites
• Cisco Catalyst Add-on (7538) with **devicehealth** writing `cisco:dnac:devicehealth` to your `catalyst` index (or equivalent).
• Agree whether **<50** matches your “unhealthy” definition (Catalyst Center **Poor** band) or whether you need stricter floors for certain `deviceType` or **site** tiers.
• Alert service account can read the index; webhook/ServiceNow/PagerDuty routing tested.
• Catalyst Center **2.3.5+**; Assurance health must be **licensed and active** for managed sites.
• See `docs/implementation-guide.md` for secure credential handling and outbound TLS to the controller.

Step 1 — Configure data collection
• **Intent API:** `GET /dna/intent/api/v1/device-health`.
• **TA input name:** **devicehealth** (Cisco Catalyst modular input); sourcetype `cisco:dnac:devicehealth`.
• **Default interval:** **900 seconds**; for MTTD goals, avoid stretching far beyond **15 minutes** unless you supplement with synthetic tests.
• **Volume:** alert result rows scale with **unhealthy devices**, not full inventory size.
• **Key fields for logic and tickets:** `overallHealth`, `reachabilityHealth`, `deviceName`, `managementIpAddress`, `deviceType`, `siteId`, and `last_seen` (from `latest(_time)` in the SPL).

Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" | where overallHealth < 50 OR reachabilityHealth="Unreachable" | stats latest(overallHealth) as health_score latest(reachabilityHealth) as reachability latest(_time) as last_seen by deviceName, managementIpAddress, deviceType, siteId | sort health_score
```

Understanding this SPL (thresholds, reachability, and paging policy)
• **`overallHealth < 50`** aligns with the common **“Poor”** side of the Catalyst Center scale; raise to **<70** for stricter operations or add a **lookup** of per-site SLAs.
• **`reachabilityHealth="Unreachable"`** should almost always **wake someone up** even if `overallHealth` is null—loss of management often precedes user impact.
• **Tuning:** exclude test sites with `where siteId!=...` or `where deviceType!="Sensor"` if those create noise; for **chronic** borderline devices, track them in a **Problem** record instead of endless pages.
• **`last_seen`** helps distinguish a **live** bad state from **stale** rows if replay or clock issues occur.

**Pipeline walkthrough**
• `where` filters low scores or unreachable state.
• `stats` collapses to one row per device with the latest measures and timestamp.
• `sort health_score` surfaces the worst devices first for the alert table or ticket body.

Step 3 — Validate
• Force or find a lab device in a bad state and confirm the search returns **non-zero** rows that **clear** when health recovers.
• Compare the result set to **Assurance** filtered to **Poor** / unreachable for the same window.
• Add a temporary `| where siteId="..."` to test throttling logic per site before going global.
• Confirm `last_seen` falls inside the alert search window so you do not page on ancient rows.

Step 4 — Operationalize (alerting)
• **Schedule:** **every 15 minutes** with time range **Last 15 minutes** (or **Last 20 minutes** with overlap) to align with a **900s** poll cadence.
• **Trigger:** **number of results > 0**; optionally split into two saved searches (reachability vs. score-only) if different teams own them.
• **Throttle / suppression:** recommend **one alert per device per 30–60 minutes** during incidents (Splunk alert **throttle** or a **lookup** of “already paged”); use a **global** throttle for **mass WAN** events so one ticket tracks the incident.
• **Actions:** ticket with `deviceName`, `siteId`, `managementIpAddress`, `health_score`, `reachability`, and a **Catalyst Center** device link; **page** only for `Unreachable` or **production** sites via a **lookup** table.
• **Recovery:** optional “cleared” notification is often handled in ITSM rather than Splunk duplicate alerts.

Step 5 — Troubleshooting
• **No fire on a known bad device:** verify the device appears in **Splunk** at all, the time range matches the poll, and **`overallHealth`** is really below the threshold in raw events.
• **Alert storm after an upgrade:** a software defect can report **0** for all devices—check Cisco **TA** / **Catalyst** release notes; temporarily adjust the threshold and open a case.
• **Duplicates across `deviceName`:** add **serial** or **instance** to the `by` clause when the field exists in your feed.
• **Reachability empty on some platforms:** document product-specific behavior in the runbook; do not assume APs and switches behave identically.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" | where overallHealth < 50 OR reachabilityHealth="Unreachable" | stats latest(overallHealth) as health_score latest(reachabilityHealth) as reachability latest(_time) as last_seen by deviceName, managementIpAddress, deviceType, siteId | sort health_score
```

## Visualization

Table of unhealthy devices, single value alert count, optional sparkline of alert frequency.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
