<!-- AUTO-GENERATED from UC-5.4.34.json — DO NOT EDIT -->

---
id: "5.4.34"
title: "Aruba ClearPass RADIUS Authentication Health (HPE Aruba)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.4.34 · Aruba ClearPass RADIUS Authentication Health (HPE Aruba)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security, Availability

*We watch aruba clearpass radius authentication health (hpe aruba) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

ClearPass Policy Manager is the authentication backbone for Aruba wireless networks, handling 802.1X, MAC auth, and captive portal. RADIUS authentication failures, timeouts, and server unreachability directly prevent users from connecting. Track auth success/failure ratios, latency, and server health.

## Value

Network security teams track Aruba ClearPass RADIUS authentication health, classifying failures by root cause (expired certificates, unknown users, timeouts) to maintain wireless access SLAs.

## Implementation

Ingest ClearPass access tracker and RADIUS-related logs via the ClearPass app. Normalize `Accept`/`Reject`/`Challenge` and timeout/unreachable patterns. Alert when reject rate or timeouts spike versus baseline, or when average RADIUS latency exceeds policy (e.g. 500ms). Segment by `nas_ip` (controller/AP cluster) to isolate WLAN vs ClearPass issues.

## Detailed Implementation

### Prerequisites
- HPE Aruba ClearPass App for Splunk (Splunkbase 7865) installed, receiving ClearPass Policy Manager access tracker logs. Data in `index=network` with `sourcetype=aruba:clearpass`. Key fields: `Enforcement_Result` or `Auth_Result` (Accept/Reject/Challenge), `radius_server`, `nas_ip` (NAS / controller IP), `request_latency_ms` or `Radius_Request_Time`, `username`, `client_mac`, `Service` (802.1X, MAC Auth, Web Login), `Auth_Source` (AD, LDAP, Local DB), `Roles` or `TipsRole`.
- ClearPass handles three authentication methods for Aruba wireless: (1) 802.1X (EAP-TLS, PEAP-MSCHAPv2) for corporate devices, (2) MAC Authentication Bypass (MAB) for IoT/printers, (3) Web Login (captive portal) for guests. Each method has different failure modes.

### Step 1 — Configure data collection
Configure ClearPass to send syslog or use the API export:
1. ClearPass Policy Manager > Administration > External Servers > Syslog Targets: Add Splunk syslog receiver.
2. Administration > External Servers > Syslog Export Filters: Enable "Session Log" and "RADIUS Accounting" export.
3. Alternatively, use ClearPass Insight API for richer data.

Verify data in Splunk:
```spl
index=network sourcetype="aruba:clearpass" earliest=-4h
| stats count by Service, Auth_Source
```

### Step 2 — Create the search and alert

**Primary search — RADIUS authentication health with root cause classification:**
```spl
index=network sourcetype="aruba:clearpass" ("RADIUS" OR TipsService="RADIUS" OR module="RADIUS") earliest=-4h
| eval result=coalesce(Enforcement_Result, Auth_Result, Status, if(match(_raw, "Access-Accept"), "Accept", if(match(_raw, "Access-Reject"), "Reject", null())))
| rex field=_raw max_match=0 "(?i)Access-(?<radius_reply>Accept|Reject|Challenge)"
| eval outcome=coalesce(result, radius_reply)
| eval latency_ms=coalesce(request_latency_ms, Radius_Request_Time, elapsed_ms, duration_ms)
| eval is_timeout=if(match(_raw, "(?i)timeout|timed out|server.unreachable|no.response.from"), 1, 0)
| eval failure_reason=case(match(_raw, "(?i)expired.*cert"), "EXPIRED_CERTIFICATE", match(_raw, "(?i)unknown.*user|not.found"), "UNKNOWN_USER", match(_raw, "(?i)wrong.*password|bad.*password|invalid.*cred"), "BAD_PASSWORD", match(_raw, "(?i)disabled|locked"), "ACCOUNT_DISABLED", match(_raw, "(?i)policy.*reject|no.*matching.*service"), "POLICY_REJECT", is_timeout=1, "RADIUS_TIMEOUT", like(outcome, "%Reject%"), "OTHER_REJECT", 1==1, null())
| stats count as events sum(is_timeout) as timeouts avg(latency_ms) as avg_latency_ms dc(username) as affected_users by outcome, failure_reason, radius_server, nas_ip
| eval severity=case(timeouts > 10, "CRITICAL — RADIUS server timeout", failure_reason="EXPIRED_CERTIFICATE" AND affected_users > 5, "HIGH — Certificate issue", affected_users > 20, "HIGH — Mass failure", avg_latency_ms > 1000, "WARNING — Slow RADIUS", 1==1, "INFO")
| where like(outcome, "%Reject%") OR like(lower(outcome), "%fail%") OR timeouts > 0 OR avg_latency_ms > 500
| sort severity, -events
```

