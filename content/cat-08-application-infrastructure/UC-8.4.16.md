<!-- AUTO-GENERATED from UC-8.4.16.json — DO NOT EDIT -->

---
id: "8.4.16"
title: "API Version Deprecation Tracking"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.4.16 · API Version Deprecation Tracking

## Description

Traffic to `/v1/` deprecated routes vs `/v2/` for migration planning. Header `Sunset` or path-based routing logs.

## Value

Traffic to `/v1/` deprecated routes vs `/v2/` for migration planning. Header `Sunset` or path-based routing logs.

## Implementation

Maintain deprecation calendar lookup. Weekly report of traffic still on old versions. Alert on any `/v1/*` usage after sunset date.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: API gateway access logs.
• Ensure the following data sources are available: `request_uri` path version segment, `X-API-Version`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Maintain deprecation calendar lookup. Weekly report of traffic still on old versions. Alert on any `/v1/*` usage after sunset date.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=api sourcetype="kong:access"
| rex field=request_uri "^/api/v(?<api_version>\d+)/"
| stats count by api_version, request_uri
| lookup api_version_deprecation api_version OUTPUT sunset_epoch
| eval days_to_sunset=round((sunset_epoch-now())/86400)
| where days_to_sunset < 90 AND api_version="1"
```

Understanding this SPL

**API Version Deprecation Tracking** — Traffic to `/v1/` deprecated routes vs `/v2/` for migration planning. Header `Sunset` or path-based routing logs.

Documented **Data sources**: `request_uri` path version segment, `X-API-Version`. **App/TA** (typical add-on context): API gateway access logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: api; **sourcetype**: kong:access. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=api, sourcetype="kong:access". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• `stats` rolls up events into metrics; results are split **by api_version, request_uri** so each row reflects one combination of those dimensions.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• `eval` defines or adjusts **days_to_sunset** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where days_to_sunset < 90 AND api_version="1"` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare with the API gateway or mesh admin (Kong, Apigee, AWS API Gateway, etc.) and a raw log tail for the same time range.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Pie chart (traffic by version), Line chart (v1 traffic trend), Table (routes still on deprecated version).

## SPL

```spl
index=api sourcetype="kong:access"
| rex field=request_uri "^/api/v(?<api_version>\d+)/"
| stats count by api_version, request_uri
| lookup api_version_deprecation api_version OUTPUT sunset_epoch
| eval days_to_sunset=round((sunset_epoch-now())/86400)
| where days_to_sunset < 90 AND api_version="1"
```

## Visualization

Pie chart (traffic by version), Line chart (v1 traffic trend), Table (routes still on deprecated version).

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
