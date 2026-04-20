---
id: "8.4.3"
title: "Rate Limiting Events"
criticality: "medium"
splunkPillar: "Security"
---

# UC-8.4.3 · Rate Limiting Events

## Description

Rate limiting indicates consumers exceeding their quotas. May signal API abuse, misconfigured clients, or quota adjustments needed.

## Value

Rate limiting indicates consumers exceeding their quotas. May signal API abuse, misconfigured clients, or quota adjustments needed.

## Implementation

Track 429 responses from API gateway. Identify rate-limited consumers and endpoints. Alert on sustained rate limiting for critical consumers. Review quota configuration if legitimate traffic is being limited.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Gateway logs.
• Ensure the following data sources are available: API gateway rate limit logs (429 responses).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Track 429 responses from API gateway. Identify rate-limited consumers and endpoints. Alert on sustained rate limiting for critical consumers. Review quota configuration if legitimate traffic is being limited.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=api sourcetype="kong:access" status=429
| stats count by consumer_id, request_uri
| sort -count
```

Understanding this SPL

**Rate Limiting Events** — Rate limiting indicates consumers exceeding their quotas. May signal API abuse, misconfigured clients, or quota adjustments needed.

Documented **Data sources**: API gateway rate limit logs (429 responses). **App/TA** (typical add-on context): Gateway logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: api; **sourcetype**: kong:access. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=api, sourcetype="kong:access". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by consumer_id, request_uri** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (rate-limited consumers), Line chart (429 rate over time), Table (rate limit events).

## SPL

```spl
index=api sourcetype="kong:access" status=429
| stats count by consumer_id, request_uri
| sort -count
```

## Visualization

Bar chart (rate-limited consumers), Line chart (429 rate over time), Table (rate limit events).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
