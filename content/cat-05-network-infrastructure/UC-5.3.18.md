<!-- AUTO-GENERATED from UC-5.3.18.json — DO NOT EDIT -->

---
id: "5.3.18"
title: "Citrix Gateway / VPN Session Monitoring (NetScaler)"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.3.18 · Citrix Gateway / VPN Session Monitoring (NetScaler)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security, Capacity

*We follow remote access and session style events so a spike in failed logins or a quiet gateway is something you can explain with data.*

---

## Description

Citrix Gateway (NetScaler Gateway) provides SSL VPN access and ICA Proxy functionality for remote Citrix session launches. Monitoring active Gateway sessions provides visibility into remote user activity, concurrent connection counts (license-relevant), authentication failures (brute force detection), and session anomalies (impossible travel, excessive bandwidth). Gateway is the perimeter entry point for all remote Citrix access, making it security-critical.

## Value

Infrastructure teams monitor Citrix Gateway VPN session health including authentication success rates, EPA compliance failures, and session timeouts, ensuring remote worker access reliability.

## Implementation

The ADC logs all AAA (Authentication, Authorization, Accounting) events via syslog, including Gateway login successes, failures, and logouts with client IP and username. Configure syslog with appflow and audit logging enabled. Alert on: authentication failure rate exceeding 30% (possible brute force), concurrent sessions exceeding licensed capacity, a single source IP attempting more than 20 failed logins in 15 minutes, or unusual login times/locations for known users. Track peak concurrent Gateway sessions for capacity planning.

## Detailed Implementation

### Prerequisites
* Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`, Splunkbase 2770). Citrix Gateway (formerly NetScaler Gateway) VPN session logs in `index=netscaler` with `sourcetype=citrix:netscaler:syslog`. Key fields: `username`, `source_ip`, `session_id`, `vpn_action` (LOGIN/LOGOUT/TIMEOUT/FAILURE), `auth_method` (LDAP/RADIUS/SAML/Certificate), `client_type` (Citrix Workspace/Browser/EPA).
* Citrix Gateway provides: (1) ICA Proxy for Citrix Virtual Apps/Desktops, (2) Full SSL VPN tunnel, (3) Clientless VPN (browser-based), (4) Micro VPN (per-app VPN for mobile). Session failures block remote worker access.

### Step 1 — - Configure data collection
Ensure Citrix Gateway audit logging is enabled:
```
add audit syslogAction splunk_vpn <splunk_ip> -logLevel ALL
add audit syslogPolicy splunk_vpn_policy ns_true splunk_vpn
bind vpn global -policyName splunk_vpn_policy -priority 1
```
Verify:
```spl
index=netscaler sourcetype="citrix:netscaler:syslog" ("VPN" OR "ICA" OR "SSLVPN" OR "Gateway" OR "LOGIN" OR "LOGOUT") earliest=-4h
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- VPN session monitoring:**
```spl
index=netscaler sourcetype="citrix:netscaler:syslog" ("VPN" OR "ICA" OR "SSLVPN" OR "LOGIN" OR "LOGOUT" OR "TIMEOUT" OR "EPA") earliest=-4h
| eval action=case(match(_raw, "(?i)(login.*success|session.*created|user.*logged.in)"), "LOGIN", match(_raw, "(?i)(logout|session.*ended|disconnected)"), "LOGOUT", match(_raw, "(?i)(timeout|session.*expired)"), "TIMEOUT", match(_raw, "(?i)(fail|denied|reject|invalid)"), "FAILURE", match(_raw, "(?i)(epa.*fail|endpoint.*fail)"), "EPA_FAILURE", 1==1, null())
| where isnotnull(action)
| eval user=coalesce(username, user, User)
| eval src=coalesce(source_ip, client_ip, src_ip)
| eval failure_reason=case(action="FAILURE" AND match(_raw, "(?i)password"), "Bad password", action="FAILURE" AND match(_raw, "(?i)(locked|disabled)"), "Account locked/disabled", action="FAILURE" AND match(_raw, "(?i)(cert|certificate)"), "Certificate issue", action="EPA_FAILURE", "Endpoint compliance check failed", action="FAILURE", "Auth failure -- check logs", 1==1, null())
| stats count(eval(action="LOGIN")) as logins count(eval(action="FAILURE")) as failures count(eval(action="EPA_FAILURE")) as epa_fails count(eval(action="TIMEOUT")) as timeouts dc(user) as unique_users by host
| eval auth_success_pct=if((logins + failures) > 0, round(100*logins/(logins + failures), 1), "N/A")
| eval severity=case(auth_success_pct < 70 AND (logins + failures) > 20, "CRITICAL", failures > 50, "HIGH", epa_fails > 10, "WARNING", 1==1, "OK")
| where severity != "OK"
```

