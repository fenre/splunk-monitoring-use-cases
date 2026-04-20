---
id: "9.5.12"
title: "Okta API Rate Limit Monitoring"
criticality: "medium"
splunkPillar: "Security"
---

# UC-9.5.12 · Okta API Rate Limit Monitoring

## Description

Hitting rate limits breaks automation, integrations, and provisioning; trending usage prevents surprise throttling during peak loads.

## Value

Hitting rate limits breaks automation, integrations, and provisioning; trending usage prevents surprise throttling during peak loads.

## Implementation

Log API calls from integrations with `X-Rate-Limit-*` headers or ingest Okta rate-limit system events. Alert on HTTP 429 or sustained high utilization. Work with app owners to add backoff and caching.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_okta`, custom HEC ingestion of API responses.
• Ensure the following data sources are available: `sourcetype=OktaIM2:log` (`system.*rate*`), API response headers ingested via scripted input.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Log API calls from integrations with `X-Rate-Limit-*` headers or ingest Okta rate-limit system events. Alert on HTTP 429 or sustained high utilization. Work with app owners to add backoff and caching.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=okta (sourcetype="okta:api" OR sourcetype="OktaIM2:log")
| search http_status=429 OR like(lower(_raw),"%rate limit%")
| stats count by client_id, endpoint, http_status
| where count > 0
| sort -count
```

Understanding this SPL

**Okta API Rate Limit Monitoring** — Hitting rate limits breaks automation, integrations, and provisioning; trending usage prevents surprise throttling during peak loads.

Documented **Data sources**: `sourcetype=OktaIM2:log` (`system.*rate*`), API response headers ingested via scripted input. **App/TA** (typical add-on context): `Splunk_TA_okta`, custom HEC ingestion of API responses. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: okta; **sourcetype**: okta:api, OktaIM2:log. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=okta, sourcetype="okta:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by client_id, endpoint, http_status** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 0` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (429s over time), Table (client, endpoint), Gauge (rate limit remaining %).

Scripted input (generic example)
This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]
interval = 300
sourcetype = your_sourcetype
index = main
disabled = 0
```

The script should print one event per line (e.g. key=value). Example minimal script (bash):

```bash
#!/usr/bin/env bash
# Output metrics or events, one per line
echo "metric=value timestamp=$(date +%s)"
```

For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=okta (sourcetype="okta:api" OR sourcetype="OktaIM2:log")
| search http_status=429 OR like(lower(_raw),"%rate limit%")
| stats count by client_id, endpoint, http_status
| where count > 0
| sort -count
```

## Visualization

Line chart (429s over time), Table (client, endpoint), Gauge (rate limit remaining %).

## Known False Positives

Planned maintenance, backups, or batch jobs can drive metrics outside normal bands — correlate with change management windows.

## References

- [Splunk_TA_okta](https://splunkbase.splunk.com/app/6553)
