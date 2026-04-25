<!-- AUTO-GENERATED from UC-5.5.1.json — DO NOT EDIT -->

---
id: "5.5.1"
title: "Tunnel Health Monitoring"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.5.1 · Tunnel Health Monitoring

## Description

Tunnel loss/latency/jitter directly impacts application experience over WAN.

## Value

Tunnel loss/latency/jitter directly impacts application experience over WAN.

## Implementation

Poll vManage API for BFD session statistics. Collect loss, latency, jitter per tunnel. Alert when SLA thresholds exceeded.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API.
• Ensure the following data sources are available: vManage BFD metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll vManage API for BFD session statistics. Collect loss, latency, jitter per tunnel. Alert when SLA thresholds exceeded.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=sdwan sourcetype="cisco:sdwan:bfd"
| stats avg(loss_percentage) as loss, avg(latency) as latency, avg(jitter) as jitter by site, tunnel_name
| where loss > 1 OR latency > 100 OR jitter > 30
```

Understanding this SPL

**Tunnel Health Monitoring** — Tunnel loss/latency/jitter directly impacts application experience over WAN.

Documented **Data sources**: vManage BFD metrics. **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: sdwan; **sourcetype**: cisco:sdwan:bfd. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=sdwan, sourcetype="cisco:sdwan:bfd". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by site, tunnel_name** so each row reflects one combination of those dimensions.
• Filters the current rows with `where loss > 1 OR latency > 100 OR jitter > 30` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
In Cisco vManage, open the monitor or reporting screen that matches this signal (device, tunnel, interface, certificate, flow, or application route) and compare site names, device IPs, and KPIs to the Splunk results for the same range.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (loss/latency/jitter per tunnel), Table, Status grid per site.

## SPL

```spl
index=sdwan sourcetype="cisco:sdwan:bfd"
| stats avg(loss_percentage) as loss, avg(latency) as latency, avg(jitter) as jitter by site, tunnel_name
| where loss > 1 OR latency > 100 OR jitter > 30
```

## Visualization

Line chart (loss/latency/jitter per tunnel), Table, Status grid per site.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