**Per-user failure analysis:**
```spl
index=netscaler sourcetype="citrix:netscaler:syslog" ("VPN" OR "SSLVPN") ("fail" OR "denied" OR "reject") earliest=-4h
| eval user=coalesce(username, user, User)
| eval src=coalesce(source_ip, client_ip)
| stats count as failures dc(src) as source_ips values(src) as ips latest(_time) as last_failure by user
| where failures > 3
| sort -failures
```

### Step 3 — - Validate
(a) Log in to Citrix Gateway and verify the LOGIN event appears in Splunk.
(b) Log in with wrong credentials and verify the FAILURE event with reason.
(c) On ADC CLI: `show vpn stats` -- compare active session count with Splunk.

### Step 4 — - Operationalize
Dashboard ("Citrix Gateway -- VPN Sessions"):
* Row 1 -- Single-value: "Active sessions", "Auth success rate", "Failures (4h)", "EPA failures", "Timeouts".
* Row 2 -- Overall authentication health.
* Row 3 -- Per-user failure analysis (top failed users).

Alerting:
* Critical (auth success rate < 70% with > 20 attempts): mass authentication failure.
* High (> 50 failures in 15 min): potential brute force or outage.
* Warning (EPA failures > 10): endpoint compliance blocking users.

### Step 5 — - Troubleshooting

* **Mass auth failures** -- Check: (1) LDAP/AD server connectivity: `show authentication ldapAction <action>`, (2) RADIUS server: `show authentication radiusAction <action>`, (3) DNS resolution for auth servers.

* **EPA failures** -- Endpoint Analysis checks device compliance (antivirus, OS version, etc.). Check: (1) EPA policy: `show vpn epaProfile`, (2) client EPA plugin version, (3) whether the policy requirements are realistic for the user population.

* **Sessions timing out prematurely** -- Check timeout settings: `show vpn sessionAction <action>` for `sessTimeout`, `forcedTimeout`. Citrix Gateway has separate timeouts for different client types.

## SPL

```spl
index=network sourcetype="citrix:netscaler:syslog" ("SSLVPN" OR "ICA" OR "AAA") ("LOGIN" OR "LOGOUT" OR "FAILURE")
| rex "User (?<user>\S+) - Client_ip (?<client_ip>\S+)"
| eval auth_result=case(match(_raw, "LOGIN"), "Success", match(_raw, "FAILURE"), "Failure", match(_raw, "LOGOUT"), "Logout", 1=1, "Other")
| bin _time span=15m
| stats sum(eval(if(auth_result="Success", 1, 0))) as logins,
  sum(eval(if(auth_result="Failure", 1, 0))) as failures,
  dc(user) as unique_users, dc(client_ip) as unique_ips by gateway_vserver, _time
| eval fail_pct=if((logins+failures)>0, round(failures/(logins+failures)*100,1), 0)
| where failures > 10 OR fail_pct > 30
| table _time, gateway_vserver, logins, failures, fail_pct, unique_users, unique_ips
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Sessions.All_Sessions
  by All_Sessions.user All_Sessions.src All_Sessions.dest All_Sessions.action span=1h
| sort -count
```

## Visualization

Timechart (logins vs failures), Bar chart (failures by source IP), Single value (concurrent sessions).

## Known False Positives

Travel peaks, class schedules, and remote-work days swing login volume without a breach.

## References

- [CIM: Network_Sessions](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Sessions)
