---
id: "8.5.9"
title: "Squid Proxy Cache Hit Ratio"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.5.9 · Squid Proxy Cache Hit Ratio

## Description

Cache HIT/MISS/DENY rates on forward/reverse proxy indicate cache effectiveness and upstream load. Declining ratio increases origin latency and bandwidth.

## Value

Cache HIT/MISS/DENY rates on forward/reverse proxy indicate cache effectiveness and upstream load. Declining ratio increases origin latency and bandwidth.

## Implementation

Configure Squid to log cache result codes (TCP_HIT, TCP_MISS, TCP_DENIED, TCP_REFRESH) in access.log. Forward via Universal Forwarder. Parse cache_result field. Alternatively poll Squid SNMP cacheHitRatio if available. Calculate hit ratio per 5-minute window. Alert when MISS rate exceeds 30%. Correlate with request rate for capacity planning.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom (Squid access log, SNMP).
• Ensure the following data sources are available: Squid access.log (cache result codes), SNMP.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Squid to log cache result codes (TCP_HIT, TCP_MISS, TCP_DENIED, TCP_REFRESH) in access.log. Forward via Universal Forwarder. Parse cache_result field. Alternatively poll Squid SNMP cacheHitRatio if available. Calculate hit ratio per 5-minute window. Alert when MISS rate exceeds 30%. Correlate with request rate for capacity planning.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=proxy sourcetype="squid:access"
| rex "TCP_(?<cache_result>HIT|MISS|DENIED|REFRESH)"
| stats count by cache_result
| eventstats sum(count) as total
| eval pct=round(count/total*100,2)
| where cache_result=="MISS" AND pct > 30
```

Understanding this SPL

**Squid Proxy Cache Hit Ratio** — Cache HIT/MISS/DENY rates on forward/reverse proxy indicate cache effectiveness and upstream load. Declining ratio increases origin latency and bandwidth.

Documented **Data sources**: Squid access.log (cache result codes), SNMP. **App/TA** (typical add-on context): Custom (Squid access log, SNMP). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: proxy; **sourcetype**: squid:access. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=proxy, sourcetype="squid:access". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• `stats` rolls up events into metrics; results are split **by cache_result** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eventstats` aggregates the pipeline (counts, distinct values, sums, percentiles, etc.) into fewer rows.
• `eval` defines or adjusts **pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where cache_result=="MISS" AND pct > 30` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Web.Web by Web.status, Web.http_method, Web.dest | sort - count
```

Understanding this CIM / accelerated SPL

**Squid Proxy Cache Hit Ratio** — Cache HIT/MISS/DENY rates on forward/reverse proxy indicate cache effectiveness and upstream load. Declining ratio increases origin latency and bandwidth.

Documented **Data sources**: Squid access.log (cache result codes), SNMP. **App/TA** (typical add-on context): Custom (Squid access log, SNMP). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Web.Web` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Pie chart (HIT vs MISS vs DENY), Line chart (hit ratio over time), Table (cache result distribution), Single value (hit ratio %).

## SPL

```spl
index=proxy sourcetype="squid:access"
| rex "TCP_(?<cache_result>HIT|MISS|DENIED|REFRESH)"
| stats count by cache_result
| eventstats sum(count) as total
| eval pct=round(count/total*100,2)
| where cache_result=="MISS" AND pct > 30
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Web.Web by Web.status, Web.http_method, Web.dest | sort - count
```

## Visualization

Pie chart (HIT vs MISS vs DENY), Line chart (hit ratio over time), Table (cache result distribution), Single value (hit ratio %).

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
