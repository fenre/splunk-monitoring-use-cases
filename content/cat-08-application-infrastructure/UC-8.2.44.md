<!-- AUTO-GENERATED from UC-8.2.44.json — DO NOT EDIT -->

---
id: "8.2.44"
title: "Microsoft IIS URL Rewrite Redirect Loop Detection"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.2.44 · Microsoft IIS URL Rewrite Redirect Loop Detection

## Description

Misconfigured outbound rules can bounce clients between URLs many times per second. IIS access logs expose tight chains of 301/302 responses tied to the same client in a short window.

## Value

Stops hard-to-reproduce mobile and crawler failures that harm SEO and conversion funnels.

## Implementation

Install IIS URL Rewrite module; ingest logs with `time-taken` and referer. Tune thresholds for CDNs.

## SPL

```spl
index=web sourcetype="ms:iis:auto"
| where sc_status IN (301,302,307,308)
| eval hop_key=c_ip.cs_uri_stem
| bin _time span=1s
| stats dc(cs_uri_stem) as distinct_uris count by c_ip, _time
| where distinct_uris > 5 OR count > 20
```

## CIM SPL

```spl
| tstats `summariesonly` count as events
  from datamodel=Web.Web
  by Web.http_method Web.dest span=5m
| sort -events
```

## Visualization

Stacked bars for status/substatus, Perfmon timecharts, top client tables.

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [Microsoft IIS documentation](https://www.iis.net/downloads/microsoft/url-rewrite)
