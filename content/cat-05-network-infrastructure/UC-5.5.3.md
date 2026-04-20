---
id: "5.5.3"
title: "Application SLA Violations"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.5.3 · Application SLA Violations

## Description

Detects when business-critical applications aren't meeting performance requirements over the WAN.

## Value

Detects when business-critical applications aren't meeting performance requirements over the WAN.

## Implementation

Collect app-aware routing statistics from vManage. Alert when critical applications violate their SLA class.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: vManage app-aware routing metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect app-aware routing statistics from vManage. Alert when critical applications violate their SLA class.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=sdwan sourcetype="cisco:sdwan:approute"
| where sla_violation="true"
| stats count by site, app_name, sla_class | sort -count
```

Understanding this SPL

**Application SLA Violations** — Detects when business-critical applications aren't meeting performance requirements over the WAN.

Documented **Data sources**: vManage app-aware routing metrics. **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: sdwan; **sourcetype**: cisco:sdwan:approute. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=sdwan, sourcetype="cisco:sdwan:approute". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where sla_violation="true"` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by site, app_name, sla_class** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (site, app, violations), Bar chart by app, Timechart.

## SPL

```spl
index=sdwan sourcetype="cisco:sdwan:approute"
| where sla_violation="true"
| stats count by site, app_name, sla_class | sort -count
```

## Visualization

Table (site, app, violations), Bar chart by app, Timechart.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
