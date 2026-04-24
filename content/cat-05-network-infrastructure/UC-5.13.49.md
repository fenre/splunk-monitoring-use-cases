---
id: "5.13.49"
title: "After-Hours Administrative Activity"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.13.49 · After-Hours Administrative Activity

## Description

Identifies administrative actions performed outside normal business hours (before 6am, after 10pm, or on weekends), which may indicate unauthorized access.

## Value

After-hours admin activity is a common indicator of insider threats, compromised accounts, or unauthorized maintenance. Flagging it enables rapid investigation.

## Implementation

Enable the `audit_logs` input in the Cisco Catalyst TA pointing to `index=catalyst`. The TA polls audit log data from the Catalyst Center Intent API `/dna/intent/api/v1/audit/logs` every 5 minutes. Key fields: `auditRequestType`, `auditDescription`, `auditUserName`, `auditTimestamp`, `auditIpAddress`.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:audit:logs (Catalyst Center /dna/intent/api/v1/audit/logs; all administrative audit events with timestamps).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable the `audit_logs` input in the Cisco Catalyst TA pointing to `index=catalyst`. The TA polls audit log data from the Catalyst Center Intent API `/dna/intent/api/v1/audit/logs` every 5 minutes. Key fields: `auditRequestType`, `auditDescription`, `auditUserName`, `auditTimestamp`, `auditIpAddress`.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" | eval hour=strftime(_time, "%H") | eval day=strftime(_time, "%a") | where (hour<6 OR hour>22) OR (day="Sat" OR day="Sun") | stats count as after_hours_actions values(auditRequestType) as action_types by auditUserName, auditIpAddress | sort -after_hours_actions
```

Understanding this SPL

**After-Hours Administrative Activity** — After-hours admin activity is a common indicator of insider threats, compromised accounts, or unauthorized maintenance. Flagging it enables rapid investigation.

**Pipeline walkthrough**

• Ingests all audit log events, then `eval` derives hour (24h string) and weekday abbreviation from event time.
• `where` keeps only late night, very early morning, or weekend work based on the stated policy; adjust to your time zone and business hours.
• `stats` totals actions and lists `auditRequestType` values for each `auditUserName` and `auditIpAddress`.
• `sort -after_hours_actions` shows the heaviest out-of-band usage first for triage with the identity team.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions as required. Consider visualizations: Table (auditUserName, auditIpAddress, after_hours_actions, action_types), timeline panel for manual review, optional alert to SOC when a known admin baseline changes.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" | eval hour=strftime(_time, "%H") | eval day=strftime(_time, "%a") | where (hour<6 OR hour>22) OR (day="Sat" OR day="Sun") | stats count as after_hours_actions values(auditRequestType) as action_types by auditUserName, auditIpAddress | sort -after_hours_actions
```

## Visualization

Table (auditUserName, auditIpAddress, after_hours_actions, action_types), timeline panel for manual review, optional alert to SOC when a known admin baseline changes.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
