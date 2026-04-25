<!-- AUTO-GENERATED from UC-7.1.82.json — DO NOT EDIT -->

---
id: "7.1.82"
title: "Snowflake Failed Login and MFA Anomaly Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-7.1.82 · Snowflake Failed Login and MFA Anomaly Detection

## Description

Credential attacks produce failed logins, while risky configuration can allow privileged roles to authenticate without a second factor. Combining failure volume with MFA field presence highlights both brute-force and policy-bypass patterns worth investigating.

## Value

Reduces account takeover and privileged-access risk for Snowflake-native and hybrid SSO deployments.

## Implementation

Map `FIRST_AUTHENTICATION_FACTOR`, `SECOND_AUTHENTICATION_FACTOR`, `IS_SUCCESS`, `ERROR_MESSAGE`, `CLIENT_IP` per TA version. Maintain `privileged_snowflake_users.csv` instead of hardcoding roles in production. For IdP-MFA, expect `SECOND_AUTHENTICATION_FACTOR` to be empty—tune the MFA-bypass stanza to your SSO model. Correlate with IdP sign-in logs.

## SPL

```spl
index=datawarehouse sourcetype="snowflake:login_history"
| eval ok=if(IS_SUCCESS="true" OR IS_SUCCESS="TRUE" OR IS_SUCCESS=1,1,0)
| eval mfa=coalesce(SECOND_AUTHENTICATION_FACTOR, second_authentication_factor,"")
| eval mfa_fail=if(ok=0 AND match(coalesce(ERROR_MESSAGE,""),"(?i)mfa|multi-?factor|second factor"),1,0)
| eval priv_bypass=if(ok=1 AND match(USER_NAME,"(?i)admin") AND (mfa="" OR match(mfa,"(?i)not applicable")),1,0)
| where ok=0 OR mfa_fail=1 OR priv_bypass=1
| bin _time span=1h
| stats count as events values(ERROR_MESSAGE) as err dc(CLIENT_IP) as ips max(mfa_fail) as had_mfa_error max(priv_bypass) as had_priv_no_mfa by USER_NAME, _time
| where events > 5 OR had_mfa_error=1
```

## Visualization

Timeline (events), Table (user, ok, err, ips), Map (CLIENT_IP).

## References

- [Snowflake LOGIN_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/login_history)
- [Snowflake — Multi-factor authentication](https://docs.snowflake.com/en/user-guide/security-mfa)
