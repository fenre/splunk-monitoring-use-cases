<!-- AUTO-GENERATED from UC-4.1.50.json — DO NOT EDIT -->

---
id: "4.1.50"
title: "Trusted Advisor Check Results and Cost Optimization"
criticality: "low"
splunkPillar: "Observability"
---

# UC-4.1.50 · Trusted Advisor Check Results and Cost Optimization

## Description

Trusted Advisor identifies cost optimization, performance, and security improvements. Tracking check results supports governance and savings.

## Value

Trusted Advisor identifies cost optimization, performance, and security improvements. Tracking check results supports governance and savings.

## Implementation

Schedule Lambda or script to call Trusted Advisor API (requires Business/Enterprise Support). Export check results to S3 or send to Splunk via HEC. Dashboard by category (cost, performance, security). Alert on new critical security checks failing.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws` (Trusted Advisor API or Support API).
• Ensure the following data sources are available: Trusted Advisor API (describe-trusted-advisor-checks, describe-trusted-advisor-check-result).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Schedule Lambda or script to call Trusted Advisor API (requires Business/Enterprise Support). Export check results to S3 or send to Splunk via HEC. Dashboard by category (cost, performance, security). Alert on new critical security checks failing.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:trustedadvisor" status="warning" OR status="error"
| stats count by category name status
| sort -count
```

Understanding this SPL

**Trusted Advisor Check Results and Cost Optimization** — Trusted Advisor identifies cost optimization, performance, and security improvements. Tracking check results supports governance and savings.

Documented **Data sources**: Trusted Advisor API (describe-trusted-advisor-checks, describe-trusted-advisor-check-result). **App/TA** (typical add-on context): `Splunk_TA_aws` (Trusted Advisor API or Support API). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:trustedadvisor. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:trustedadvisor". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by category name status** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (check, category, status), Pie chart (ok vs warning vs error), Bar chart by category.

## SPL

```spl
index=aws sourcetype="aws:trustedadvisor" status="warning" OR status="error"
| stats count by category name status
| sort -count
```

## Visualization

Table (check, category, status), Pie chart (ok vs warning vs error), Bar chart by category.

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
