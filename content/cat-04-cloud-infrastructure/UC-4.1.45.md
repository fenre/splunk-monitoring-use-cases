<!-- AUTO-GENERATED from UC-4.1.45.json — DO NOT EDIT -->

---
id: "4.1.45"
title: "Systems Manager (SSM) Patch Compliance"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.1.45 · Systems Manager (SSM) Patch Compliance

## Description

Low patch compliance increases vulnerability. SSM Patch Manager compliance status enables prioritization and remediation tracking.

## Value

Low patch compliance increases vulnerability. SSM Patch Manager compliance status enables prioritization and remediation tracking.

## Implementation

Use AWS Config rule for patch-compliance or custom automation to export Patch Manager compliance to S3/CloudWatch. Ingest in Splunk. Dashboard compliance % by OU/account. Alert when compliance drops below threshold.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: SSM compliance data via Config, or custom Lambda polling SSM DescribeInstancePatchStates.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use AWS Config rule for patch-compliance or custom automation to export Patch Manager compliance to S3/CloudWatch. Ingest in Splunk. Dashboard compliance % by OU/account. Alert when compliance drops below threshold.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:ssm:compliance" ComplianceType="Patch" status!="Compliant"
| stats count by status, InstanceId
| sort -count
```

Understanding this SPL

**Systems Manager (SSM) Patch Compliance** — Low patch compliance increases vulnerability. SSM Patch Manager compliance status enables prioritization and remediation tracking.

Documented **Data sources**: SSM compliance data via Config, or custom Lambda polling SSM DescribeInstancePatchStates. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:ssm:compliance. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:ssm:compliance". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by status, InstanceId** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (instance, status), Pie chart (compliant vs non-compliant), Bar chart by patch group.

## SPL

```spl
index=aws sourcetype="aws:ssm:compliance" ComplianceType="Patch" status!="Compliant"
| stats count by status, InstanceId
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Updates.Updates
  where match(Updates.status, "(?i)non-?compliant|missing|failed|not.?installed")
  by Updates.dest Updates.app span=1d
| sort -count
```

## Visualization

Table (instance, status), Pie chart (compliant vs non-compliant), Bar chart by patch group.

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
