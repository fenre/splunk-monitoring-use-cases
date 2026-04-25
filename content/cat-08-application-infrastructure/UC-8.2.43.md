<!-- AUTO-GENERATED from UC-8.2.43.json — DO NOT EDIT -->

---
id: "8.2.43"
title: "Microsoft IIS Client Certificate Authentication Failures"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.2.43 · Microsoft IIS Client Certificate Authentication Failures

## Description

Mutual TLS and client certificate mapping failures often surface as HTTP 403.7-class patterns. Volume spikes frequently track partner certificate expiries or cipher suite mismatches after hardening.

## Value

Protects B2B APIs and federated integrations that depend on certificate authentication continuity.

## Implementation

Enable detailed errors in lower env only; prod relies on W3C fields. Join `iis:httperr` for `BadRequest` reasons.

## SPL

```spl
index=web sourcetype="ms:iis:auto"
| where sc_status=403 AND match(cs_uri_stem, "(?i)\.asmx|api")
| regex _raw="(?i)(403\.7|certificate|SSL client)"
| stats count by c_ip, cs_uri_stem, sc_status
| where count > 10
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where (Authentication.action="failure" OR lower(Authentication.action)="failed")
  by Authentication.user Authentication.src Authentication.app span=5m
| sort -count
```

## Visualization

Stacked bars for status/substatus, Perfmon timecharts, top client tables.

## References

- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
- [Microsoft IIS documentation](https://learn.microsoft.com/en-us/iis/configuration/system.applicationhost/applicationpools/add/processmodel)
