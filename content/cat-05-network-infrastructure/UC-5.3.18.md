---
id: "5.3.18"
title: "Citrix Gateway / VPN Session Monitoring (NetScaler)"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.3.18 · Citrix Gateway / VPN Session Monitoring (NetScaler)

## Description

Citrix Gateway (NetScaler Gateway) provides SSL VPN access and ICA Proxy functionality for remote Citrix session launches. Monitoring active Gateway sessions provides visibility into remote user activity, concurrent connection counts (license-relevant), authentication failures (brute force detection), and session anomalies (impossible travel, excessive bandwidth). Gateway is the perimeter entry point for all remote Citrix access, making it security-critical.

## Value

Citrix Gateway (NetScaler Gateway) provides SSL VPN access and ICA Proxy functionality for remote Citrix session launches. Monitoring active Gateway sessions provides visibility into remote user activity, concurrent connection counts (license-relevant), authentication failures (brute force detection), and session anomalies (impossible travel, excessive bandwidth). Gateway is the perimeter entry point for all remote Citrix access, making it security-critical.

## Implementation

The ADC logs all AAA (Authentication, Authorization, Accounting) events via syslog, including Gateway login successes, failures, and logouts with client IP and username. Configure syslog with appflow and audit logging enabled. Alert on: authentication failure rate exceeding 30% (possible brute force), concurrent sessions exceeding licensed capacity, a single source IP attempting more than 20 failed logins in 15 minutes, or unusual login times/locations for known users. Track peak concurrent Gateway sessions for capacity planning.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`).
• Ensure the following data sources are available: `index=network` `sourcetype="citrix:netscaler:syslog"` fields `user`, `client_ip`, `session_type`, `auth_result`, `gateway_vserver`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
The ADC logs all AAA (Authentication, Authorization, Accounting) events via syslog, including Gateway login successes, failures, and logouts with client IP and username. Configure syslog with appflow and audit logging enabled. Alert on: authentication failure rate exceeding 30% (possible brute force), concurrent sessions exceeding licensed capacity, a single source IP attempting more than 20 failed logins in 15 minutes, or unusual login times/locations for known users. Track peak concurrent Gate…

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

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

Understanding this SPL

**Citrix Gateway / VPN Session Monitoring (NetScaler)** — Citrix Gateway (NetScaler Gateway) provides SSL VPN access and ICA Proxy functionality for remote Citrix session launches. Monitoring active Gateway sessions provides visibility into remote user activity, concurrent connection counts (license-relevant), authentication failures (brute force detection), and session anomalies (impossible travel, excessive bandwidth). Gateway is the perimeter entry point for all remote Citrix access, making it security-critical.

Documented **Data sources**: `index=network` `sourcetype="citrix:netscaler:syslog"` fields `user`, `client_ip`, `session_type`, `auth_result`, `gateway_vserver`. **App/TA** (typical add-on context): Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: citrix:netscaler:syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="citrix:netscaler:syslog". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• `eval` defines or adjusts **auth_result** — often to normalize units, derive a ratio, or prepare for thresholds.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by gateway_vserver, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **fail_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where failures > 10 OR fail_pct > 30` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Citrix Gateway / VPN Session Monitoring (NetScaler)**): table _time, gateway_vserver, logins, failures, fail_pct, unique_users, unique_ips

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t dc(Authentication.src) as agg_value from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src span=15m | sort - agg_value
```

Understanding this CIM / accelerated SPL

**Citrix Gateway / VPN Session Monitoring (NetScaler)** — Citrix Gateway (NetScaler Gateway) provides SSL VPN access and ICA Proxy functionality for remote Citrix session launches. Monitoring active Gateway sessions provides visibility into remote user activity, concurrent connection counts (license-relevant), authentication failures (brute force detection), and session anomalies (impossible travel, excessive bandwidth). Gateway is the perimeter entry point for all remote Citrix access, making it security-critical.

Documented **Data sources**: `index=network` `sourcetype="citrix:netscaler:syslog"` fields `user`, `client_ip`, `session_type`, `auth_result`, `gateway_vserver`. **App/TA** (typical add-on context): Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timechart (logins vs failures), Bar chart (failures by source IP), Single value (concurrent sessions).

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
| tstats summariesonly=t dc(Authentication.src) as agg_value from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src span=15m | sort - agg_value
```

## Visualization

Timechart (logins vs failures), Bar chart (failures by source IP), Single value (concurrent sessions).

## References

- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
