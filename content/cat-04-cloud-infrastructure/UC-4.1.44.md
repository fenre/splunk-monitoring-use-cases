<!-- AUTO-GENERATED from UC-4.1.44.json — DO NOT EDIT -->

---
id: "4.1.44"
title: "Inspector Vulnerability and Finding Trends"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.1.44 · Inspector Vulnerability and Finding Trends

## Description

Inspector findings (EC2, ECR, Lambda) identify vulnerabilities. Tracking trends and new critical findings supports patch and image hygiene.

## Value

Inspector findings (EC2, ECR, Lambda) identify vulnerabilities. Tracking trends and new critical findings supports patch and image hygiene.

## Implementation

Configure Inspector to send findings to EventBridge or SNS; ingest in Splunk. Alert on new CRITICAL findings. Dashboard open findings by severity and age. Correlate with patch compliance (SSM).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: Inspector findings via EventBridge or SNS, or Security Hub (which aggregates Inspector).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Inspector to send findings to EventBridge or SNS; ingest in Splunk. Alert on new CRITICAL findings. Dashboard open findings by severity and age. Correlate with patch compliance (SSM).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:inspector" severity="CRITICAL" OR severity="HIGH"
| stats count by severity, findingType, resourceType
| sort -count
```

Understanding this SPL

**Inspector Vulnerability and Finding Trends** — Inspector findings (EC2, ECR, Lambda) identify vulnerabilities. Tracking trends and new critical findings supports patch and image hygiene.

Documented **Data sources**: Inspector findings via EventBridge or SNS, or Security Hub (which aggregates Inspector). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:inspector. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:inspector". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by severity, findingType, resourceType** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (severity, type, count), Bar chart by severity, Trend line (findings over time).

## SPL

```spl
index=aws sourcetype="aws:inspector" severity="CRITICAL" OR severity="HIGH"
| stats count by severity, findingType, resourceType
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Intrusion_Detection.IDS_Attacks
  where match(lower(IDS_Attacks.severity), "high|critical")
  by IDS_Attacks.signature IDS_Attacks.src span=1d
| sort -count
```

## Visualization

Table (severity, type, count), Bar chart by severity, Trend line (findings over time).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
