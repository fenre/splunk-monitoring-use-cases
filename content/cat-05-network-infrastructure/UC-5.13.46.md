---
id: "5.13.46"
title: "Configuration Change Audit Trail"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.13.46 · Configuration Change Audit Trail

## Description

Tracks all configuration changes made through Catalyst Center, including template deployments, provisioning actions, and policy changes.

## Value

Configuration changes are the leading cause of network outages. A complete audit trail enables rapid rollback and root-cause identification.

## Implementation

Enable the `audit_logs` input in the Cisco Catalyst TA pointing to `index=catalyst`. The TA polls audit log data from the Catalyst Center Intent API `/dna/intent/api/v1/audit/logs` every 5 minutes. Key fields: `auditRequestType`, `auditDescription`, `auditUserName`, `auditTimestamp`, `auditIpAddress`.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:audit:logs (Catalyst Center audit; configuration, provisioning, template-related auditRequestType values).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable the `audit_logs` input in the Cisco Catalyst TA pointing to `index=catalyst`. The TA polls audit log data from the Catalyst Center Intent API `/dna/intent/api/v1/audit/logs` every 5 minutes. Key fields: `auditRequestType`, `auditDescription`, `auditUserName`, `auditTimestamp`, `auditIpAddress`.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" (auditRequestType="CONFIG*" OR auditRequestType="*PROVISION*" OR auditRequestType="*TEMPLATE*") | stats count as change_count values(auditDescription) as actions by auditUserName, auditIpAddress | sort -change_count
```

Understanding this SPL

**Configuration Change Audit Trail** — Configuration changes are the leading cause of network outages. A complete audit trail enables rapid rollback and root-cause identification.

**Pipeline walkthrough**

• Uses wildcard filters on `auditRequestType` to keep configuration, provisioning, and template activities.
• `stats` counts changes per `auditUserName` and `auditIpAddress` and lists distinct `auditDescription` values in the `actions` multivalue field.
• `sort -change_count` surfaces the heaviest changers for review or approval alignment.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions as required. Consider visualizations: Table (auditUserName, auditIpAddress, change_count, actions), timechart of config-related events, drilldown to raw events for ticket correlation.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" (auditRequestType="CONFIG*" OR auditRequestType="*PROVISION*" OR auditRequestType="*TEMPLATE*") | stats count as change_count values(auditDescription) as actions by auditUserName, auditIpAddress | sort -change_count
```

## Visualization

Table (auditUserName, auditIpAddress, change_count, actions), timechart of config-related events, drilldown to raw events for ticket correlation.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
