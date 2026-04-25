<!-- AUTO-GENERATED from UC-5.13.1.json — DO NOT EDIT -->

---
id: "5.13.1"
title: "Device Health Score Overview"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.13.1 · Device Health Score Overview

## Description

Provides a real-time overview of all network device health scores reported by Catalyst Center Assurance, enabling rapid identification of degraded or failing devices.

## Value

Gives network operations teams a single-pane view of device health across the entire managed infrastructure, enabling proactive identification of problems before users are affected.

## Implementation

Install the Cisco Catalyst Add-on for Splunk (Splunkbase 7538) and configure a Catalyst Center account. Enable the `devicehealth` input pointing to `index=catalyst`. The TA polls the Catalyst Center Intent API `/dna/intent/api/v1/device-health` every 15 minutes by default. Key fields include `overallHealth`, `reachabilityHealth`, `deviceName`, `deviceType`, and `siteId`.

## Detailed Implementation

Prerequisites
• Install and configure the Cisco Catalyst Add-on for Splunk (Splunkbase 7538).
• Data: `index=catalyst` and sourcetype `cisco:dnac:devicehealth` (Intent API device health).
• Verify Catalyst Center **2.3.5+** so `overallHealth` and related fields align with current Assurance health score APIs (older releases can differ; validate field names in a sample event).
• Service account: grant **`SUPER-ADMIN-ROLE`** or **`NETWORK-ADMIN-ROLE`** (read Assurance inventory and device health). Read-only or observer-style roles are often insufficient to poll some Assurance endpoints; confirm with your organization.
• For app install paths and modular input layout, see `docs/implementation-guide.md`

Step 1 — Configure data collection
• **Intent API polled:** `GET /dna/intent/api/v1/device-health` (Catalyst Center per managed device; the TA follows Cisco pagination and token auth).
• **TA input (inputs.conf / Inputs UI):** enable the **devicehealth** modular input in the Cisco Catalyst Add-on; set the destination index to `catalyst` and confirm assigned sourcetype `cisco:dnac:devicehealth` (the exact stanza name in `inputs.conf` matches the add-on’s modular input name—`devicehealth` in the **Data inputs** list).
• **Default interval:** **900 seconds (15 minutes)** in typical deployments; shorter intervals improve freshness but increase API load and the chance of throttling.
• **Volume:** expect roughly **one event per managed device per successful poll** (plus occasional pagination); scale with device inventory, not with traffic.
• **Key fields to validate in Search (raw / Interesting Fields):** `overallHealth` (0–100), `reachabilityHealth` (`Reachable`/`Unreachable`), `deviceName`, `deviceType`, `siteId`, `platformId`, `managementIpAddress`.

Step 2 — Create the search and alert
Run the following SPL in Search (save as a report, dashboard base, or ad hoc validation; pick a time range covering at least two poll cycles):

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" | stats latest(overallHealth) as health_score latest(reachabilityHealth) as reachability by deviceName, deviceType, siteId | eval health_status=case(health_score>=75,"Healthy",health_score>=50,"Fair",health_score>=25,"Poor",1==1,"Critical") | sort health_score
```

Understanding this SPL (why these thresholds, what to tune)

**Device Health Score Overview** — Surfaces the lowest-scoring devices first for operations triage.
• **Banding at 75 / 50 / 25** follows common Catalyst Center presentation where **below 50 is “Poor”** in Assurance. Tighten the bands for stricter SLOs (for example, **<70** for access switches in hospitals, or **<80** for data-center cores only).
• If `health_status` is too noisy, filter by `deviceType` or site, or require **two consecutive** bad polls using a **summary index** or **lookup of prior state** (this sample stays intentionally simple for crawl tier).
• `latest()` is the most recent sample per `deviceName, deviceType, siteId` key—add `managementIpAddress` to the `by` clause if hostnames are reused.

**Pipeline walkthrough**
• `stats` with `latest()` for `overallHealth` and `reachabilityHealth` per key.
• `eval` with `case()` labels **Healthy, Fair, Poor,** or **Critical** from the numeric `health_score`.
• `sort health_score` ascending—worst devices appear first in tables and drilldowns.

Step 3 — Validate (completeness and parity with Catalyst Center)
• Run `index=catalyst sourcetype="cisco:dnac:devicehealth" | stats count by deviceType` to confirm expected families (switches, routers, WLC, etc.) appear in expected proportions.
• Run `| stats dc(deviceName) as devices` and compare the count to **Catalyst Center > Inventory** and **Assurance > Device health** for the same site scope; investigate missing device types.
• Pick two known devices: compare `overallHealth` and `reachabilityHealth` in Splunk to the same device in **Assurance** within a single poll window.
• `| timechart count` or `| timechart count by deviceType` over 24h to catch silent gaps (flat line at zero).

Step 4 — Operationalize
• **Dashboard layout:** use this as a **top-row table** on a Catalyst / Assurance dashboard; add **single value** or **trellis** panels with `| stats count by health_status` beside it for a fleet mix view.
• **Time picker:** **Last 4 hours** or **Last 24 hours** for NOC; schedule a **weekly** PDF from a **Last 7 days** saved search for staff meetings.
• **Access:** limit the panel to NOC/NetEng roles; hostnames and IPs in results can be sensitive.
• **Runbook:** document remediation ownership by `siteId` or building and deep-link to Catalyst **Device 360** for each `deviceName`.

Step 5 — Troubleshooting
• **No `cisco:dnac:devicehealth` events:** verify the service account’s role (**SUPER-ADMIN-ROLE** or **NETWORK-ADMIN-ROLE**), correct **base URL** and credentials, and that the **devicehealth** input is **enabled** with no **ERROR** in `splunkd.log` on the input host.
• **All `overallHealth` NULL or zero:** confirm **Assurance** licensing and that Assurance analytics is **on** for the site; some platforms do not report until inventory sync completes.
• **Fewer devices than the Catalyst Center UI:** re-sync **inventory**; confirm the Splunk user’s **virtual domain / multi-cluster** scope; look for RMA/rename issues duplicating or hiding `deviceName`.
• **Stale or clustered `_time`:** check NTP on forwarders, proxy timeouts, and API throttling; consider **lowering** poll frequency or contact Cisco TAC if 429/5xx repeat.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" | stats latest(overallHealth) as health_score latest(reachabilityHealth) as reachability by deviceName, deviceType, siteId | eval health_status=case(health_score>=75,"Healthy",health_score>=50,"Fair",health_score>=25,"Poor",1==1,"Critical") | sort health_score
```

## Visualization

Table (device name, health score, status, type), Single value panels (healthy/unhealthy counts), Gauge (overall fleet health percentage).

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
