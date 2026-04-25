<!-- AUTO-GENERATED from UC-2.6.51.json — DO NOT EDIT -->

---
id: "2.6.51"
title: "Citrix StoreFront Server IIS Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.6.51 · Citrix StoreFront Server IIS Health

## Description

StoreFront is the first hop for many users after the gateway. If IIS app pools recycle frequently, if worker processes crash, or if HTTP 401/500/503 rates climb, every receiver update, resource enumeration, and single sign-on call suffers — often before the broker shows pressure. You should monitor the IIS access log error mix, time-taken (latency) percentiles, and the Windows event trail for `W3SVC`, `IIS*`, and app pool `Application pool * stopped` or rapid recycling on each StoreFront node. A healthy farm shows symmetric latency across members; asymmetry is a sign of broken authentication provider settings or a sick node still receiving traffic from the load balancer.

## Value

StoreFront is the first hop for many users after the gateway. If IIS app pools recycle frequently, if worker processes crash, or if HTTP 401/500/503 rates climb, every receiver update, resource enumeration, and single sign-on call suffers — often before the broker shows pressure. You should monitor the IIS access log error mix, time-taken (latency) percentiles, and the Windows event trail for `W3SVC`, `IIS*`, and app pool `Application pool * stopped` or rapid recycling on each StoreFront node. A healthy farm shows symmetric latency across members; asymmetry is a sign of broken authentication provider settings or a sick node still receiving traffic from the load balancer.

## Implementation

Enable W3C extended logging on StoreFront with `time-taken`, `sc-status`, and `cs-uri-stem` at minimum. Ingest in near real time. Add a second scheduled search on Application/System for IIS worker crashes. Baseline 401 rates versus known maintenance. Alert when 5xx exceeds 0.2% of requests for 15 minutes, or p95 time-taken exceeds 2,000 ms for authentication and resource endpoints, or on app pool recycles more than one per hour per site. De-dupe load-balanced pairs by `cs-host` to avoid double counting a single user action.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for Microsoft Windows, IIS with W3C logging, Splunk or MS IIS add-on for parsing.
• Ensure the following data sources are available: `iis` access logs, relevant Windows event logs, correct time on all StoreFront nodes behind the load balancer.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Set `sourcetype` to `iis` for consistency. If you use XML `HTTPERR`, add a separate `sourcetype` and a union search. Add `props` to parse `timetaken` in milliseconds. If `csUsername` is empty by design, do not use it for triage. Verify log rollover does not create gaps in forwarder file tails.

Step 2 — Create the search and alert
The primary SPL in this file is tuned for p95 time-taken and error mix. A companion search on events:

```spl
index=windows sourcetype="WinEventLog:Application" source="*IIS*" OR source="*W3SVC*"
| stats count by EventCode, host
| where count>0
```

**Citrix StoreFront Server IIS Health** — Correlates HTTP errors to application pool and worker events using `host` and time proximity with `transaction` in a follow-on panel.

Step 3 — Validate
Request synthetic GETs to `/Citrix/StoreWeb/` from a canary, confirm rows and latency. Induce a controlled app pool recycle in a lab and see event + HTTP correlation.

Step 4 — Operationalize
Page the Citrix and Windows teams together when 503s exceed baseline; include load balancer and authentication provider runbooks. Keep six months of access logs in warm storage for post-incident forensics on enumeration storms.

## SPL

```spl
index=windows (sourcetype="iis" OR sourcetype="W3C*" OR source="*u_ex*.log")
| eval site=coalesce(s_sitename, "default")
| search cs_uri_stem="*Authentication*" OR cs_uri_stem="*Resources*" OR cs_uri_stem="*Icon*" OR like(lower(cs_uri_stem), "%citrix%")
| eval sc=tonumber(sc_status)
| eval is_err=if(sc>=400,1,0)
| bin _time span=5m
| stats count as total, sum(is_err) as http_err, avg(timetaken) as avg_ms, perc95(timetaken) as p95_ms by site, _time
| eval err_pct=if(total>0, round(100*http_err/total,2), 0)
| where err_pct>1 OR p95_ms>2000
| table _time, site, total, err_pct, avg_ms, p95_ms
```

## Visualization

Timechart of 4xx/5xx counts, timechart of p95 time-taken by virtual directory, table of app pool recycles, single value for 503 spike.

## References

- [Citrix StoreFront 1912 and later (planning and networking)](https://docs.citrix.com/en-us/storefront/1912/plan/considerations.html)
- [Microsoft: IIS log fields](https://learn.microsoft.com/en-us/iis/get-started/whats-new-in-iis-85/iis-85-rewrite-module-logging-rewrite-tracing)
