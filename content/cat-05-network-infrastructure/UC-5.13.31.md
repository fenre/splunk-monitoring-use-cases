---
id: "5.13.31"
title: "Compliance by Rule/Policy Category"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.13.31 · Compliance by Rule/Policy Category

## Description

Breaks down non-compliance by policy rule category to identify which compliance areas (running config, image, PSIRT, etc.) have the most violations.

## Value

Not all compliance violations are equal. Breaking down by rule category reveals whether the problem is configuration drift, outdated images, or unpatched vulnerabilities.

## Implementation

Enable the `compliance` input. If `complianceType` is nested, use `spath` or field aliases from the TA so category names appear consistently.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:compliance (complianceType, deviceName, complianceStatus).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable the `compliance` input. If `complianceType` is nested, use `spath` or field aliases from the TA so category names appear consistently.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:compliance" complianceStatus="NON_COMPLIANT" | stats count as violations dc(deviceName) as affected_devices by complianceType | sort -violations
```

Understanding this SPL

**Compliance by Rule/Policy Category** — Not all compliance violations are equal. Breaking down by rule category reveals whether the problem is configuration drift, outdated images, or unpatched vulnerabilities.

**Pipeline walkthrough**

• Keeps only failing checks so the chart is not swamped with passing noise.
• `stats` counts how many non-compliant results appear for each `complianceType` and how many unique `deviceName` values that represents.
• Sorting by `-violations` shows which policy families need engineering attention first.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions as required. Consider visualizations: Bar chart (violations by complianceType), table with affected device counts.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:compliance" complianceStatus="NON_COMPLIANT" | stats count as violations dc(deviceName) as affected_devices by complianceType | sort -violations
```

## Visualization

Bar chart (violations by complianceType), table with affected device counts.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
