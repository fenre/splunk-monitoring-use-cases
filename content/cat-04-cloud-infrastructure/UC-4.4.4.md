---
id: "4.4.4"
title: "Cloud Resource Tagging Compliance"
criticality: "low"
splunkPillar: "Security"
---

# UC-4.4.4 · Cloud Resource Tagging Compliance

## Description

Untagged resources can't be tracked for cost allocation, compliance, or ownership. Tagging compliance is foundational for cloud governance.

## Value

Untagged resources can't be tracked for cost allocation, compliance, or ownership. Tagging compliance is foundational for cloud governance.

## Implementation

Use AWS Config rules (required-tags), Azure Policy, or GCP org policies to evaluate tagging. Ingest compliance results. Dashboard showing tagging compliance by tag and resource type.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Cloud provider TAs, Config rules.
• Ensure the following data sources are available: Cloud resource inventories, Config/Policy compliance.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use AWS Config rules (required-tags), Azure Policy, or GCP org policies to evaluate tagging. Ingest compliance results. Dashboard showing tagging compliance by tag and resource type.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:config:notification" resourceType="AWS::EC2::Instance"
| spath output=tags path=configuration.tags{}
| eval has_owner = if(match(tags, "Owner"), "Yes", "No")
| eval has_env = if(match(tags, "Environment"), "Yes", "No")
| where has_owner="No" OR has_env="No"
| table resourceId has_owner has_env
```

Understanding this SPL

**Cloud Resource Tagging Compliance** — Untagged resources can't be tracked for cost allocation, compliance, or ownership. Tagging compliance is foundational for cloud governance.

Documented **Data sources**: Cloud resource inventories, Config/Policy compliance. **App/TA** (typical add-on context): Cloud provider TAs, Config rules. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:config:notification, AWS::EC2::Instance. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:config:notification". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts structured paths (JSON/XML) with `spath`.
• `eval` defines or adjusts **has_owner** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **has_env** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where has_owner="No" OR has_env="No"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Cloud Resource Tagging Compliance**): table resourceId has_owner has_env


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (resource, missing tags), Pie chart (compliant %), Bar chart by tag.

## SPL

```spl
index=aws sourcetype="aws:config:notification" resourceType="AWS::EC2::Instance"
| spath output=tags path=configuration.tags{}
| eval has_owner = if(match(tags, "Owner"), "Yes", "No")
| eval has_env = if(match(tags, "Environment"), "Yes", "No")
| where has_owner="No" OR has_env="No"
| table resourceId has_owner has_env
```

## Visualization

Table (resource, missing tags), Pie chart (compliant %), Bar chart by tag.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
