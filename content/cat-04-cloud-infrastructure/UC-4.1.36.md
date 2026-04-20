---
id: "4.1.36"
title: "ElastiCache/Redis CPU and Evictions"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.1.36 · ElastiCache/Redis CPU and Evictions

## Description

High CPU or evictions indicate undersized cache or hot keys. Impacts application latency and cache hit ratio.

## Value

High CPU or evictions indicate undersized cache or hot keys. Impacts application latency and cache hit ratio.

## Implementation

Collect ElastiCache metrics per node/cluster. Alert on CPUUtilization > 80% sustained. Monitor CacheHitRate; low hit rate and high evictions suggest need for more memory or key design review.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: CloudWatch ElastiCache metrics (CPUUtilization, CacheEvictions, CacheHitRate).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect ElastiCache metrics per node/cluster. Alert on CPUUtilization > 80% sustained. Monitor CacheHitRate; low hit rate and high evictions suggest need for more memory or key design review.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/ElastiCache" (metric_name="CPUUtilization" OR metric_name="CacheEvictions")
| bin _time span=5m
| eval cpu=if(metric_name="CPUUtilization", Average, null()),
       evictions=if(metric_name="CacheEvictions", Average, null())
| stats avg(cpu) as cpu, sum(evictions) as evictions by _time, CacheClusterId
| where cpu > 80 OR evictions > 100
```

Understanding this SPL

**ElastiCache/Redis CPU and Evictions** — High CPU or evictions indicate undersized cache or hot keys. Impacts application latency and cache hit ratio.

Documented **Data sources**: CloudWatch ElastiCache metrics (CPUUtilization, CacheEvictions, CacheHitRate). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `eval` defines or adjusts **cpu** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by _time, CacheClusterId** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where cpu > 80 OR evictions > 100` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (CPU, evictions, hit rate), Table (cluster, metrics), Gauge (hit rate).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/ElastiCache" (metric_name="CPUUtilization" OR metric_name="CacheEvictions")
| bin _time span=5m
| eval cpu=if(metric_name="CPUUtilization", Average, null()),
       evictions=if(metric_name="CacheEvictions", Average, null())
| stats avg(cpu) as cpu, sum(evictions) as evictions by _time, CacheClusterId
| where cpu > 80 OR evictions > 100
```

## Visualization

Line chart (CPU, evictions, hit rate), Table (cluster, metrics), Gauge (hit rate).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
