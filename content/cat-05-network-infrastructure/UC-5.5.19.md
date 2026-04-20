---
id: "5.5.19"
title: "Transport Circuit SLA Tracking"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.5.19 · Transport Circuit SLA Tracking

## Description

ISPs commit to contractual SLAs for latency, jitter, loss, and uptime per circuit. SD-WAN BFD metrics provide continuous proof of whether carriers meet their commitments. SLA violation evidence supports service credits and carrier negotiations.

## Value

ISPs commit to contractual SLAs for latency, jitter, loss, and uptime per circuit. SD-WAN BFD metrics provide continuous proof of whether carriers meet their commitments. SLA violation evidence supports service credits and carrier negotiations.

## Implementation

Define contractual SLA thresholds per transport type (MPLS: latency <50ms, loss <0.1%; Internet: latency <80ms, loss <0.5%). Aggregate BFD metrics daily. Generate monthly SLA compliance reports per carrier per circuit. Include uptime percentage from interface state changes. Use as evidence for carrier escalations and service credit claims.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API.
• Ensure the following data sources are available: `sourcetype=cisco:sdwan:bfd`, `sourcetype=cisco:sdwan:interface`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Define contractual SLA thresholds per transport type (MPLS: latency <50ms, loss <0.1%; Internet: latency <80ms, loss <0.5%). Aggregate BFD metrics daily. Generate monthly SLA compliance reports per carrier per circuit. Include uptime percentage from interface state changes. Use as evidence for carrier escalations and service credit claims.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=sdwan sourcetype="cisco:sdwan:bfd"
| stats avg(latency) as avg_latency, perc95(latency) as p95_latency, avg(jitter) as avg_jitter, avg(loss_percentage) as avg_loss, count as samples by local_color, site_id, remote_system_ip
| eval sla_latency=50, sla_loss=0.1
| eval latency_breach=if(avg_latency>sla_latency,"YES","NO"), loss_breach=if(avg_loss>sla_loss,"YES","NO")
| where latency_breach="YES" OR loss_breach="YES"
| table site_id local_color avg_latency p95_latency avg_jitter avg_loss latency_breach loss_breach
```

Understanding this SPL

**Transport Circuit SLA Tracking** — ISPs commit to contractual SLAs for latency, jitter, loss, and uptime per circuit. SD-WAN BFD metrics provide continuous proof of whether carriers meet their commitments. SLA violation evidence supports service credits and carrier negotiations.

Documented **Data sources**: `sourcetype=cisco:sdwan:bfd`, `sourcetype=cisco:sdwan:interface`. **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: sdwan; **sourcetype**: cisco:sdwan:bfd. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=sdwan, sourcetype="cisco:sdwan:bfd". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by local_color, site_id, remote_system_ip** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **sla_latency** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **latency_breach** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where latency_breach="YES" OR loss_breach="YES"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Transport Circuit SLA Tracking**): table site_id local_color avg_latency p95_latency avg_jitter avg_loss latency_breach loss_breach


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (circuit SLA compliance), Line chart (latency trending per carrier), Single value (overall SLA compliance %).

## SPL

```spl
index=sdwan sourcetype="cisco:sdwan:bfd"
| stats avg(latency) as avg_latency, perc95(latency) as p95_latency, avg(jitter) as avg_jitter, avg(loss_percentage) as avg_loss, count as samples by local_color, site_id, remote_system_ip
| eval sla_latency=50, sla_loss=0.1
| eval latency_breach=if(avg_latency>sla_latency,"YES","NO"), loss_breach=if(avg_loss>sla_loss,"YES","NO")
| where latency_breach="YES" OR loss_breach="YES"
| table site_id local_color avg_latency p95_latency avg_jitter avg_loss latency_breach loss_breach
```

## Visualization

Table (circuit SLA compliance), Line chart (latency trending per carrier), Single value (overall SLA compliance %).

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
