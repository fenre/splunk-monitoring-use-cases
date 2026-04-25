<!-- AUTO-GENERATED from UC-5.5.8.json — DO NOT EDIT -->

---
id: "5.5.8"
title: "Jitter and Latency per Tunnel"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.5.8 · Jitter and Latency per Tunnel

## Description

Real-time jitter and latency metrics reveal WAN quality degradation before users complain. Critical for voice/video SLAs.

## Value

Real-time jitter and latency metrics reveal WAN quality degradation before users complain. Critical for voice/video SLAs.

## Implementation

Ingest BFD and app-route statistics from vManage API. Monitor per-tunnel quality metrics. Alert when latency >100ms, jitter >30ms, or loss >1% for business-critical SLAs.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), Cisco vManage API.
• Ensure the following data sources are available: `sourcetype=cisco:sdwan:bfd`, `sourcetype=cisco:sdwan:approute`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest BFD and app-route statistics from vManage API. Monitor per-tunnel quality metrics. Alert when latency >100ms, jitter >30ms, or loss >1% for business-critical SLAs.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="cisco:sdwan:approute"
| stats avg(latency) as avg_latency, avg(jitter) as avg_jitter, avg(loss_percentage) as avg_loss by local_system_ip, remote_system_ip, local_color
| where avg_latency > 100 OR avg_jitter > 30 OR avg_loss > 1
| sort -avg_latency
```

Understanding this SPL

**Jitter and Latency per Tunnel** — Real-time jitter and latency metrics reveal WAN quality degradation before users complain. Critical for voice/video SLAs.

Documented **Data sources**: `sourcetype=cisco:sdwan:bfd`, `sourcetype=cisco:sdwan:approute`. **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), Cisco vManage API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: cisco:sdwan:approute. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="cisco:sdwan:approute". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by local_system_ip, remote_system_ip, local_color** so each row reflects one combination of those dimensions.
• Filters the current rows with `where avg_latency > 100 OR avg_jitter > 30 OR avg_loss > 1` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
In Cisco vManage, open the monitor or reporting screen that matches this signal (device, tunnel, interface, certificate, flow, or application route) and compare site names, device IPs, and KPIs to the Splunk results for the same range.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (latency/jitter over time), Table (tunnel, metrics), Gauge (SLA compliance).

## SPL

```spl
index=network sourcetype="cisco:sdwan:approute"
| stats avg(latency) as avg_latency, avg(jitter) as avg_jitter, avg(loss_percentage) as avg_loss by local_system_ip, remote_system_ip, local_color
| where avg_latency > 100 OR avg_jitter > 30 OR avg_loss > 1
| sort -avg_latency
```

## Visualization

Line chart (latency/jitter over time), Table (tunnel, metrics), Gauge (SLA compliance).

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
