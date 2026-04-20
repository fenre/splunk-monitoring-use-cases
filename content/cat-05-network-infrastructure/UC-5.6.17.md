---
id: "5.6.17"
title: "DNS Query Latency and Resolution Failure by Resolver"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.6.17 · DNS Query Latency and Resolution Failure by Resolver

## Description

Slow or failing DNS resolution impacts all applications. Tracking latency and NXDOMAIN/timeout rates per resolver supports capacity and upstream provider decisions.

## Value

Slow or failing DNS resolution impacts all applications. Tracking latency and NXDOMAIN/timeout rates per resolver supports capacity and upstream provider decisions.

## Implementation

Run synthetic DNS probes (e.g. dig to critical domains) from multiple hosts; ingest response time and result. Optionally ingest resolver query logs. Alert when latency exceeds 200ms or failure rate exceeds 5%.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (dig, DNS query log), Infoblox/BIND query logs.
• Ensure the following data sources are available: DNS resolver query logs, synthetic DNS probes.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Run synthetic DNS probes (e.g. dig to critical domains) from multiple hosts; ingest response time and result. Optionally ingest resolver query logs. Alert when latency exceeds 200ms or failure rate exceeds 5%.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype=dns_query
| bin _time span=5m
| stats avg(response_time_ms) as avg_ms, count(eval(response_code="NXDOMAIN" OR response_code="SERVFAIL")) as failures, count as total by resolver_ip, _time
| eval fail_rate=round(failures/total*100, 2)
| where avg_ms > 200 OR fail_rate > 5
| table resolver_ip avg_ms fail_rate total
```

Understanding this SPL

**DNS Query Latency and Resolution Failure by Resolver** — Slow or failing DNS resolution impacts all applications. Tracking latency and NXDOMAIN/timeout rates per resolver supports capacity and upstream provider decisions.

Documented **Data sources**: DNS resolver query logs, synthetic DNS probes. **App/TA** (typical add-on context): Custom scripted input (dig, DNS query log), Infoblox/BIND query logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: dns_query. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype=dns_query. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by resolver_ip, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **fail_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where avg_ms > 200 OR fail_rate > 5` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **DNS Query Latency and Resolution Failure by Resolver**): table resolver_ip avg_ms fail_rate total


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (latency by resolver), Table (resolver, avg ms, fail rate), Single value (p95 latency).

## SPL

```spl
index=network sourcetype=dns_query
| bin _time span=5m
| stats avg(response_time_ms) as avg_ms, count(eval(response_code="NXDOMAIN" OR response_code="SERVFAIL")) as failures, count as total by resolver_ip, _time
| eval fail_rate=round(failures/total*100, 2)
| where avg_ms > 200 OR fail_rate > 5
| table resolver_ip avg_ms fail_rate total
```

## Visualization

Line chart (latency by resolver), Table (resolver, avg ms, fail rate), Single value (p95 latency).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
