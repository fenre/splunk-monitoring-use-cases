---
id: "9.3.16"
title: "Token Endpoint Rate Limiting"
criticality: "medium"
splunkPillar: "Security"
---

# UC-9.3.16 · Token Endpoint Rate Limiting

## Description

Throttling at `/oauth2/token` breaks integrations and may indicate credential stuffing or runaway automation.

## Value

Throttling at `/oauth2/token` breaks integrations and may indicate credential stuffing or runaway automation.

## Implementation

Log token endpoint from AAD Application Proxy or API Management. Alert on 429 spikes per client_id. Implement exponential backoff in callers.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: API gateway / WAF logs, Entra `SignInLogs` with error codes, custom HEC from reverse proxy.
• Ensure the following data sources are available: HTTP 429, `AADSTS50196` / `invalid_client` bursts, `rateLimit` in response headers.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Log token endpoint from AAD Application Proxy or API Management. Alert on 429 spikes per client_id. Implement exponential backoff in callers.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=proxy sourcetype="access_combined" uri_path="/oauth2/v2.0/token"
| search status=429 OR like(_raw,"%rate limit%")
| bin _time span=5m
| stats count by client_id, _time
| where count > 100
| sort -count
```

Understanding this SPL

**Token Endpoint Rate Limiting** — Throttling at `/oauth2/token` breaks integrations and may indicate credential stuffing or runaway automation.

Documented **Data sources**: HTTP 429, `AADSTS50196` / `invalid_client` bursts, `rateLimit` in response headers. **App/TA** (typical add-on context): API gateway / WAF logs, Entra `SignInLogs` with error codes, custom HEC from reverse proxy. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: proxy; **sourcetype**: access_combined. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=proxy, sourcetype="access_combined". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by client_id, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 100` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (429 rate), Table (top clients), Single value (throttled requests/hour).

## SPL

```spl
index=proxy sourcetype="access_combined" uri_path="/oauth2/v2.0/token"
| search status=429 OR like(_raw,"%rate limit%")
| bin _time span=5m
| stats count by client_id, _time
| where count > 100
| sort -count
```

## Visualization

Line chart (429 rate), Table (top clients), Single value (throttled requests/hour).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
