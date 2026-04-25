<!-- AUTO-GENERATED from UC-8.1.26.json — DO NOT EDIT -->

---
id: "8.1.26"
title: "HAProxy HTTP Frontend 5xx Rate from Syslog"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.1.26 · HAProxy HTTP Frontend 5xx Rate from Syslog

## Description

HAProxy HTTP logs include terminal status codes after timing fields. Monitoring 5xx rates complements CSV stats for user-visible errors.

## Value

Catches application failures that do not yet mark backends DOWN in stats.

## Implementation

Enable `option httplog`, forward syslog to Splunk, and extract status at EOL. Validate `rex` against your exact `log-format`.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: HAProxy syslog + props/transforms for HTTP log format.
• Ensure the following data sources are available: `index=proxy` HAProxy HTTP log mode via syslog (`sourcetype=haproxy:http` recommended at ingest).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Adjust the `rex` if you customized `log-format`; test against sample events.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=proxy sourcetype="haproxy:http"
| rex field=_raw "\s(?<http_status>5\d{2})\s+(?<resp_bytes>\d+|-)\s*$"
| where isnotnull(http_status)
| bin _time span=5m
| stats count as err5 by http_status
| eventstats sum(err5) as tot
| eval pct=round(100*err5/tot,2)
| where pct > 2
```

Understanding this SPL

**HAProxy HTTP Frontend 5xx Rate from Syslog** — See the description and value fields in this use case JSON.

Documented **Data sources**: `index=proxy` HAProxy HTTP log mode via syslog (`sourcetype=haproxy:http` recommended at ingest). **App/TA**: HAProxy syslog + props/transforms for HTTP log format. Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

• Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.


Step 3 — Validate
Compare with web server access logs on disk (Apache, NGINX, or W3C) for the same time range, or tail the same sourcetype in Search, to confirm status codes, URIs, and counts.


Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Stacked bar (5xx codes), timechart of 5xx/min, top frontends if parsed..

## SPL

```spl
index=proxy sourcetype="haproxy:http"
| rex field=_raw "\s(?<http_status>5\d{2})\s+(?<resp_bytes>\d+|-)\s*$"
| where isnotnull(http_status)
| bin _time span=5m
| stats count as err5 by http_status
| eventstats sum(err5) as tot
| eval pct=round(100*err5/tot,2)
| where pct > 2
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

Stacked bar (5xx codes), timechart of 5xx/min, top frontends if parsed.

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [HAProxy Management Guide — Logging](https://www.haproxy.com/documentation/haproxy-management-guide/latest/observability/logging/)
