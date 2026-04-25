<!-- AUTO-GENERATED from UC-5.3.26.json — DO NOT EDIT -->

---
id: "5.3.26"
title: "Citrix ADC nFactor Authentication Pipeline Failures"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.3.26 · Citrix ADC nFactor Authentication Pipeline Failures

## Description

Citrix ADC nFactor ties multiple authentication steps (VPN, web apps, user directories, SAML) into one pipeline. Login schema parse errors, per-factor timeouts, SAML attribute or assertion mismatches, or IdP reachability issues strand users in partial login states. Tracking these failures protects both availability (users cannot sign in) and security (forced fallbacks, repeated attempts, or mis-issued factors).

## Value

Citrix ADC nFactor ties multiple authentication steps (VPN, web apps, user directories, SAML) into one pipeline. Login schema parse errors, per-factor timeouts, SAML attribute or assertion mismatches, or IdP reachability issues strand users in partial login states. Tracking these failures protects both availability (users cannot sign in) and security (forced fallbacks, repeated attempts, or mis-issued factors).

## Implementation

Send AAA, audit, and authentication-related syslog to `index=netscaler` as `citrix:netscaler:syslog`. Classify by factor type (SAML, LDAP, RADIUS, EPA). Alert on growing failure rates for a given policy, IdP down messages, and schema errors after config pushes. Cross-reference with change records for nFactor flow edits.

## Detailed Implementation

Prerequisites
• High-volume auth syslog in `index=netscaler` with time sync.
• Knowledge of nFactor flow names and IdP hostnames (for allowlists and enrichment).
• Optional: extract `auth_policy` from structured fields if the TA provides them.

Step 1 — Configure data collection
Enable detailed authentication result logging. Forward only necessary fields to satisfy privacy policy. If client IP is masked, use session correlation IDs instead for drilldown.

Step 2 — Create the search and alert
Run the search; set thresholds per population (for example, IdP unreachable = page immediately; gradual SAML errors = warn after N events in 5 minutes). Throttle repeat alerts for the same root cause string.



Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  by Authentication.user Authentication.action Authentication.src Authentication.app span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

This block uses `tstats` on the Authentication data model. Enable data model acceleration for the same dataset in Settings → Data models before you rely on summaries.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for the Authentication model — enable acceleration and confirm CIM tags on your source data.
• Order and filter as needed for your environment (index-time filters, allowlists, and buckets).

Enable Data Model Acceleration for the model referenced above; otherwise `tstats` may return no results from summaries.



Step 3 — Validate
Compare vservers, services, and load-balancing state in the Citrix ADC management view or command line for the same time window and objects.
Step 4 — Operationalize
Runbook: verify IdP health, cert expiry, attribute maps, and DNS for IdP. Escalate to identity team with payload snippets (redacted).

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

## References

- [Splunk Documentation: Splunk Add-on for Citrix NetScaler](https://docs.splunk.com/Documentation/AddOns/released/CitrixNetScaler/CitrixNetScaler)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
- [Citrix ADC — nFactor authentication](https://docs.citrix.com/en-us/citrix-adc/current-release/aaatm-authentication.html)
