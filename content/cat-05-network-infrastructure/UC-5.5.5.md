<!-- AUTO-GENERATED from UC-5.5.5.json — DO NOT EDIT -->

---
id: "5.5.5"
title: "Control Plane Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.5.5 · Control Plane Health

## Description

vSmart/vManage connectivity issues affect policy distribution and overlay routing.

## Value

vSmart/vManage connectivity issues affect policy distribution and overlay routing.

## Implementation

Monitor control connections to vSmart and vManage. Alert on any control connection down.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: vManage control connection logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor control connections to vSmart and vManage. Alert on any control connection down.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=sdwan sourcetype="cisco:sdwan:control"
| where state!="up"
| table _time hostname peer_type peer_system_ip state | sort -_time
```

Understanding this SPL

**Control Plane Health** — vSmart/vManage connectivity issues affect policy distribution and overlay routing.

Documented **Data sources**: vManage control connection logs. **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: sdwan; **sourcetype**: cisco:sdwan:control. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=sdwan, sourcetype="cisco:sdwan:control". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where state!="up"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Control Plane Health**): table _time hostname peer_type peer_system_ip state
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
In Cisco vManage, open the monitor or reporting screen that matches this signal (device, tunnel, interface, certificate, flow, or application route) and compare site names, device IPs, and KPIs to the Splunk results for the same range.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status panel, Table, Timeline.

## SPL

```spl
index=sdwan sourcetype="cisco:sdwan:control"
| where state!="up"
| table _time hostname peer_type peer_system_ip state | sort -_time
```

## Visualization

Status panel, Table, Timeline.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
