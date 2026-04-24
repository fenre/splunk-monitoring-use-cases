---
id: "5.13.47"
title: "Privileged User Activity Monitoring"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.13.47 · Privileged User Activity Monitoring

## Description

Monitors activity from privileged accounts (admins, super-admins) and user/role management actions to detect potential abuse or compromised credentials.

## Value

Privileged accounts can cause maximum damage. Monitoring their activity detects unauthorized use, credential compromise, and insider threats.

## Implementation

Enable the `audit_logs` input in the Cisco Catalyst TA pointing to `index=catalyst`. The TA polls audit log data from the Catalyst Center Intent API `/dna/intent/api/v1/audit/logs` every 5 minutes. Key fields: `auditRequestType`, `auditDescription`, `auditUserName`, `auditTimestamp`, `auditIpAddress`.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:audit:logs (Catalyst Center audit; user, role, permission, and admin-sounding auditRequestType values).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable the `audit_logs` input in the Cisco Catalyst TA pointing to `index=catalyst`. The TA polls audit log data from the Catalyst Center Intent API `/dna/intent/api/v1/audit/logs` every 5 minutes. Key fields: `auditRequestType`, `auditDescription`, `auditUserName`, `auditTimestamp`, `auditIpAddress`.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" (auditUserName="admin" OR auditRequestType="*USER*" OR auditRequestType="*ROLE*" OR auditRequestType="*PERMISSION*") | stats count as action_count dc(auditRequestType) as unique_actions values(auditRequestType) as action_types by auditUserName, auditIpAddress | sort -action_count
```

Understanding this SPL

**Privileged User Activity Monitoring** — Privileged accounts can cause maximum damage. Monitoring their activity detects unauthorized use, credential compromise, and insider threats.

**Pipeline walkthrough**

• Filters to likely privileged traffic: literal `admin` usernames and USER/ROLE/PERM-related request types (tune to your account naming standard).
• `stats` measures volume, unique action types, and lists raw `auditRequestType` values per `auditUserName` and `auditIpAddress` source pair.
• `sort -action_count` orders the noisiest or most active sources for follow-up or correlation with PAM and IdP tools.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions as required. Consider visualizations: Table (auditUserName, auditIpAddress, action_count, unique_actions, action_types), alert on spikes or new admin sources.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" (auditUserName="admin" OR auditRequestType="*USER*" OR auditRequestType="*ROLE*" OR auditRequestType="*PERMISSION*") | stats count as action_count dc(auditRequestType) as unique_actions values(auditRequestType) as action_types by auditUserName, auditIpAddress | sort -action_count
```

## Visualization

Table (auditUserName, auditIpAddress, action_count, unique_actions, action_types), alert on spikes or new admin sources.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
