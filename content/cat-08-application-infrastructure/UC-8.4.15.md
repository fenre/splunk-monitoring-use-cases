<!-- AUTO-GENERATED from UC-8.4.15.json — DO NOT EDIT -->

---
id: "8.4.15"
title: "GraphQL Query Depth Violations"
criticality: "medium"
splunkPillar: "Security"
---

# UC-8.4.15 · GraphQL Query Depth Violations

## Description

Depth/complexity limit errors from Apollo/GraphQL server logs prevent DoS via deep queries.

## Value

Depth/complexity limit errors from Apollo/GraphQL server logs prevent DoS via deep queries.

## Implementation

Log structured rejection reason. Alert on high rejection rate from single client or operation. Tune limits for legitimate mobile apps.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Application logs, GraphQL gateway.
• Ensure the following data sources are available: `graphql:request` `depth`, `errors`, `operationName`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Log structured rejection reason. Alert on high rejection rate from single client or operation. Tune limits for legitimate mobile apps.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=application sourcetype="graphql:server"
| search "depth limit" OR "complexity" OR "Query is too deep"
| stats count by operationName, client_name, depth
| where count > 10
```

Understanding this SPL

**GraphQL Query Depth Violations** — Depth/complexity limit errors from Apollo/GraphQL server logs prevent DoS via deep queries.

Documented **Data sources**: `graphql:request` `depth`, `errors`, `operationName`. **App/TA** (typical add-on context): Application logs, GraphQL gateway. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: application; **sourcetype**: graphql:server. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=application, sourcetype="graphql:server". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by operationName, client_name, depth** so each row reflects one combination of those dimensions.
• Filters the current rows with `where count > 10` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare with the API gateway or mesh admin (Kong, Apigee, AWS API Gateway, etc.) and a raw log tail for the same time range.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (operation, depth, count), Bar chart (rejections by client), Line chart (depth violations over time).

## SPL

```spl
index=application sourcetype="graphql:server"
| search "depth limit" OR "complexity" OR "Query is too deep"
| stats count by operationName, client_name, depth
| where count > 10
```

## Visualization

Table (operation, depth, count), Bar chart (rejections by client), Line chart (depth violations over time).

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
