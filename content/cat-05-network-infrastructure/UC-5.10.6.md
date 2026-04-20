---
id: "5.10.6"
title: "SIP Post-Dial Delay Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.10.6 · SIP Post-Dial Delay Monitoring

## Description

Measures the time between a SIP INVITE and the first ringing or answer response, directly reflecting the user experience of waiting after dialing. High post-dial delay indicates trunk congestion, routing loops, or downstream SBC issues.

## Value

Measures the time between a SIP INVITE and the first ringing or answer response, directly reflecting the user experience of waiting after dialing. High post-dial delay indicates trunk congestion, routing loops, or downstream SBC issues.

## Implementation

Configure Splunk App for Stream to capture SIP INVITE and response transactions. The `setup_delay` field measures the time from INVITE to the first non-100 response (typically 180 Ringing or 200 OK). Monitor by `dest` to identify slow destinations or trunks. ITU-T E.721 recommends post-dial delay under 3 seconds for national calls and under 5 seconds for international calls. Create tiered alerts: warning at p95 >3s, critical at p95 >5s. Trend analysis reveals degradation patterns across time of day and destination.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk App for Stream` (Splunkbase #1809).
• Ensure the following data sources are available: `sourcetype=stream:sip`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Splunk App for Stream to capture SIP INVITE and response transactions. The `setup_delay` field measures the time from INVITE to the first non-100 response (typically 180 Ringing or 200 OK). Monitor by `dest` to identify slow destinations or trunks. ITU-T E.721 recommends post-dial delay under 3 seconds for national calls and under 5 seconds for international calls. Create tiered alerts: warning at p95 >3s, critical at p95 >5s. Trend analysis reveals degradation patterns across time of …

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
sourcetype="stream:sip" method="INVITE" reply_code=200
| where isnotnull(setup_delay)
| stats avg(setup_delay) as avg_pdd, perc95(setup_delay) as p95_pdd, max(setup_delay) as max_pdd, count as calls by dest
| eval avg_pdd_ms=round(avg_pdd*1000, 0), p95_pdd_ms=round(p95_pdd*1000, 0)
| where p95_pdd_ms>3000
| sort -p95_pdd_ms
```

Understanding this SPL

**SIP Post-Dial Delay Monitoring** — Measures the time between a SIP INVITE and the first ringing or answer response, directly reflecting the user experience of waiting after dialing. High post-dial delay indicates trunk congestion, routing loops, or downstream SBC issues.

Documented **Data sources**: `sourcetype=stream:sip`. **App/TA** (typical add-on context): `Splunk App for Stream` (Splunkbase #1809). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **sourcetype**: stream:sip. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: sourcetype="stream:sip". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where isnotnull(setup_delay)` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by dest** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **avg_pdd_ms** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where p95_pdd_ms>3000` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (p95 post-dial delay with thresholds: green <2s, yellow 2-3s, red >3s), Line chart (average PDD trend by dest over 24h), Table (dest, calls, avg_pdd_ms, p95_pdd_ms, max_pdd_ms — sortable), Histogram (PDD distribution across all calls).

## SPL

```spl
sourcetype="stream:sip" method="INVITE" reply_code=200
| where isnotnull(setup_delay)
| stats avg(setup_delay) as avg_pdd, perc95(setup_delay) as p95_pdd, max(setup_delay) as max_pdd, count as calls by dest
| eval avg_pdd_ms=round(avg_pdd*1000, 0), p95_pdd_ms=round(p95_pdd*1000, 0)
| where p95_pdd_ms>3000
| sort -p95_pdd_ms
```

## Visualization

Gauge (p95 post-dial delay with thresholds: green <2s, yellow 2-3s, red >3s), Line chart (average PDD trend by dest over 24h), Table (dest, calls, avg_pdd_ms, p95_pdd_ms, max_pdd_ms — sortable), Histogram (PDD distribution across all calls).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
