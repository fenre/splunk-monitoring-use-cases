---
id: "8.4.14"
title: "API Key Abuse Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-8.4.14 · API Key Abuse Detection

## Description

Unusual volume of requests per API key or key used from many distinct IPs/countries in short window.

## Value

Unusual volume of requests per API key or key used from many distinct IPs/countries in short window.

## Implementation

Never log raw API keys. Use hashed id. Baseline per credential. Alert on volume or IP diversity anomaly. Integrate with IP reputation.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Gateway logs with `consumer_id` or `api_key` hash.
• Ensure the following data sources are available: `kong:access` `credential_id`, `src`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Never log raw API keys. Use hashed id. Baseline per credential. Alert on volume or IP diversity anomaly. Integrate with IP reputation.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=api sourcetype="kong:access"
| bin _time span=1h
| stats count, dc(src) as ips by credential_id, _time
| where count > 10000 OR ips > 50
| table credential_id count ips
```

Understanding this SPL

**API Key Abuse Detection** — Unusual volume of requests per API key or key used from many distinct IPs/countries in short window.

Documented **Data sources**: `kong:access` `credential_id`, `src`. **App/TA** (typical add-on context): Gateway logs with `consumer_id` or `api_key` hash. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: api; **sourcetype**: kong:access. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=api, sourcetype="kong:access". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by credential_id, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 10000 OR ips > 50` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **API Key Abuse Detection**): table credential_id count ips

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t dc(Web.src) as agg_value from datamodel=Web.Web by Web.status, Web.http_method, Web.dest | sort - agg_value
```

Understanding this CIM / accelerated SPL

**API Key Abuse Detection** — Unusual volume of requests per API key or key used from many distinct IPs/countries in short window.

Documented **Data sources**: `kong:access` `credential_id`, `src`. **App/TA** (typical add-on context): Gateway logs with `consumer_id` or `api_key` hash. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Web.Web` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (credential, count, ips), Map (src), Timeline (abuse spikes).

## SPL

```spl
index=api sourcetype="kong:access"
| bin _time span=1h
| stats count, dc(src) as ips by credential_id, _time
| where count > 10000 OR ips > 50
| table credential_id count ips
```

## CIM SPL

```spl
| tstats summariesonly=t dc(Web.src) as agg_value from datamodel=Web.Web by Web.status, Web.http_method, Web.dest | sort - agg_value
```

## Visualization

Table (credential, count, ips), Map (src), Timeline (abuse spikes).

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
