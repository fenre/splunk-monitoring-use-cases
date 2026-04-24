---
id: "5.13.33"
title: "Compliance Violation Detail Drill-Down"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.13.33 · Compliance Violation Detail Drill-Down

## Description

Provides detailed violation-level information for non-compliant devices, including the specific rule violated, the violation message, and suggested remediation actions.

## Value

Operations teams need actionable detail to remediate violations. This drill-down provides the specific violation and recommended fix for each non-compliant device.

## Implementation

Enable the `compliance` input. Confirm the TA normalises `violations` (JSON or multivalue) as expected. Adjust `spath` paths if the payload structure differs in your version.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:compliance (complianceStatus, violations, deviceName, complianceType; nested fields may require spath).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable the `compliance` input. Confirm the TA normalises `violations` (JSON or multivalue) as expected. Adjust `spath` paths if the payload structure differs in your version.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:compliance" complianceStatus="NON_COMPLIANT" | spath output=violations path=violations{} | mvexpand violations | spath input=violations | table deviceName complianceType violationType violationMessage remediationAction | sort deviceName complianceType
```

Understanding this SPL

**Compliance Violation Detail Drill-Down** — Operations teams need actionable detail to remediate violations. This drill-down provides the specific violation and recommended fix for each non-compliant device.

**Pipeline walkthrough**

• Starts with non-compliant records only, then `spath` pulls structured violation details from the nested payload.
• `mvexpand` creates one row per violation when multiple issues exist for a single device or policy type.
• The second `spath` extracts typed fields (for example `violationType`, `remediationAction`) and `table` produces an operator-facing remediation checklist.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions as required. Consider visualizations: Table (deviceName, complianceType, violationType, violationMessage, remediationAction) with drilldowns.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:compliance" complianceStatus="NON_COMPLIANT" | spath output=violations path=violations{} | mvexpand violations | spath input=violations | table deviceName complianceType violationType violationMessage remediationAction | sort deviceName complianceType
```

## Visualization

Table (deviceName, complianceType, violationType, violationMessage, remediationAction) with drilldowns.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
