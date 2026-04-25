<!-- AUTO-GENERATED from UC-4.1.15.json — DO NOT EDIT -->

---
id: "4.1.15"
title: "Config Compliance Monitoring"
criticality: "medium"
splunkPillar: "Security"
---

# UC-4.1.15 · Config Compliance Monitoring

## Description

AWS Config rules continuously evaluate resource compliance against security best practices. Non-compliant resources are attack surface.

## Value

AWS Config rules continuously evaluate resource compliance against security best practices. Non-compliant resources are attack surface.

## Implementation

Enable AWS Config with rules (e.g., CIS Benchmark). Forward Config notifications to SNS/S3 and ingest in Splunk. Dashboard showing compliance score per rule. Alert on newly non-compliant critical resources.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: `sourcetype=aws:config:notification`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable AWS Config with rules (e.g., CIS Benchmark). Forward Config notifications to SNS/S3 and ingest in Splunk. Dashboard showing compliance score per rule. Alert on newly non-compliant critical resources.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:config:notification" configRuleList{}.complianceType="NON_COMPLIANT"
| stats count by resourceType, resourceId, configRuleList{}.configRuleName
| sort -count
```

Understanding this SPL

**Config Compliance Monitoring** — AWS Config rules continuously evaluate resource compliance against security best practices. Non-compliant resources are attack surface.

Documented **Data sources**: `sourcetype=aws:config:notification`. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:config:notification. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:config:notification". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by resourceType, resourceId, configRuleList{}.configRuleName** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (resource, rule, status), Pie chart (compliant %), Bar chart by rule.

## SPL

```spl
index=aws sourcetype="aws:config:notification" configRuleList{}.complianceType="NON_COMPLIANT"
| stats count by resourceType, resourceId, configRuleList{}.configRuleName
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  where like(All_Changes.status, "%NON%") OR match(All_Changes.status, "(?i)non_?compliant|fail|error")
  by All_Changes.object All_Changes.user span=1h
| sort -count
```

## Visualization

Table (resource, rule, status), Pie chart (compliant %), Bar chart by rule.

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
