<!-- AUTO-GENERATED from UC-5.13.48.json — DO NOT EDIT -->

---
id: "5.13.48"
title: "Failed API/Login Attempt Detection"
status: "verified"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.13.48 · Failed API/Login Attempt Detection

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security, Audit &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch for repeated failed login attempts on the network management system — the kind of pattern that means someone is trying to guess passwords or break in. When we see too many failures from the same account, we alert your security team immediately so they can check whether the account has been compromised.*

---

## Description

Detects failed API authentication and login attempts against the Catalyst Center platform, identifying potential brute-force attacks, credential stuffing, or misconfigured service accounts — the first signal of a credential compromise attempt against the network management plane.

## Value

Failed login attempts are the first indicator of a credential attack. A single failure is a typo. Five failures in 10 minutes is a brute-force attempt. Failed API authentication from an unexpected source is a compromised credential being tested from an attacker's infrastructure. This UC catches all three patterns and provides the evidence for NIST AC-7 (Unsuccessful Logon Attempts). Since Catalyst Center controls the configuration of every managed network device, a compromised Catalyst Center account is a network-wide compromise — detection must be fast and reliable.

## Implementation

Same `audit_logs` input as UC-5.13.45. Text search for authentication failure indicators. Alert on > 3 failures from the same user within the search window. Schedule every 15 minutes.

## Detailed Implementation

### Prerequisites
- UC-5.13.45 (Audit Log Overview) must be operational — same `audit_logs` data feed.
- The exact field values or description text for failed logins depend on your Catalyst Center version. Common patterns: HTTP `401` in the response, `unauthorized` in the description, `authentication failed`, or `login failed`. Run `| search "fail" OR "error" OR "deny" OR "401" | stats count` to verify failed auth events are captured.
- For NIST AC-7, document your lockout policy: after how many failures does Catalyst Center lock the account? (Typically 5–10 attempts.) This UC detects the attack; the lockout policy prevents the compromise.

### Step 1 — Configure data collection
Same `audit_logs` input as UC-5.13.45. No additional configuration.

Confirm failed auth events are captured:
```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" earliest=-7d
| search "401" OR "unauthorized" OR "failed" OR "denied"
| stats count
```
If count > 0, the audit log captures authentication failures. If 0, either no failures occurred (good!) or the audit log doesn't capture them (check with a deliberate wrong-password test).

### Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" ("401" OR "unauthorized" OR "authentication failed" OR "login failed")
| stats count as failures earliest(_time) as first_attempt latest(_time) as last_attempt by auditUserName
| where failures > 3
| eval window_min=round((last_attempt-first_attempt)/60,1)
| eval rate=round(failures/max(window_min,1),1)
| sort -failures
```

Why text search for `401`/`unauthorized` instead of a field-based filter: the audit log may not have a dedicated `authResult` field. Text search catches the failure indicator regardless of which field contains it — `auditDescription`, HTTP response code in the event body, or a status field.

Why `failures > 3`: a single failure is a normal typo. Multiple failures in a short window indicate a systematic problem (brute force, misconfigured integration, expired credential).

Why `rate` (failures per minute): distinguishes manual password guessing (1/min) from automated brute-force (50/min). High rate = automated attack. Low rate = user struggling with password.

Schedule as Alert:
- Cron: `*/15 * * * *` (every 15 minutes)
- Time range: `-20m to now`
- Trigger: "Number of results > 0"
- Throttle: by `auditUserName` for `4h`
- Severity: Critical (for > 10 failures) or High (for 4–10 failures)

### Step 3 — Validate
(a) Intentional test: enter wrong credentials in Catalyst Center 5 times. Within 15 minutes, the alert should fire with your username and `failures=5`.
(b) Check that the TA service account's routine authentication doesn't generate false failures: `| search "splunk-svc" | stats count`. If count > 0, exclude the service account from the alert.
(c) Verify rate calculation: `rate > 5` (5+ failures per minute) indicates automated attack. `rate < 1` indicates manual attempts.
(d) Cross-reference with **Catalyst Center > System > Audit Logs** for authentication events.

### Step 4 — Operationalize
- Alert: page security operations for > 5 failures in 15 minutes. Include `auditUserName`, `failures`, `rate`, and `window_min`.
- Correlate with UC-5.13.49 (after-hours): failed login attempts at 3 AM are more suspicious than at 10 AM.
- For NIST AC-7: document the alert and the Catalyst Center lockout policy as complementary controls.
- SOX evidence: monthly failed-login report with investigation outcomes.

Runbook (owner: Security Operations):
1. Receive alert. Note `auditUserName`, `failures`, and `rate`.
2. If the username is a known service account (TA, ITSM integration): check if the password was recently rotated. Update the credential in the integration and close.
3. If the username is a human admin: contact the user. Was this them trying to log in? If yes, assist with password reset. If no, this is a potential credential compromise — proceed to step 4.
4. Compromise suspected: disable the Catalyst Center account immediately. Check recent audit activity for that user (UC-5.13.46). If they successfully logged in after the failures, investigate what they did. Escalate to the incident response team.
5. If `rate > 5` (automated attack): check source IP if available. Block at the network perimeter. Report to threat intelligence.

### Step 5 — Troubleshooting

- **No failed auth events found** — the audit log may not capture authentication failures explicitly. Try broader searches: `| search "fail" OR "error" OR "deny"`. Also test by entering wrong credentials and checking whether the event appears.

- **TA service account generates constant failures** — credential rotation issue. Update the password in the TA immediately: Configuration → Account → Edit.

- **Too many false positives** — raise the threshold from 3 to 5 failures. Or add a time-window constraint: `| where window_min < 30` to focus on rapid-fire attempts.

- **Can't identify the source IP** — the audit log may not include source IP for API calls. Check if the event contains `sourceIP`, `clientIP`, or `remoteAddress` fields.

- **Account locked out by Catalyst Center** — after N failures, Catalyst Center may lock the account. The TA will then fail every 5 minutes, generating a steady stream of failure events. Fix the credential or unlock the account.

- **Brute-force attack from internal IP** — an insider threat or compromised internal host. Escalate to the security incident response team.

- **Want to track successful logins alongside failures** — search `"login" OR "authenticated" OR "session"` without the failure keywords for a complete auth log.

- **Compliance reporting** — export failed login attempts monthly for NIST AC-7 and SOX ITGC access review evidence.

Additional operational context for Failed API/Login Attempt Detection:

For month-over-month comparison:
- Export the primary search results monthly as CSV to a `catalyst_monthly_snapshots` directory. Compare current month vs previous month to identify trends, improvements, and regressions.
- Track the key metric from this UC over 90 days with `| timechart span=1w` for the quarterly operations review.

For SLA alignment:
- Define the acceptable threshold for this UC's primary metric in your SLA documentation.
- Schedule a weekly check against the SLA target. Breaches should generate tickets in your ITSM with a link to this UC's dashboard panel for investigation context.

Cross-reference with related UCs:
- When this UC flags an issue, always cross-reference with UC-5.13.1 (Device Health) and UC-5.13.16 (Network Health) to assess the broader impact.
- For compliance-related findings, connect to UC-5.13.28-33 for the compliance posture context.
- For security-related findings, connect to UC-5.13.34-39 for PSIRT advisory exposure.

Runbook integration:
- Document the response procedure for each alert from this UC in your operations runbook.
- Include: who to contact, what to check first, typical root causes, and escalation criteria.
- Review and update the runbook quarterly based on actual alert outcomes (was the runbook helpful? did it miss common scenarios?).

Additional troubleshooting:
- If the search returns unexpected results, check `| fieldsummary` on the base data to verify field names and types match the SPL.
- If data is not arriving for the expected sourcetype, verify the TA input is enabled and check `index=_internal sourcetype=splunkd component=ExecProcessor "TA_cisco_catalyst"` for errors from the modular input.
- If field values changed after a Catalyst Center upgrade, compare `| fieldsummary` from before and after the upgrade to identify renamed or restructured fields.
- If the search is slow, narrow the time range to `earliest=-20m` for a real-time snapshot, or use summary indexing for historical analysis.
- For vendor UI parity, cross-reference the Splunk results with the corresponding **Catalyst Center > Assurance** page for the same time window to confirm counts and values match.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" ("401" OR "unauthorized" OR "authentication failed" OR "login failed")
| stats count as failures earliest(_time) as first_attempt latest(_time) as last_attempt by auditUserName
| where failures > 3
| eval window_min=round((last_attempt-first_attempt)/60,1)
| eval rate=round(failures/max(window_min,1),1)
| sort -failures
```

## Visualization

(1) Table: auditUserName, failures, window_min, rate — brute-force candidates. (2) Timechart: failed attempts over 24h. (3) Single value: failed attempts in last hour (red ≥ 5). (4) Alert: > 5 failures from same user in 15 minutes → page security ops.

## Known False Positives

**TA service account credential rotation causing temporary auth failures.** When the service account password is rotated in Catalyst Center but not yet updated in the TA, the TA's polling generates failed authentication attempts every 5 minutes. Distinguish by checking `auditUserName` — if it matches the TA service account, the password needs to be updated in the TA configuration. Suppress by updating the TA credential promptly during rotation.

**Expired certificate causing API authentication failures.** If the Catalyst Center API certificate expires or is replaced, the TA's SSL validation fails, generating authentication errors. Distinguish by checking `index=_internal sourcetype=splunkd "TA_cisco_catalyst" "SSL"` for certificate-related errors. Fix by updating the certificate trust or temporarily disabling SSL verification.

**User entering wrong password on first attempt.** A single failure followed by a success is a normal typo. Distinguish by checking whether `failures = 1` for the user. Suppress by requiring `failures > 3` before alerting (already in the default SPL).

**Shared service accounts generating failures from multiple integrations.** If multiple systems use the same API account and one is misconfigured, the misconfigured system generates failures while the others work. Distinguish by checking the source IP or client identifier in the audit event (if available). Fix by using separate service accounts per integration.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Audit Log API](https://developer.cisco.com/docs/catalyst-center/#!get-audit-log-records)
- [Catalyst Center Integration Guide (this repo)](../../docs/guides/catalyst-center.md)
- [NIST SP 800-53 Rev. 5 — AC-7 Unsuccessful Logon Attempts](https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=AC-7)
