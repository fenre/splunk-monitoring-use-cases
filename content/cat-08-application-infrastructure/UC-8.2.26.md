<!-- AUTO-GENERATED from UC-8.2.26.json — DO NOT EDIT -->

---
id: "8.2.26"
title: "Squid Upstream and Peer Connection Failures"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.2.26 · Squid Upstream and Peer Connection Failures

## Description

cache.log records parent/peer connect failures, TLS issues, and routing errors that may not appear as 5xx in access logs yet.

## Value

Explains intermittent proxy failures during upstream maintenance or path MTU issues.

## Implementation

Enable informative logging; rotate and forward cache.log. Tune noise from benign peer flaps.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom (Squid `cache.log` forwarding).
• Ensure the following data sources are available: `index=proxy` `sourcetype=squid:cache` (cache.log warnings/errors).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Validate search terms against your Squid major version; adjust phrases for your locale.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=proxy sourcetype="squid:cache"
| search ("Connection to" AND failed) OR "CONNECT tunnel error" OR "Network unreachable"
| rex field=_raw "(?<peer>\d+\.\d+\.\d+\.\d+|\S+:\d+)"
| stats count by peer
| sort -count
```

Understanding this SPL

**Squid Upstream and Peer Connection Failures** — See the description and value fields in this use case JSON.

Documented **Data sources**: `index=proxy` `sourcetype=squid:cache` (cache.log warnings/errors). **App/TA**: Custom (Squid `cache.log` forwarding). Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

• Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.

Step 3 — Validate
Compare with JBoss, WebLogic, or Tomcat admin consoles, or `catalina` / server logs on the host, for the same window. Confirm hostnames and fields match the vendor UI.


Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Table (peer × count), timeline of failures, link to network change calendar..

## SPL

```spl
index=proxy sourcetype="squid:cache"
| search ("Connection to" AND failed) OR "CONNECT tunnel error" OR "Network unreachable"
| rex field=_raw "(?<peer>\d+\.\d+\.\d+\.\d+|\S+:\d+)"
| stats count by peer
| sort -count
```

## Visualization

Table (peer × count), timeline of failures, link to network change calendar.

## References

- [Squid Configuration Manual — Access Log](http://www.squid-cache.org/Doc/config/access_log/)
