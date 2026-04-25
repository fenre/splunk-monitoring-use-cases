<!-- AUTO-GENERATED from UC-5.9.14.json — DO NOT EDIT -->

---
id: "5.9.14"
title: "DNS Resolution Time Trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.14 · DNS Resolution Time Trending

## Description

Slow DNS resolution adds latency to every connection. Trending resolution time helps identify degrading DNS infrastructure or inefficient recursive resolution chains.

## Value

Slow DNS resolution adds latency to every connection. Trending resolution time helps identify degrading DNS infrastructure or inefficient recursive resolution chains.

## Implementation

The OTel metric `dns.lookup.duration` reports DNS resolve time in seconds. The Splunk App Network dashboard includes a "DNS Duration (s)" line chart. Alert when resolution time exceeds 200 ms consistently — this adds noticeable delay to every new connection.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (DNS tests).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
The OTel metric `dns.lookup.duration` reports DNS resolve time in seconds. The Splunk App Network dashboard includes a "DNS Duration (s)" line chart. Alert when resolution time exceeds 200 ms consistently — this adds noticeable delay to every new connection.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.type="dns-server"
| timechart span=5m avg(dns.lookup.duration) as avg_dns_duration_s by dns.question.name
| eval avg_dns_duration_ms=round(avg_dns_duration_s*1000,1)
```

Understanding this SPL

**DNS Resolution Time Trending** — Slow DNS resolution adds latency to every connection. Trending resolution time helps identify degrading DNS infrastructure or inefficient recursive resolution chains.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (DNS tests). **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by dns.question.name** — ideal for trending and alerting on this use case.
• `eval` defines or adjusts **avg_dns_duration_ms** — often to normalize units, derive a ratio, or prepare for thresholds.


Step 3 — Validate
Compare the same tests and time window in the Cisco ThousandEyes App for Splunk dashboard or the test view at app.thousandeyes.com so Splunk’s metrics and states match the vendor. If they disagree, check streaming or HEC inputs, macros, and API or token health before retuning.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (resolution time over time by domain), Table with drilldown to ThousandEyes.

## SPL

```spl
`stream_index` thousandeyes.test.type="dns-server"
| timechart span=5m avg(dns.lookup.duration) as avg_dns_duration_s by dns.question.name
| eval avg_dns_duration_ms=round(avg_dns_duration_s*1000,1)
```

## Visualization

Line chart (resolution time over time by domain), Table with drilldown to ThousandEyes.

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
