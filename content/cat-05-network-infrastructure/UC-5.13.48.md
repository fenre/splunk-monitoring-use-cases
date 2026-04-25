<!-- AUTO-GENERATED from UC-5.13.48.json — DO NOT EDIT -->

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
• Cisco Catalyst Add-on (7538) with `cisco:dnac:audit:logs` for Catalyst **management plane** sign-in and API authentication attempts captured in audit.
• This is **not** a substitute for ISE, AD, or MFA logs—Catalyst may only see what its UI/API layer records. Combine evidence sources in SOC runbooks.
• For true brute-force use cases, add `| bin _time span=5m` and count within each bucket before the `>3` test; a single unbounded `stats` can merge days of noise into one total.
• `docs/implementation-guide.md` and `docs/guides/catalyst-center.md`.

Step 1 — Configure data collection
• Review 50 `auditDescription` samples that match `*fail*` to confirm the strings are real auth failures, not spurious `error` text.

Step 2 — Failed attempt prototype
```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" (auditRequestType="*LOGIN*" OR auditRequestType="*AUTH*") (auditDescription="*fail*" OR auditDescription="*denied*" OR auditDescription="*error*" OR auditDescription="*invalid*") | stats count as failed_attempts by auditUserName, auditIpAddress | where failed_attempts > 3 | sort -failed_attempts
```

Understanding this SPL (Catalyst control plane)
**Failed API / login (heuristic)** — Reduces the audit stream to likely authentication-related `auditRequestType` values and failure-like substrings in `auditDescription`. Tighten to explicit Cisco message codes when your build documents them, and time-bucket for AC-7 style rate-based alerting.

**Pipeline walkthrough**
• Filter auth-ish types and text patterns → per `auditUserName`+`auditIpAddress` `count` → `where` threshold → `sort` by failures.

Step 3 — Validate
• In a lab, intentionally fail login and confirm one raw event and its `auditDescription` field; adjust substrings to avoid double-counting “error” in non-auth contexts.

Step 4 — Operationalize (SOC)
• Enrich `auditIpAddress` with your RFC1918, VPN, and partner ranges; different responses for on-net vs off-net. Create allowlists for health-check and backup accounts that re-auth by design.

Step 5 — Troubleshooting
• Zero rows: Catalyst may encode failures without those keywords—`| stats count by auditRequestType, auditDescription` to rebuild filters after upgrade. Too many rows: add `bin` to `_time` and require multiple buckets above threshold, or raise the numeric `>3` in line with IdP lockout policy.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" (auditRequestType="*LOGIN*" OR auditRequestType="*AUTH*") (auditDescription="*fail*" OR auditDescription="*denied*" OR auditDescription="*error*" OR auditDescription="*invalid*") | stats count as failed_attempts by auditUserName, auditIpAddress | where failed_attempts > 3 | sort -failed_attempts
```

## Visualization

Table (auditUserName, auditIpAddress, failed_attempts), map of source IP if you enrich, alert when threshold is exceeded in a short window (use a shorter `stats` or `bin` in production).

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
