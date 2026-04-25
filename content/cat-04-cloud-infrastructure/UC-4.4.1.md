<!-- AUTO-GENERATED from UC-4.4.1.json — DO NOT EDIT -->

---
id: "4.4.1"
title: "Terraform Drift Detection"
criticality: "medium"
splunkPillar: "Security"
---

# UC-4.4.1 · Terraform Drift Detection

## Description

Infrastructure drift from declared IaC state means manual changes broke the single source of truth. Causes unpredictable behavior and deployment failures.

## Value

Infrastructure drift from declared IaC state means manual changes broke the single source of truth. Causes unpredictable behavior and deployment failures.

## Implementation

Run `terraform plan -detailed-exitcode` on schedule in CI/CD. Forward plan output to Splunk via HEC. Exit code 2 = changes detected (drift). Alert on any drift in production workspaces.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom input (Terraform CLI output, CI/CD integration).
• Ensure the following data sources are available: `terraform plan` output, CI/CD pipeline logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Run `terraform plan -detailed-exitcode` on schedule in CI/CD. Forward plan output to Splunk via HEC. Exit code 2 = changes detected (drift). Alert on any drift in production workspaces.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=devops sourcetype="terraform:plan"
| where changes_detected="true"
| stats count as drifted_resources by workspace, resource_type
| sort -drifted_resources
```

Understanding this SPL

**Terraform Drift Detection** — Infrastructure drift from declared IaC state means manual changes broke the single source of truth. Causes unpredictable behavior and deployment failures.

Documented **Data sources**: `terraform plan` output, CI/CD pipeline logs. **App/TA** (typical add-on context): Custom input (Terraform CLI output, CI/CD integration). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: devops; **sourcetype**: terraform:plan. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=devops, sourcetype="terraform:plan". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where changes_detected="true"` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by workspace, resource_type** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (workspace, resource, drift), Single value (drifted resources), Bar chart.

## SPL

```spl
index=devops sourcetype="terraform:plan"
| where changes_detected="true"
| stats count as drifted_resources by workspace, resource_type
| sort -drifted_resources
```

## Visualization

Table (workspace, resource, drift), Single value (drifted resources), Bar chart.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
