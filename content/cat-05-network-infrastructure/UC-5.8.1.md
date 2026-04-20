---
id: "5.8.1"
title: "DNA Center Assurance Alerts (Cisco Catalyst Center)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.8.1 · DNA Center Assurance Alerts (Cisco Catalyst Center)

## Description

DNA Center provides AI/ML-driven network issue detection. Centralizing in Splunk enables cross-domain correlation.

## Value

DNA Center provides AI/ML-driven network issue detection. Centralizing in Splunk enables cross-domain correlation.

## Implementation

Configure DNA Center API integration in Splunk TA. Poll for issues and client health. Alert on P1/P2 issues.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: DNA Center API (issues, events).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure DNA Center API integration in Splunk TA. Poll for issues and client health. Alert on P1/P2 issues.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="cisco:dnac:issues"
| stats count by priority, category, name | sort -priority -count
```

Understanding this SPL

**DNA Center Assurance Alerts (Cisco Catalyst Center)** — DNA Center provides AI/ML-driven network issue detection. Centralizing in Splunk enables cross-domain correlation.

Documented **Data sources**: DNA Center API (issues, events). **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: cisco:dnac:issues. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="cisco:dnac:issues". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by priority, category, name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (issue, priority, category), Bar chart, Single value.

## SPL

```spl
index=network sourcetype="cisco:dnac:issues"
| stats count by priority, category, name | sort -priority -count
```

## Visualization

Table (issue, priority, category), Bar chart, Single value.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
