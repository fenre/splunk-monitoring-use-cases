<!-- AUTO-GENERATED from UC-8.1.3.json — DO NOT EDIT -->

---
id: "8.1.3"
title: "Request Rate Trending"
criticality: "medium"
splunkPillar: "Security"
---

# UC-8.1.3 · Request Rate Trending

## Description

Traffic trending supports capacity planning and identifies unexpected traffic patterns (bot attacks, viral events, traffic drops).

## Value

Traffic trending supports capacity planning and identifies unexpected traffic patterns (bot attacks, viral events, traffic drops).

## Implementation

Ingest access logs. Track requests per second/minute. Baseline normal traffic patterns using `predict`. Alert on sudden drops (possible outage) or spikes (possible attack). Break down by URI for endpoint-level trending.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_apache`, `TA-nginx`.
• Ensure the following data sources are available: Access logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest access logs. Track requests per second/minute. Baseline normal traffic patterns using `predict`. Alert on sudden drops (possible outage) or spikes (possible attack). Break down by URI for endpoint-level trending.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=web sourcetype="access_combined"
| timechart span=1m count as requests_per_min by host
| predict requests_per_min as predicted
```

Understanding this SPL

**Request Rate Trending** — Traffic trending supports capacity planning and identifies unexpected traffic patterns (bot attacks, viral events, traffic drops).

Documented **Data sources**: Access logs. **App/TA** (typical add-on context): `Splunk_TA_apache`, `TA-nginx`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: web; **sourcetype**: access_combined. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=web, sourcetype="access_combined". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• Pipeline stage (see **Request Rate Trending**): predict requests_per_min as predicted


Step 3 — Validate
Compare with web server access logs on disk (Apache, NGINX, or W3C) for the same time range, or tail the same sourcetype in Search, to confirm status codes, URIs, and counts.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (request rate with prediction band), Area chart (traffic over time), Bar chart (requests by host).

## SPL

```spl
index=web sourcetype="access_combined"
| timechart span=1m count as requests_per_min by host
| predict requests_per_min as predicted
```

## CIM SPL

```spl
| tstats `summariesonly` count sum(Web.bytes) as total_bytes
  from datamodel=Web.Web
  by Web.src Web.dest Web.uri_path Web.status span=1h
| sort -count
```

## Visualization

Line chart (request rate with prediction band), Area chart (traffic over time), Bar chart (requests by host).

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
