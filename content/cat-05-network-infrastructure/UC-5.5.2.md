<!-- AUTO-GENERATED from UC-5.5.2.json — DO NOT EDIT -->

---
id: "5.5.2"
title: "Site Availability"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.5.2 · Site Availability

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We keep an eye on how our wide-area links and SD-WAN paths are behaving so we spot a bad circuit or policy issue before branch users lose voice, video, or critical apps.*

---

## Description

Edge device offline = remote site disconnected from the network.

## Value

Edge device offline = remote site disconnected from the network.

## Implementation

Poll vManage device inventory API. Alert when any edge device becomes unreachable. Include site name and location.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API.
- Ensure the following data sources are available: vManage device status.
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
Poll vManage device inventory API. Alert when any edge device becomes unreachable. Include site name and location.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=sdwan sourcetype="cisco:sdwan:device"
| where reachability!="reachable"
| table _time site_id hostname system_ip reachability | sort -_time
```

#### Understanding this SPL

**Site Availability** — Edge device offline = remote site disconnected from the network.

Documented **Data sources**: vManage device status. **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: sdwan; **sourcetype**: cisco:sdwan:device. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

- Scopes the data: index=sdwan, sourcetype="cisco:sdwan:device". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Filters the current rows with `where reachability!="reachable"` — typically the threshold or rule expression for this monitoring goal.
- Pipeline stage (see **Site Availability**): table _time site_id hostname system_ip reachability
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
In Cisco vManage, open the monitor or reporting screen that matches this signal (device, tunnel, interface, certificate, flow, or application route) and compare site names, device IPs, and KPIs to the Splunk results for the same range.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Map (site locations with status), Table, Status grid.

## SPL

```spl
index=sdwan sourcetype="cisco:sdwan:device"
| where reachability!="reachable"
| table _time site_id hostname system_ip reachability | sort -_time
```

## Visualization

Map (site locations with status), Table, Status grid.

## Known False Positives

Tunnels may renegotiate during ISP maintenance, BFD timer changes, planned controller upgrades, or policy pushes; short blips may look like failures when the business path is still acceptable.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
