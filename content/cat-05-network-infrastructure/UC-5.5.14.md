<!-- AUTO-GENERATED from UC-5.5.14.json — DO NOT EDIT -->

---
id: "5.5.14"
title: "Firmware Version Compliance"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.5.14 · Firmware Version Compliance

## Description

Running inconsistent or outdated software versions across the SD-WAN fabric creates security vulnerabilities and feature gaps. Compliance dashboards accelerate upgrade planning and audit readiness.

## Value

Running inconsistent or outdated software versions across the SD-WAN fabric creates security vulnerabilities and feature gaps. Compliance dashboards accelerate upgrade planning and audit readiness.

## Implementation

Poll vManage device inventory for software versions and model types. Define a target version per device family. Report on compliance percentage. Alert when devices fall more than two minor versions behind the target. Use to prioritize upgrade batches by site criticality.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API.
• Ensure the following data sources are available: vManage device inventory, `sourcetype=cisco:sdwan:device`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll vManage device inventory for software versions and model types. Define a target version per device family. Report on compliance percentage. Alert when devices fall more than two minor versions behind the target. Use to prioritize upgrade batches by site criticality.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=sdwan sourcetype="cisco:sdwan:device"
| stats latest(version) as sw_version, latest(model) as model by hostname, system_ip, site_id
| eventstats count by sw_version
| eval target_version="17.12.04"
| eval compliant=if(sw_version=target_version,"yes","no")
| stats count as total, count(eval(compliant="yes")) as compliant_count by sw_version
| eval pct=round(compliant_count/total*100,1)
| sort -total
```

Understanding this SPL

**Firmware Version Compliance** — Running inconsistent or outdated software versions across the SD-WAN fabric creates security vulnerabilities and feature gaps. Compliance dashboards accelerate upgrade planning and audit readiness.

Documented **Data sources**: vManage device inventory, `sourcetype=cisco:sdwan:device`. **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: sdwan; **sourcetype**: cisco:sdwan:device. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=sdwan, sourcetype="cisco:sdwan:device". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by hostname, system_ip, site_id** so each row reflects one combination of those dimensions.
• `eventstats` rolls up events into metrics; results are split **by sw_version** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **target_version** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **compliant** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by sw_version** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
In Cisco vManage, open the monitor or reporting screen that matches this signal (device, tunnel, interface, certificate, flow, or application route) and compare site names, device IPs, and KPIs to the Splunk results for the same range.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Pie chart (version distribution), Table (non-compliant devices), Single value (compliance percentage).

## SPL

```spl
index=sdwan sourcetype="cisco:sdwan:device"
| stats latest(version) as sw_version, latest(model) as model by hostname, system_ip, site_id
| eventstats count by sw_version
| eval target_version="17.12.04"
| eval compliant=if(sw_version=target_version,"yes","no")
| stats count as total, count(eval(compliant="yes")) as compliant_count by sw_version
| eval pct=round(compliant_count/total*100,1)
| sort -total
```

## Visualization

Pie chart (version distribution), Table (non-compliant devices), Single value (compliance percentage).

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
