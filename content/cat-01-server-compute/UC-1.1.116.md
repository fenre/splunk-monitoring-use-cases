<!-- AUTO-GENERATED from UC-1.1.116.json — DO NOT EDIT -->

---
id: "1.1.116"
title: "Installed Package Drift Detection"
criticality: "medium"
splunkPillar: "Security"
---

# UC-1.1.116 · Installed Package Drift Detection

## Description

Package drift indicates unauthorized software installation or configuration management failures.

## Value

Package drift indicates unauthorized software installation or configuration management failures.

## Implementation

Use Splunk_TA_nix package input to track installed software. Baseline expected packages per host. Alert on unexpected new packages with name and version details.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`.
• Ensure the following data sources are available: `sourcetype=package`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use Splunk_TA_nix package input to track installed software. Baseline expected packages per host. Alert on unexpected new packages with name and version details.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=package host=*
| stats dc(package) as installed_count by host
| stats avg(installed_count) as baseline
| where installed_count > baseline + threshold
```

Understanding this SPL

**Installed Package Drift Detection** — Package drift indicates unauthorized software installation or configuration management failures.

Documented **Data sources**: `sourcetype=package`. **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: package. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=package. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions.
• `stats` aggregates the pipeline (counts, distinct values, sums, percentiles, etc.) into fewer rows.
• Filters the current rows with `where installed_count > baseline + threshold` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Alert

## SPL

```spl
index=os sourcetype=package host=*
| stats dc(package) as installed_count by host
| stats avg(installed_count) as baseline
| where installed_count > baseline + threshold
```

## Visualization

Table, Alert

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
