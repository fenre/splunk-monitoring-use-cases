---
id: "5.5.11"
title: "OMP Route Table Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.5.11 · OMP Route Table Monitoring

## Description

OMP (Overlay Management Protocol) distributes routes across the SD-WAN fabric. Route churn, missing prefixes, or unexpected withdrawals indicate overlay instability that degrades site-to-site reachability.

## Value

OMP (Overlay Management Protocol) distributes routes across the SD-WAN fabric. Route churn, missing prefixes, or unexpected withdrawals indicate overlay instability that degrades site-to-site reachability.

## Implementation

Poll vManage OMP peers and routes API endpoints. Baseline route count per device. Alert when a site loses more than 20% of its expected routes or when OMP peer adjacencies drop. Track route churn rate over time to identify flapping prefixes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API.
• Ensure the following data sources are available: vManage OMP route table, `sourcetype=cisco:sdwan:omp`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll vManage OMP peers and routes API endpoints. Baseline route count per device. Alert when a site loses more than 20% of its expected routes or when OMP peer adjacencies drop. Track route churn rate over time to identify flapping prefixes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=sdwan sourcetype="cisco:sdwan:omp"
| stats dc(prefix) as route_count, dc(peer) as peer_count by system_ip, site_id
| appendpipe [| stats avg(route_count) as baseline_routes]
| where route_count < baseline_routes * 0.8
| table system_ip site_id route_count peer_count
```

Understanding this SPL

**OMP Route Table Monitoring** — OMP (Overlay Management Protocol) distributes routes across the SD-WAN fabric. Route churn, missing prefixes, or unexpected withdrawals indicate overlay instability that degrades site-to-site reachability.

Documented **Data sources**: vManage OMP route table, `sourcetype=cisco:sdwan:omp`. **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: sdwan; **sourcetype**: cisco:sdwan:omp. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=sdwan, sourcetype="cisco:sdwan:omp". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by system_ip, site_id** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Appends rows from a subsearch with `append`.
• Filters the current rows with `where route_count < baseline_routes * 0.8` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **OMP Route Table Monitoring**): table system_ip site_id route_count peer_count


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (route count over time per site), Table (devices below baseline), Single value (total OMP peers).

## SPL

```spl
index=sdwan sourcetype="cisco:sdwan:omp"
| stats dc(prefix) as route_count, dc(peer) as peer_count by system_ip, site_id
| appendpipe [| stats avg(route_count) as baseline_routes]
| where route_count < baseline_routes * 0.8
| table system_ip site_id route_count peer_count
```

## Visualization

Line chart (route count over time per site), Table (devices below baseline), Single value (total OMP peers).

## Known False Positives

Planned network changes that withdraw routes intentionally; correlate with change management windows.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
