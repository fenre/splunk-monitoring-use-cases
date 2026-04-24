---
id: "5.13.48"
title: "Failed API/Login Attempt Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.13.48 · Failed API/Login Attempt Detection

## Description

Detects multiple failed login or API authentication attempts against Catalyst Center, which may indicate brute-force attacks or misconfigured integrations.

## Value

Failed authentication attempts are a primary indicator of credential attacks. Detecting them early enables account lockout and IP blocking before a breach occurs.

## Implementation

Enable the `audit_logs` input in the Cisco Catalyst TA pointing to `index=catalyst`. The TA polls audit log data from the Catalyst Center Intent API `/dna/intent/api/v1/audit/logs` every 5 minutes. Key fields: `auditRequestType`, `auditDescription`, `auditUserName`, `auditTimestamp`, `auditIpAddress`.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:audit:logs (Catalyst Center audit; auth-related request types and failure substrings in auditDescription).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable the `audit_logs` input in the Cisco Catalyst TA pointing to `index=catalyst`. The TA polls audit log data from the Catalyst Center Intent API `/dna/intent/api/v1/audit/logs` every 5 minutes. Key fields: `auditRequestType`, `auditDescription`, `auditUserName`, `auditTimestamp`, `auditIpAddress`.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" (auditRequestType="*LOGIN*" OR auditRequestType="*AUTH*") (auditDescription="*fail*" OR auditDescription="*denied*" OR auditDescription="*error*" OR auditDescription="*invalid*") | stats count as failed_attempts by auditUserName, auditIpAddress | where failed_attempts > 3 | sort -failed_attempts
```

Understanding this SPL

**Failed API/Login Attempt Detection** — Failed authentication attempts are a primary indicator of credential attacks. Detecting them early enables account lockout and IP blocking before a breach occurs.

**Pipeline walkthrough**

• Keeps authentication-related `auditRequestType` values and failure markers in `auditDescription` to reduce noise from successful actions.
• `stats` tallies `failed_attempts` per `auditUserName` and `auditIpAddress` in the current search window; tighten with `bin` on `_time` for short-window brute-force use cases.
• `where failed_attempts > 3` applies a simple threshold; tune the number to match NIST, SOC, and IdP lockout policy.
• `sort -failed_attempts` prioritises the highest-risk sources for blocking or case creation.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions as required. Consider visualizations: Table (auditUserName, auditIpAddress, failed_attempts), map of source IP if you enrich, alert when threshold is exceeded in a short window (use a shorter `stats` or `bin` in production).

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" (auditRequestType="*LOGIN*" OR auditRequestType="*AUTH*") (auditDescription="*fail*" OR auditDescription="*denied*" OR auditDescription="*error*" OR auditDescription="*invalid*") | stats count as failed_attempts by auditUserName, auditIpAddress | where failed_attempts > 3 | sort -failed_attempts
```

## Visualization

Table (auditUserName, auditIpAddress, failed_attempts), map of source IP if you enrich, alert when threshold is exceeded in a short window (use a shorter `stats` or `bin` in production).

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
