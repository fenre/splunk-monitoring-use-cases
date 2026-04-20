---
id: "5.9.32"
title: "CDN Edge Network Performance"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.9.32 · CDN Edge Network Performance

## Description

Measures latency, loss, and path characteristics to CDN edge locations, revealing when CDN performance varies by region or when edge servers are not serving content as expected.

## Value

Measures latency, loss, and path characteristics to CDN edge locations, revealing when CDN performance varies by region or when edge servers are not serving content as expected.

## Implementation

Create HTTP Server tests targeting CDN-served URLs from multiple ThousandEyes Cloud Agents. The `server.address` will show which CDN edge server responded. Compare performance across regions by grouping by `thousandeyes.source.agent.location`. Correlate HTTP response headers (cache hit/miss) with performance differences.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create HTTP Server tests targeting CDN-served URLs from multiple ThousandEyes Cloud Agents. The `server.address` will show which CDN edge server responded. Compare performance across regions by grouping by `thousandeyes.source.agent.location`. Correlate HTTP response headers (cache hit/miss) with performance differences.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.type="http-server"
| search thousandeyes.test.name="*CDN*"
| stats avg(http.client.request.duration) as avg_ttfb_s avg(http.server.throughput) as avg_throughput by thousandeyes.test.name, thousandeyes.source.agent.name, server.address
| eval avg_ttfb_ms=round(avg_ttfb_s*1000,1), throughput_mbps=round(avg_throughput/1048576,2)
| sort thousandeyes.source.agent.name
```

Understanding this SPL

**CDN Edge Network Performance** — Measures latency, loss, and path characteristics to CDN edge locations, revealing when CDN performance varies by region or when edge servers are not serving content as expected.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics. **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by thousandeyes.test.name, thousandeyes.source.agent.name, server.address** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **avg_ttfb_ms** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Column chart (TTFB by CDN edge), Table (agent, CDN edge, TTFB, throughput), Map.

## SPL

```spl
`stream_index` thousandeyes.test.type="http-server"
| search thousandeyes.test.name="*CDN*"
| stats avg(http.client.request.duration) as avg_ttfb_s avg(http.server.throughput) as avg_throughput by thousandeyes.test.name, thousandeyes.source.agent.name, server.address
| eval avg_ttfb_ms=round(avg_ttfb_s*1000,1), throughput_mbps=round(avg_throughput/1048576,2)
| sort thousandeyes.source.agent.name
```

## Visualization

Column chart (TTFB by CDN edge), Table (agent, CDN edge, TTFB, throughput), Map.

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
