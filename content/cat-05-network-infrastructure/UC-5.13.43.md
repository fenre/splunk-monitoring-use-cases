---
id: "5.13.43"
title: "Client Connection Failure Analysis"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.43 · Client Connection Failure Analysis

## Description

Analyzes client connection failures by reason, connection type, and SSID to identify the root cause of connectivity problems.

## Value

Connection failures frustrate users and generate helpdesk tickets. Categorizing failures by reason (auth, DHCP, association) points directly to the failing infrastructure component.

## Implementation

Enable the `client` input in the Cisco Catalyst TA pointing to `index=catalyst`. The TA polls client detail data from the Catalyst Center Intent API every 60 minutes. Key fields: `connectionStatus`, `onboardingStatus`, `failureReason`, `connectionType`, `ssid`, `macAddress`.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:client (Catalyst Center client data; fields connectionStatus, onboardingStatus, failureReason, connectionType, ssid).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable the `client` input in the Cisco Catalyst TA pointing to `index=catalyst`. The TA polls client detail data from the Catalyst Center Intent API every 60 minutes. Key fields: `connectionStatus`, `onboardingStatus`, `failureReason`, `connectionType`, `ssid`, `macAddress`.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:client" (connectionStatus="FAILED" OR onboardingStatus="FAILED") | stats count as failure_count by failureReason, connectionType, ssid | sort -failure_count
```

Understanding this SPL

**Client Connection Failure Analysis** — Connection failures frustrate users and generate helpdesk tickets. Categorizing failures by reason (auth, DHCP, association) points directly to the failing infrastructure component.

**Pipeline walkthrough**

• Selects only client events where `connectionStatus` or `onboardingStatus` equals FAILED to focus on error paths.
• `stats count as failure_count by failureReason, connectionType, ssid` groups failures for root-cause grouping.
• `sort -failure_count` lists the most frequent failure signatures first for triage.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions as required. Consider visualizations: Table (failureReason, connectionType, ssid, failure_count), bar chart of top failure reasons, alert when new dominant failure class appears.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:client" (connectionStatus="FAILED" OR onboardingStatus="FAILED") | stats count as failure_count by failureReason, connectionType, ssid | sort -failure_count
```

## Visualization

Table (failureReason, connectionType, ssid, failure_count), bar chart of top failure reasons, alert when new dominant failure class appears.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
