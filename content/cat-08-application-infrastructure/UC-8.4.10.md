---
id: "8.4.10"
title: "Kong Rate Limit Violations"
criticality: "medium"
splunkPillar: "Security"
---

# UC-8.4.10 · Kong Rate Limit Violations

## Description

Kong `rate_limiting` plugin log lines and `429` with `RateLimit-*` headers. Identifies abusive consumers vs tight quotas.

## Value

Kong `rate_limiting` plugin log lines and `429` with `RateLimit-*` headers. Identifies abusive consumers vs tight quotas.

## Implementation

Enable plugin logging. Baseline 429s per consumer. Alert on spike vs baseline or new consumer_id hitting limit.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Kong admin/access logs.
• Ensure the following data sources are available: `kong:access` `status=429`, `rate_limiting` plugin log.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable plugin logging. Baseline 429s per consumer. Alert on spike vs baseline or new consumer_id hitting limit.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=api sourcetype="kong:access" status=429
| stats count by consumer_id, request_uri, rate_limit_plugin
| sort -count
| head 50
```

Understanding this SPL

**Kong Rate Limit Violations** — Kong `rate_limiting` plugin log lines and `429` with `RateLimit-*` headers. Identifies abusive consumers vs tight quotas.

Documented **Data sources**: `kong:access` `status=429`, `rate_limiting` plugin log. **App/TA** (typical add-on context): Kong admin/access logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: api; **sourcetype**: kong:access. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=api, sourcetype="kong:access". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by consumer_id, request_uri, rate_limit_plugin** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Limits the number of rows with `head`.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Web.Web by Web.status, Web.http_method, Web.dest | sort - count
```

Understanding this CIM / accelerated SPL

**Kong Rate Limit Violations** — Kong `rate_limiting` plugin log lines and `429` with `RateLimit-*` headers. Identifies abusive consumers vs tight quotas.

Documented **Data sources**: `kong:access` `status=429`, `rate_limiting` plugin log. **App/TA** (typical add-on context): Kong admin/access logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Web.Web` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (429 by consumer), Line chart (429 rate), Table (top limited routes).

## SPL

```spl
index=api sourcetype="kong:access" status=429
| stats count by consumer_id, request_uri, rate_limit_plugin
| sort -count
| head 50
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Web.Web by Web.status, Web.http_method, Web.dest | sort - count
```

## Visualization

Bar chart (429 by consumer), Line chart (429 rate), Table (top limited routes).

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
