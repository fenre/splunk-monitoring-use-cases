---
id: "5.9.50"
title: "ThousandEyes ITSI Service Health (Content Pack)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.50 · ThousandEyes ITSI Service Health (Content Pack)

## Description

The ITSI Content Pack for Cisco ThousandEyes provides pre-built service templates, KPI base searches, entity types, and Glass Tables for service-centric monitoring. It maps ThousandEyes test results to ITSI services for unified health scoring across all monitoring domains.

## Value

The ITSI Content Pack for Cisco ThousandEyes provides pre-built service templates, KPI base searches, entity types, and Glass Tables for service-centric monitoring. It maps ThousandEyes test results to ITSI services for unified health scoring across all monitoring domains.

## Implementation

Install the ITSI Content Pack for Cisco ThousandEyes from the ITSI Content Library. The content pack provides: entity types (ThousandEyes Test, ThousandEyes Agent), KPI base searches (latency, loss, jitter, availability, MOS for each test type), service templates, and Glass Table templates. After installation, import the service templates and configure entity discovery to match your ThousandEyes tests. KPIs are automatically populated from the ThousandEyes data model.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719), ITSI Content Pack for Cisco ThousandEyes.
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel data via ITSI KPI base searches.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Install the ITSI Content Pack for Cisco ThousandEyes from the ITSI Content Library. The content pack provides: entity types (ThousandEyes Test, ThousandEyes Agent), KPI base searches (latency, loss, jitter, availability, MOS for each test type), service templates, and Glass Table templates. After installation, import the service templates and configure entity discovery to match your ThousandEyes tests. KPIs are automatically populated from the ThousandEyes data model.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
| from datamodel:"ITSI_KPI_Summary"
| where service_name="*ThousandEyes*"
| stats latest(kpi_urgency) as urgency latest(alert_level) as alert_level by service_name, kpiid, itsi_kpi_id
| sort -urgency
```

Understanding this SPL

**ThousandEyes ITSI Service Health (Content Pack)** — The ITSI Content Pack for Cisco ThousandEyes provides pre-built service templates, KPI base searches, entity types, and Glass Tables for service-centric monitoring. It maps ThousandEyes test results to ITSI services for unified health scoring across all monitoring domains.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel data via ITSI KPI base searches. **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719), ITSI Content Pack for Cisco ThousandEyes. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Uses `from` (dataset / Federated Search) — verify dataset availability and permissions.
• Filters the current rows with `where service_name="*ThousandEyes*"` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by service_name, kpiid, itsi_kpi_id** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: ITSI Service Tree, Glass Table, KPI cards (latency, loss, availability, MOS), Service health score.

## SPL

```spl
| from datamodel:"ITSI_KPI_Summary"
| where service_name="*ThousandEyes*"
| stats latest(kpi_urgency) as urgency latest(alert_level) as alert_level by service_name, kpiid, itsi_kpi_id
| sort -urgency
```

## Visualization

ITSI Service Tree, Glass Table, KPI cards (latency, loss, availability, MOS), Service health score.

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