**Authentication availability (SLA tracking):**
```spl
index=network sourcetype="aruba:clearpass" ("RADIUS" OR TipsService="RADIUS") earliest=-24h
| eval outcome=coalesce(Enforcement_Result, Auth_Result, if(match(_raw, "Access-Accept"), "Accept", if(match(_raw, "Access-Reject"), "Reject", null())))
| bin _time span=15m
| stats count(eval(outcome="Accept")) as accepts count(eval(like(outcome, "%Reject%"))) as rejects count as total by _time, radius_server
| eval availability_pct=round(100*accepts/total, 2)
| timechart span=15m avg(availability_pct) by radius_server
```

### Step 3 — Validate
(a) Log in with an invalid password on the corporate SSID and verify the "BAD_PASSWORD" failure appears in Splunk.
(b) Check ClearPass Access Tracker (Monitoring > Live Monitoring > Access Tracker) for the same time window and compare event counts.
(c) Verify RADIUS latency: ClearPass > Monitoring > System Health > RADIUS Latency — compare with Splunk-reported `avg_latency_ms`.

### Step 4 — Operationalize
Dashboard ("Aruba ClearPass — RADIUS Health"):
- Row 1 — Single-value tiles: "Auth availability %", "Total auths (4h)", "Reject count", "RADIUS timeouts", "Avg latency (ms)".
- Row 2 — Failure classification table: reason, affected users, RADIUS server, NAS.
- Row 3 — Authentication availability trending by RADIUS server.

Alerting:
- Critical (RADIUS timeouts > 10 in 5 min): RADIUS server unreachable — all new wireless connections will fail.
- High (Reject rate > 20% with > 50 attempts in 15 min): mass auth failure.
- Warning (avg RADIUS latency > 500 ms): slow authentication — user experience degradation.

### Step 5 — Troubleshooting

- **Mass RADIUS timeouts** — ClearPass server may be down or overloaded. Check: (1) ClearPass service status: `service cppm-server status`, (2) Network connectivity between controller and ClearPass, (3) Firewall rules for UDP 1812/1813.

- **"EXPIRED_CERTIFICATE" spike** — Client machine certificates have expired. This is common after a certificate lifecycle change. Check: ClearPass > Configuration > Certificate Store, and coordinate with PKI team for certificate renewal.

- **"UNKNOWN_USER" failures** — Users not in the authentication source (AD/LDAP). Check: (1) AD connectivity from ClearPass, (2) Service configuration points to the correct AD domain, (3) Username format (UPN vs sAMAccountName).

## SPL

```spl
index=network sourcetype="aruba:clearpass" ("RADIUS" OR TipsService="RADIUS" OR module="RADIUS")
| eval result=coalesce(Enforcement_Result, Auth_Result, Status, if(match(_raw,"Access-Accept"),"Accept",if(match(_raw,"Access-Reject"),"Reject",null())))
| rex field=_raw max_match=0 "(?i)Access-(?<radius_reply>Accept|Reject|Challenge)"
| eval outcome=coalesce(result, radius_reply)
| eval latency_ms=coalesce(request_latency_ms, Radius_Request_Time, elapsed_ms, duration_ms)
| eval is_timeout=if(match(_raw,"(?i)timeout|timed out|server.unreachable|no.response.from"),1,0)
| stats count as events, sum(is_timeout) as timeouts, avg(latency_ms) as avg_latency_ms by outcome, radius_server, nas_ip
| where like(outcome,"%Reject%") OR like(lower(outcome),"%fail%") OR timeouts>0 OR avg_latency_ms>500
| sort -events
```

## Visualization

Timechart (accept vs reject vs timeout), Bar chart (outcomes by NAS), Table (radius_server, NAS, latency, counts), Single value (auth availability %).

## Known False Positives

Failed logins often come from typos, expired passwords, guest self-service, or a single misconfigured device; treat sustained rises across many users as the real signal.

## References

- [Splunkbase app 7865](https://splunkbase.splunk.com/app/7865)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
