<!-- AUTO-GENERATED from UC-5.4.8.json — DO NOT EDIT -->

---
id: "5.4.8"
title: "RADIUS Authentication Failures"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.4.8 · RADIUS Authentication Failures

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security

*We watch radius authentication failures so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Mass RADIUS failures prevent wireless users from connecting. Distinguishing between user errors and server issues drives faster resolution.

## Value

Network operations teams analyze RADIUS authentication failures by category (certificate, credential, server, policy) to rapidly distinguish between infrastructure issues affecting all users and individual user problems.

## Implementation

Forward ISE/RADIUS logs to Splunk. Alert when failure rate exceeds 20% of attempts. Distinguish between bad credentials, expired certificates, and server timeouts.

## Detailed Implementation

### Prerequisites
- RADIUS server logs (Cisco ISE, Aruba ClearPass, Microsoft NPS, FreeRADIUS) forwarded to Splunk. Data in `index=radius` (or `index=network`) with vendor-specific sourcetypes: `sourcetype=cisco:ise:auth` (ISE), `sourcetype=clearpass:auth` (ClearPass), `sourcetype=nps` (Microsoft NPS).
- Key fields: `username`, `client_mac` (calling station ID), `nas_ip` (authenticator/WLC IP), `auth_result` (PASS/FAIL), `failure_reason`, `eap_type` (PEAP, EAP-TLS, EAP-FAST), `auth_policy`, `network_device_name`.
- Build `radius_servers.csv` lookup: `server_ip,server_name,role,location` for health tracking.

### Step 1 — Configure data collection
Verify RADIUS authentication data:
```spl
index=radius earliest=-4h
| stats count by sourcetype, auth_result
```

### Step 2 — Create the search and alert

**Primary search — RADIUS failure analysis:**
```spl
index=radius auth_result="FAIL" earliest=-4h
| stats count as failures dc(username) as affected_users dc(client_mac) as affected_devices values(failure_reason) as reasons by nas_ip, eap_type, auth_policy
| eval severity=case(failures > 100 AND affected_users > 20, "CRITICAL", failures > 50, "HIGH", failures > 10, "MEDIUM", 1==1, "LOW")
| eval failure_category=case(match(mvjoin(reasons, ","), "(?i)certificate"), "CERT_ISSUE", match(mvjoin(reasons, ","), "(?i)timeout|unreachable"), "SERVER_UNREACHABLE", match(mvjoin(reasons, ","), "(?i)password|credential"), "BAD_CREDENTIALS", match(mvjoin(reasons, ","), "(?i)policy|authorization"), "POLICY_DENIED", 1==1, "OTHER")
| sort severity, -failures
```

#### Understanding this SPL: RADIUS failure categories determine the fix. CERT_ISSUE: the RADIUS server certificate or the client's supplicant certificate has expired or is untrusted. SERVER_UNREACHABLE: the RADIUS server is down or the WLC can't reach it (network issue, firewall). BAD_CREDENTIALS: user has wrong password or account is locked. POLICY_DENIED: user is authenticated but not authorized for the requested network.

**RADIUS server response time:**
```spl
index=radius earliest=-4h
| where isnotnull(response_time)
| stats avg(response_time) as avg_ms p95(response_time) as p95_ms max(response_time) as max_ms by server_ip
| lookup radius_servers.csv server_ip OUTPUT server_name
| eval status=case(p95_ms > 2000, "CRITICAL", p95_ms > 500, "WARNING", 1==1, "OK")
| sort -p95_ms
```

**Per-user failure tracking (account lockout detection):**
```spl
index=radius auth_result="FAIL" earliest=-1h
| stats count as failures dc(nas_ip) as auth_sources dc(client_mac) as devices by username
| where failures > 5
| eval risk=case(failures > 50, "BRUTE_FORCE_SUSPECTED", failures > 20, "HIGH", 1==1, "INVESTIGATE")
| sort -failures
```

### Step 3 — Validate
(a) Intentionally enter wrong credentials on a wireless 802.1X network and verify the failure appears in Splunk.
(b) Compare RADIUS authentication statistics with the RADIUS server's own reports (ISE Live Logs, ClearPass Access Tracker).
(c) Test RADIUS server failover: stop the primary RADIUS server and verify clients authenticate via the secondary.

### Step 4 — Operationalize
Dashboard ("RADIUS Authentication"):
- Row 1 — Single-value tiles: "Auth success rate", "Total failures (4h)", "Affected users", "RADIUS server status".
- Row 2 — Failure analysis table: authenticator, EAP type, failures, affected users, category, severity.
- Row 3 — RADIUS server response times.
- Row 4 — Per-user failure tracking (potential brute force).

Alerting:
- Critical (RADIUS failure rate > 20% and > 20 affected users): widespread authentication outage.
- Critical (RADIUS server unreachable): all 802.1X authentication will fail — users can't connect.
- High (per-user failures > 50 in 1 hour): possible brute force attack.

### Step 5 — Troubleshooting

- **Mass RADIUS failures with "certificate" reason** — The RADIUS server's EAP certificate has expired. Check: ISE > Administration > Certificates > System Certificates, or ClearPass > Administration > Certificates. Renew the certificate immediately.

- **Failures from specific NAS IP only** — The WLC at that NAS IP may have the wrong RADIUS shared secret. Verify the shared secret on both the WLC and RADIUS server match exactly.

- **High response time from RADIUS** — The RADIUS server may be overloaded, or there's an LDAP/AD backend latency issue. Check server CPU, memory, and backend directory response times.

## SPL

```spl
index=network sourcetype="cisco:ise:syslog" "Authentication failed"
| rex "UserName=(?<username>\S+).*?FailureReason=(?<reason>[^;]+)"
| stats count by reason, username | sort -count
| head 20
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  by Authentication.user Authentication.action Authentication.src Authentication.app span=1h
| sort -count
```

## Visualization

Bar chart (failure reasons), Table (username, reason, count), Timechart (failure rate).

## Known False Positives

Failed logins often come from typos, expired passwords, guest self-service, or a single misconfigured device; treat sustained rises across many users as the real signal.

## References

- [Splunk_TA_cisco-ise](https://splunkbase.splunk.com/app/1915)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
