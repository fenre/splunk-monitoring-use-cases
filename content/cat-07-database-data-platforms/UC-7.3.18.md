<!-- AUTO-GENERATED from UC-7.3.18.json — DO NOT EDIT -->

---
id: "7.3.18"
title: "Snowflake Failed Login Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-7.3.18 · Snowflake Failed Login Detection

## Description

Brute-force and credential stuffing against Snowflake appear as bursts of failed logins in LOGIN_HISTORY. Security teams baseline failures per user and source IP.

## Value

Reduces account takeover risk and supports insider-threat reviews without relying only on Snowflake-native notifications.

## Implementation

Schedule ACCOUNT_USAGE.LOGIN_HISTORY replication to Splunk (respecting latency of the view). Hash or tokenize usernames if required by privacy policy. Tune thresholds per SSO vs local users. Correlate with Okta/Azure AD logs if federated.

## SPL

```spl
index=datawarehouse sourcetype="snowflake:login_history"
| where IS_SUCCESS=="false" OR IS_SUCCESS=="FALSE" OR IS_SUCCESS==0
| bin _time span=1h
| stats count as failures dc(CLIENT_IP) as distinct_ips values(ERROR_MESSAGE) as errors by USER_NAME, _time
| where failures > 20 OR distinct_ips > 5
```

## Visualization

Table (user, failures, IPs), Map (client_ip), Timeline (failed attempts).

## References

- [Snowflake LOGIN_HISTORY view](https://docs.snowflake.com/en/sql-reference/account-usage/login_history)
- [DBX Add-on for Snowflake JDBC](https://splunkbase.splunk.com/app/6153)
