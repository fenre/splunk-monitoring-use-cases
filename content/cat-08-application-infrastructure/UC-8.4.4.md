---
id: "8.4.4"
title: "Authentication Failures"
criticality: "high"
splunkPillar: "Security"
---

# UC-8.4.4 · Authentication Failures

## Description

Authentication failures may indicate credential compromise, API key rotation issues, or brute-force attacks.

## Value

Authentication failures may indicate credential compromise, API key rotation issues, or brute-force attacks.

## Implementation

Track 401/403 responses with source IP and consumer identity. Alert on high failure rates from single sources (potential brute force). Correlate with successful authentications to detect account compromise patterns.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Gateway auth logs.
• Ensure the following data sources are available: API gateway authentication logs (401/403 responses), OAuth error logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Track 401/403 responses with source IP and consumer identity. Alert on high failure rates from single sources (potential brute force). Correlate with successful authentications to detect account compromise patterns.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=api sourcetype="kong:access" status IN (401, 403)
| stats count by consumer_id, src, request_uri
| where count > 50
| sort -count
```

Understanding this SPL

**Authentication Failures** — Authentication failures may indicate credential compromise, API key rotation issues, or brute-force attacks.

Documented **Data sources**: API gateway authentication logs (401/403 responses), OAuth error logs. **App/TA** (typical add-on context): Gateway auth logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: api; **sourcetype**: kong:access. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=api, sourcetype="kong:access". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by consumer_id, src, request_uri** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 50` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (auth failures by consumer/IP), Line chart (failure rate over time), Geo map (failures by source location).

## SPL

```spl
index=api sourcetype="kong:access" status IN (401, 403)
| stats count by consumer_id, src, request_uri
| where count > 50
| sort -count
```

## Visualization

Table (auth failures by consumer/IP), Line chart (failure rate over time), Geo map (failures by source location).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
