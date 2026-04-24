---
id: "5.13.32"
title: "Compliance Drift Detection (Was Compliant, Now Not)"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.13.32 · Compliance Drift Detection (Was Compliant, Now Not)

## Description

Detects devices that were previously compliant but have drifted to non-compliant status, indicating unauthorized changes or configuration drift.

## Value

Compliance drift means something changed — either an unauthorized modification, a failed change, or a new policy that existing configs do not meet. Catching drift early prevents audit findings.

## Implementation

Enable the `compliance` input. Use a time range that includes at least two polling cycles per device. Pair with change records to distinguish policy updates from unauthorized edits.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:compliance (complianceStatus, deviceName, complianceType over time).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable the `compliance` input. Use a time range that includes at least two polling cycles per device. Pair with change records to distinguish policy updates from unauthorized edits.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:compliance" | stats latest(complianceStatus) as current_status earliest(complianceStatus) as previous_status by deviceName, complianceType | where current_status="NON_COMPLIANT" AND previous_status="COMPLIANT" | table deviceName complianceType current_status previous_status
```

Understanding this SPL

**Compliance Drift Detection (Was Compliant, Now Not)** — Compliance drift means something changed — either an unauthorized modification, a failed change, or a new policy that existing configs do not meet. Catching drift early prevents audit findings.

**Pipeline walkthrough**

• `stats` compares the earliest and latest `complianceStatus` seen in the window for each `deviceName` and `complianceType` pair.
• The `where` clause keeps rows where the path moved from `COMPLIANT` to `NON_COMPLIANT`, highlighting regression rather than steady failure.
• `table` presents a simple evidence list for SOC or audit follow-up.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions as required. Consider visualizations: Table (deviceName, complianceType, current_status, previous_status), alert list for drift events.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:compliance" | stats latest(complianceStatus) as current_status earliest(complianceStatus) as previous_status by deviceName, complianceType | where current_status="NON_COMPLIANT" AND previous_status="COMPLIANT" | table deviceName complianceType current_status previous_status
```

## Visualization

Table (deviceName, complianceType, current_status, previous_status), alert list for drift events.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
