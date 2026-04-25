<!-- AUTO-GENERATED from UC-5.6.8.json — DO NOT EDIT -->

---
id: "5.6.8"
title: "DNS Latency Monitoring"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.6.8 · DNS Latency Monitoring

## Description

DNS latency directly adds to every network connection. Slow DNS = slow everything.

## Value

DNS latency directly adds to every network connection. Slow DNS = slow everything.

## Implementation

Use scripted input running `dig` queries against DNS servers measuring response time. Or enable DNS analytical logging with timing. Alert when average latency >50ms.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input, DNS diagnostic logs.
• Ensure the following data sources are available: DNS recursive query timing.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use scripted input running `dig` queries against DNS servers measuring response time. Or enable DNS analytical logging with timing. Alert when average latency >50ms.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=dns sourcetype="dns:latency"
| timechart span=5m avg(response_time_ms) as avg_latency by dns_server
| where avg_latency > 50
```

Understanding this SPL

**DNS Latency Monitoring** — DNS latency directly adds to every network connection. Slow DNS = slow everything.

Documented **Data sources**: DNS recursive query timing. **App/TA** (typical add-on context): Custom scripted input, DNS diagnostic logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: dns; **sourcetype**: dns:latency. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=dns, sourcetype="dns:latency". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by dns_server** — ideal for trending and alerting on this use case.
• Filters the current rows with `where avg_latency > 50` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare query volume, response codes, or latency in Infoblox reporting, Microsoft DNS views, BIND logs, or Meraki Network > Monitor to the Splunk results for the same resolvers and time range.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart per server, Gauge, Table.

## SPL

```spl
index=dns sourcetype="dns:latency"
| timechart span=5m avg(response_time_ms) as avg_latency by dns_server
| where avg_latency > 50
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Resolution.DNS
  by DNS.query DNS.reply_code span=5m
| where count>0
| sort -count
```

## Visualization

Line chart per server, Gauge, Table.

## References

- [CIM: Network_Resolution](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Resolution)
