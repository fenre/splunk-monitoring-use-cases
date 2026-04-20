---
id: "8.5.7"
title: "Key Expiration Trending"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.5.7 · Key Expiration Trending

## Description

Monitoring TTL patterns ensures cache freshness strategy is working. Unusual patterns may indicate application bugs.

## Value

Monitoring TTL patterns ensures cache freshness strategy is working. Unusual patterns may indicate application bugs.

## Implementation

Track keys with TTL vs total keys. Monitor expiration rate. Alert if expire_pct drops significantly (new code not setting TTL on keys). Track expired_stale_perc for lazy expiration health.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input.
• Ensure the following data sources are available: Redis INFO keyspace (expires, expired_keys).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Track keys with TTL vs total keys. Monitor expiration rate. Alert if expire_pct drops significantly (new code not setting TTL on keys). Track expired_stale_perc for lazy expiration health.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cache sourcetype="redis:info"
| eval expire_pct=round(expires/keys*100,1)
| timechart span=15m avg(expire_pct) as pct_with_ttl, per_second(expired_keys) as expire_rate by host
```

Understanding this SPL

**Key Expiration Trending** — Monitoring TTL patterns ensures cache freshness strategy is working. Unusual patterns may indicate application bugs.

Documented **Data sources**: Redis INFO keyspace (expires, expired_keys). **App/TA** (typical add-on context): Custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cache; **sourcetype**: redis:info. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=cache, sourcetype="redis:info". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **expire_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=15m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (expiration rate), Dual-axis (keys with TTL % + expiration rate), Single value (% keys with TTL).

## SPL

```spl
index=cache sourcetype="redis:info"
| eval expire_pct=round(expires/keys*100,1)
| timechart span=15m avg(expire_pct) as pct_with_ttl, per_second(expired_keys) as expire_rate by host
```

## Visualization

Line chart (expiration rate), Dual-axis (keys with TTL % + expiration rate), Single value (% keys with TTL).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
