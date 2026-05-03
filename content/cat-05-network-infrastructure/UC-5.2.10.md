<!-- AUTO-GENERATED from UC-5.2.10.json — DO NOT EDIT -->

---
id: "5.2.10"
title: "Admin Access Audit"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.10 · Admin Access Audit

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Compliance

*We follow who signs into the firewall itself so we can catch stolen sessions, after-hours access, and missing change records.*

---

## Description

Firewall admin access is highly privileged. Audit trail is a compliance must-have.

## Value

Security teams audit firewall admin access attempts, detecting brute force attacks, suspicious external logins, and successful authentication following multiple failures.

## Implementation

Forward system/auth logs. Alert on failed admin logins. Track all successful logins. Alert on unexpected source IPs.

## Detailed Implementation

### Prerequisites
* Firewall management access logs. Palo Alto: `sourcetype=pan:system` (login events), Fortinet: `sourcetype=fgt_event` (admin events), Cisco FTD: admin login events. Key fields: `user`/`admin`, `src_ip`, `action` (login-success/login-fail), `auth_method`.
* Admin access audit tracks: (1) who accessed the firewall, (2) from where, (3) authentication method, (4) failed login attempts.

### Step 1 — - Configure data collection
Verify admin login events:
```spl
index=firewall earliest=-24h
| where match(_raw, "(?i)admin.*login|auth.*success|auth.*fail|login.*success|login.*fail|management.*session")
| stats count by sourcetype, host
```

### Step 2 — - Create the search and alert

**Primary search -- Admin access audit:**
```spl
index=firewall earliest=-24h
| where match(_raw, "(?i)admin.*login|auth.*(success|fail)|login.*(success|fail)|management.*session|web.*ui.*login|cli.*login|api.*login")
| eval login_result=case(match(_raw, "(?i)success|succeeded|authenticated"), "SUCCESS", match(_raw, "(?i)fail|denied|rejected|invalid|wrong"), "FAILURE", 1==1, "OTHER")
| eval admin_user=coalesce(user, admin, src_user)
| eval admin_src=coalesce(src_ip, src, srcaddr)
| eval method=case(match(_raw, "(?i)web|https|gui|UI"), "Web-UI", match(_raw, "(?i)cli|ssh|console"), "CLI/SSH", match(_raw, "(?i)api|rest|xml"), "API", 1==1, "Unknown")
| stats count as attempts count(eval(login_result="FAILURE")) as failures count(eval(login_result="SUCCESS")) as successes latest(_time) as last_attempt by admin_user, admin_src, method, host
| eval failure_rate=if(attempts > 0, round(100*failures/attempts, 1), 0)
| eval severity=case(failures > 10 AND successes=0, "CRITICAL -- brute force (no success)", failures > 5 AND successes > 0, "HIGH -- multiple failures then success (possible compromise)", match(admin_src, "^(10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.)") = 0 AND successes > 0, "WARNING -- external admin access", 1==1, "INFO")
| where severity != "INFO"
| sort severity, -failures
```

### Step 3 — - Validate
(a) Attempt a failed login and verify it appears in Splunk.
(b) Compare with firewall audit: Palo Alto `show admins all`, Fortinet `get system admin`.
(c) Verify source IP attribution -- some firewalls log the management interface IP, not the admin client IP.

### Step 4 — - Operationalize
Dashboard ("Firewall -- Admin Access Audit"):
* Row 1 -- Single-value: "Failed logins (24h)", "Successful logins", "External admin access", "Unique admin IPs".
* Row 2 -- Admin login events table with failure analysis.

Alerting:
* Critical (> 10 failures with no success): brute force attempt.
* High (failures followed by success): potential account compromise.
* Warning (successful login from external IP): verify authorized remote admin.

### Step 5 — - Troubleshooting

* **Brute force on admin interface** -- Restrict management access: (1) limit to specific IPs, (2) enable MFA for admin access, (3) lockout after N failed attempts, (4) use RADIUS/TACACS+ with accounting.

* **Admin user unknown** -- API or service account access may use different usernames. Check: API key configuration, service accounts in identity management.

* **External admin login** -- If not expected, check: (1) management interface is not exposed to internet, (2) VPN is required for remote admin access, (3) IP belongs to a known admin location.

## SPL

```spl
index=firewall sourcetype="pan:system" ("login" OR "logout" OR "auth")
| eval status=case(match(_raw,"success"),"Success", match(_raw,"fail"),"Failed", 1=1,"Other")
| stats count by admin_user, src, status | sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  by Authentication.user Authentication.action Authentication.src Authentication.app span=1h
| sort -count
```

## Visualization

Table (admin, source, status), Timeline, Bar chart.

## Known False Positives

Scheduled automation, help desk remotes, and break-glass access from new locations can look unusual without being malicious.

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
