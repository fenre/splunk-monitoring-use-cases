<!-- AUTO-GENERATED from UC-8.1.21.json — DO NOT EDIT -->

---
id: "8.1.21"
title: "Squid Access Log HTTP 5xx and Error Result Codes"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.1.21 · Squid Access Log HTTP 5xx and Error Result Codes

## Description

Squid logs cache result codes with embedded HTTP status (for example `TCP_MISS/503`). Elevated 5xx rates indicate origin or peer failures seen through the proxy.

## Value

Reduces blind spots when the proxy masks origin outages—5xx in Squid logs often match user-visible failures.

## Implementation

Use `access_log` with Squid-native format so status codes are present. Forward via Universal Forwarder. Tune threshold to request volume.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom (Squid access.log forwarding).
• Ensure the following data sources are available: `index=proxy` `sourcetype=squid:access` native or extended log format.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Confirm access logs include `/status` style result codes; validate `rex` against a sample line from your deployment.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=proxy sourcetype="squid:access"
| rex field=_raw "(?i)(?:TCP_[A-Z_]+)/(?<http_status>5\d\d)"
| where isnotnull(http_status)
| bin _time span=5m
| stats count by http_status, _time
| where count >= 20
```

Understanding this SPL

**Squid Access Log HTTP 5xx and Error Result Codes** — See the description and value fields in this use case JSON.

Documented **Data sources**: `index=proxy` `sourcetype=squid:access` native or extended log format. **App/TA**: Custom (Squid access.log forwarding). Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

• Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.


Step 3 — Validate
Compare with web server access logs on disk (Apache, NGINX, or W3C) for the same time range, or tail the same sourcetype in Search, to confirm status codes, URIs, and counts.


Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Stacked bar (5xx by code), timechart of 5xx/min, top clients if fields are extracted..

## SPL

```spl
index=proxy sourcetype="squid:access"
| rex field=_raw "(?i)(?:TCP_[A-Z_]+)/(?<http_status>5\d\d)"
| where isnotnull(http_status)
| bin _time span=5m
| stats count by http_status, _time
| where count >= 20
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

Stacked bar (5xx by code), timechart of 5xx/min, top clients if fields are extracted.

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [Squid Configuration Manual — Access Log](http://www.squid-cache.org/Doc/config/access_log/)
