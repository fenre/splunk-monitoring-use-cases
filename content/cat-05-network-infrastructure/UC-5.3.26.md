<!-- AUTO-GENERATED from UC-5.3.26.json — DO NOT EDIT -->

---
id: "5.3.26"
title: "Citrix ADC nFactor Authentication Pipeline Failures"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.3.26 · Citrix ADC nFactor Authentication Pipeline Failures

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Availability, Security

*We look at login and factor style failures in one chain so a broken factor, a bad schema, and a user typo are not all the same in the dark.*

---

## Description

Citrix ADC nFactor ties multiple authentication steps (VPN, web apps, user directories, SAML) into one pipeline. Login schema parse errors, per-factor timeouts, SAML attribute or assertion mismatches, or IdP reachability issues strand users in partial login states. Tracking these failures protects both availability (users cannot sign in) and security (forced fallbacks, repeated attempts, or mis-issued factors).

## Value

Identity teams monitor Citrix ADC nFactor multi-step authentication pipeline failures, identifying which specific factor (LDAP, RADIUS/MFA, SAML, certificate) is blocking user authentication.

## Implementation

Send AAA, audit, and authentication-related syslog to `index=netscaler` as `citrix:netscaler:syslog`. Classify by factor type (SAML, LDAP, RADIUS, EPA). Alert on growing failure rates for a given policy, IdP down messages, and schema errors after config pushes. Cross-reference with change records for nFactor flow edits.

## Detailed Implementation

### Prerequisites
* Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`, Splunkbase 2770). Citrix ADC nFactor authentication pipeline logs. Key fields: `nfactor_flow`, `factor_name`, `auth_method` (LDAP/RADIUS/SAML/OAuth/Certificate), `result` (SUCCESS/FAILURE), `username`, `factor_order`, `error_reason`.
* nFactor authentication: Citrix ADC's multi-factor, multi-step authentication framework. Each "factor" is a step: (1) username/password via LDAP, (2) TOTP/push via RADIUS to Duo/Okta, (3) certificate validation, (4) conditional logic (group membership, client IP). Pipeline failures at any factor block the entire authentication.

### Step 1 — - Configure data collection
Verify nFactor events:
```spl
index=netscaler sourcetype="citrix:netscaler:syslog" ("nFactor" OR "NFACTOR" OR "factor" OR "authentication" OR "LOGIN" OR "AAA") earliest=-4h
| where match(_raw, "(?i)(fail|error|success|factor)")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- nFactor pipeline failure analysis:**
```spl
index=netscaler sourcetype="citrix:netscaler:syslog" ("nFactor" OR "authentication" OR "AAA" OR "factor") ("fail" OR "error" OR "timeout" OR "reject") earliest=-4h
| eval factor=coalesce(factor_name, nfactor_flow, if(match(_raw, "(?i)ldap"), "LDAP", if(match(_raw, "(?i)radius"), "RADIUS", if(match(_raw, "(?i)saml"), "SAML", if(match(_raw, "(?i)cert"), "Certificate", "Unknown")))))
| eval user=coalesce(username, user, User)
| eval reason=coalesce(error_reason, if(match(_raw, "(?i)timeout"), "Timeout", if(match(_raw, "(?i)invalid.*password"), "Bad password", if(match(_raw, "(?i)server.*down|unreachable"), "Auth server unreachable", if(match(_raw, "(?i)cert.*expired"), "Certificate expired", "Check raw event")))))
| stats count as failures dc(user) as affected_users by host, factor, reason
| eval severity=case(factor="LDAP" AND reason="Auth server unreachable", "CRITICAL -- LDAP down", factor="RADIUS" AND reason="Timeout", "CRITICAL -- MFA provider down", failures > 50, "HIGH -- mass failures", 1==1, "WARNING")
| sort severity, -failures
```

### Step 3 — - Validate
(a) Log in through the nFactor flow and verify each factor's success event in Splunk.
(b) Enter wrong TOTP code and verify the RADIUS factor shows failure.
(c) On ADC CLI: `show authentication vserver <vs>` -- check bound policies and status.

### Step 4 — - Operationalize
Dashboard ("Citrix ADC -- nFactor Authentication"):
* Row 1 -- Single-value: "Total auth attempts", "Failures", "Affected users", "Worst factor".
* Row 2 -- Per-factor failure analysis with reason.

Alerting:
* Critical (LDAP or RADIUS timeout): authentication backend down -- all logins affected.
* High (> 50 failures in 15 min at any factor): systemic auth issue.

### Step 5 — - Troubleshooting

* **LDAP timeout** -- Check: (1) LDAP server reachability, (2) ADC LDAP action config: `show authentication ldapAction <action>`, (3) DNS resolution for LDAP server FQDN.

* **RADIUS timeout (MFA)** -- Check: (1) Duo/Okta proxy server status, (2) RADIUS shared secret matches, (3) Network path between ADC and RADIUS proxy.

* **nFactor flow not progressing past first factor** -- Check factor policy expressions and next-factor bindings: `show authentication loginSchema <schema>` and `show authentication policylabel <label>`.

## SPL

```spl
index=netscaler sourcetype="citrix:netscaler:syslog" (nFactor OR "login schema" OR AAA OR SAML OR "factor" OR IdP OR "assertion" OR "epa")
( "failed" OR "error" OR "timeout" OR "unreachable" OR "invalid" OR "reject" )
| rex field=_raw "(?i)(?<fail_reason>schema|timeout|SAML|assertion|IdP|LDAP|radius)"
| bin _time span=5m
| stats count as failures, values(fail_reason) as reasons, dc(client_ip) as src_ips, latest(host) as adc by auth_policy, _time
| where failures >= 3
| sort - failures
| table _time, adc, auth_policy, reasons, src_ips, failures
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  by Authentication.user Authentication.action Authentication.src Authentication.app span=1h
| sort -count
```

## Visualization

Time chart of auth failures by reason, top policies table, map or table of source IPs (if allowed by privacy policy).

## Known False Positives

Password resets, token expiry, and user mistakes can add login path failures on busy days.

## References

- [Splunk Documentation: Splunk Add-on for Citrix NetScaler](https://docs.splunk.com/Documentation/AddOns/released/CitrixNetScaler/CitrixNetScaler)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
- [Citrix ADC — nFactor authentication](https://docs.citrix.com/en-us/citrix-adc/current-release/)
