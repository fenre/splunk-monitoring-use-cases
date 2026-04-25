<!-- AUTO-GENERATED from UC-8.5.12.json — DO NOT EDIT -->

---
id: "8.5.12"
title: "Website Page Load Time Breakdown"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.5.12 · Website Page Load Time Breakdown

## Description

DNS, connect, TLS, TTFB, and download timing per page element enable root cause analysis of slow page loads. Breakdown identifies whether slowness is network, backend, or resource-related.

## Value

DNS, connect, TLS, TTFB, and download timing per page element enable root cause analysis of slow page loads. Breakdown identifies whether slowness is network, backend, or resource-related.

## Implementation

Instrument frontend with RUM (Splunk RUM, Boomerang, or custom beacon) to capture Navigation Timing API fields. Alternatively run curl with `-w` format for key endpoints. Parse domainLookupEnd-domainLookupStart (DNS), connectEnd-connectStart (connect), responseStart-requestStart (TTFB). Forward to Splunk via HEC. Alert when p95 TTFB exceeds 1s. Correlate with backend latency and CDN metrics.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk RUM or custom scripted input (curl timing).
• Ensure the following data sources are available: Navigation Timing API, curl -w format, RUM beacon data.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Instrument frontend with RUM (Splunk RUM, Boomerang, or custom beacon) to capture Navigation Timing API fields. Alternatively run curl with `-w` format for key endpoints. Parse domainLookupEnd-domainLookupStart (DNS), connectEnd-connectStart (connect), responseStart-requestStart (TTFB). Forward to Splunk via HEC. Alert when p95 TTFB exceeds 1s. Correlate with backend latency and CDN metrics.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=rum sourcetype="rum:timing"
| eval dns_ms=domain_dns_end-domain_dns_start, connect_ms=connect_end-connect_start, ttfb_ms=response_start-request_start
| timechart span=5m perc95(ttfb_ms) as p95_ttfb, perc95(dns_ms) as p95_dns by page_url
| where p95_ttfb > 1000
```

Understanding this SPL

**Website Page Load Time Breakdown** — DNS, connect, TLS, TTFB, and download timing per page element enable root cause analysis of slow page loads. Breakdown identifies whether slowness is network, backend, or resource-related.

Documented **Data sources**: Navigation Timing API, curl -w format, RUM beacon data. **App/TA** (typical add-on context): Splunk RUM or custom scripted input (curl timing). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: rum; **sourcetype**: rum:timing. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=rum, sourcetype="rum:timing". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **dns_ms** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by page_url** — ideal for trending and alerting on this use case.
• Filters the current rows with `where p95_ttfb > 1000` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare with the cache or proxy product’s own stats (CLI or UI) and a small sample of indexed events.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Waterfall (timing breakdown by resource), Line chart (p95 TTFB/DNS/connect over time), Table (slowest pages), Single value (p95 page load).

## SPL

```spl
index=rum sourcetype="rum:timing"
| eval dns_ms=domain_dns_end-domain_dns_start, connect_ms=connect_end-connect_start, ttfb_ms=response_start-request_start
| timechart span=5m perc95(ttfb_ms) as p95_ttfb, perc95(dns_ms) as p95_dns by page_url
| where p95_ttfb > 1000
```

## Visualization

Waterfall (timing breakdown by resource), Line chart (p95 TTFB/DNS/connect over time), Table (slowest pages), Single value (p95 page load).

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
