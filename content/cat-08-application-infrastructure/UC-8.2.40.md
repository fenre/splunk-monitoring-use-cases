<!-- AUTO-GENERATED from UC-8.2.40.json — DO NOT EDIT -->

---
id: "8.2.40"
title: "Microsoft IIS HTTP 500.x Sub-Status Code Breakdown"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.2.40 · Microsoft IIS HTTP 500.x Sub-Status Code Breakdown

## Description

IIS substatus codes differentiate configuration lockdown (500.19) from module crashes (500.0). Without `sc-substatus`, operations teams guess from sparse client errors instead of precise failure classes.

## Value

Targets the right remediation playbook per failure class and shortens Sev-1 bridges.

## Implementation

Splunk Add-on for Microsoft IIS (Splunkbase 3185); ensure substatus field enabled in IIS logging. Map 500.19 to config errors, 500.0 to module crashes.

## SPL

```spl
index=web sourcetype="ms:iis:auto"
| where sc_status >= 500 AND sc_status < 600
| eval sub=coalesce('sc-substatus', sc_substatus, "0")
| stats count by sc_status, sub, s_sitename
| sort - count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Web.Web
  where Web.status>=500
  by Web.dest Web.uri_path Web.status span=5m
| sort -count
```

## Visualization

Stacked bars for status/substatus, Perfmon timecharts, top client tables.

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [Microsoft IIS documentation](https://learn.microsoft.com/en-us/troubleshoot/developer/webapps/iis/www-administration-management/http-status-code)
