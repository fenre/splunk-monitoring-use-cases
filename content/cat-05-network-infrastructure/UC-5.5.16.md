<!-- AUTO-GENERATED from UC-5.5.16.json — DO NOT EDIT -->

---
id: "5.5.16"
title: "Cloud OnRamp Performance"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.5.16 · Cloud OnRamp Performance

## Description

Cloud OnRamp probes SaaS and IaaS endpoints from each site to select the best path. Monitoring probe results reveals when cloud application performance degrades before users open tickets, and validates that SD-WAN is actually improving cloud access.

## Value

Cloud OnRamp probes SaaS and IaaS endpoints from each site to select the best path. Monitoring probe results reveals when cloud application performance degrades before users open tickets, and validates that SD-WAN is actually improving cloud access.

## Implementation

Enable Cloud OnRamp for SaaS (Microsoft 365, Webex, Salesforce, etc.) and/or IaaS (AWS, Azure, GCP) in vManage. Collect vQoE scores and probe metrics. Alert when a SaaS application's quality score drops below 8 (out of 10) or latency exceeds 150ms. Compare direct internet access (DIA) vs gateway exit paths to validate routing decisions.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API.
• Ensure the following data sources are available: vManage Cloud OnRamp metrics, `sourcetype=cisco:sdwan:cloudx`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Cloud OnRamp for SaaS (Microsoft 365, Webex, Salesforce, etc.) and/or IaaS (AWS, Azure, GCP) in vManage. Collect vQoE scores and probe metrics. Alert when a SaaS application's quality score drops below 8 (out of 10) or latency exceeds 150ms. Compare direct internet access (DIA) vs gateway exit paths to validate routing decisions.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=sdwan sourcetype="cisco:sdwan:cloudx"
| stats avg(vqoe_score) as avg_score, avg(latency) as avg_latency, avg(loss) as avg_loss by app_name, site_id, exit_type
| where avg_score < 8 OR avg_latency > 150
| sort avg_score
| table app_name site_id exit_type avg_score avg_latency avg_loss
```

Understanding this SPL

**Cloud OnRamp Performance** — Cloud OnRamp probes SaaS and IaaS endpoints from each site to select the best path. Monitoring probe results reveals when cloud application performance degrades before users open tickets, and validates that SD-WAN is actually improving cloud access.

Documented **Data sources**: vManage Cloud OnRamp metrics, `sourcetype=cisco:sdwan:cloudx`. **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: sdwan; **sourcetype**: cisco:sdwan:cloudx. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=sdwan, sourcetype="cisco:sdwan:cloudx". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by app_name, site_id, exit_type** so each row reflects one combination of those dimensions.
• Filters the current rows with `where avg_score < 8 OR avg_latency > 150` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **Cloud OnRamp Performance**): table app_name site_id exit_type avg_score avg_latency avg_loss


Step 3 — Validate
In Cisco vManage, open the monitor or reporting screen that matches this signal (device, tunnel, interface, certificate, flow, or application route) and compare site names, device IPs, and KPIs to the Splunk results for the same range.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (vQoE score trending per app), Table (underperforming apps), Bar chart (DIA vs gateway comparison).

## SPL

```spl
index=sdwan sourcetype="cisco:sdwan:cloudx"
| stats avg(vqoe_score) as avg_score, avg(latency) as avg_latency, avg(loss) as avg_loss by app_name, site_id, exit_type
| where avg_score < 8 OR avg_latency > 150
| sort avg_score
| table app_name site_id exit_type avg_score avg_latency avg_loss
```

## Visualization

Line chart (vQoE score trending per app), Table (underperforming apps), Bar chart (DIA vs gateway comparison).

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
