<!-- AUTO-GENERATED from UC-4.1.56.json — DO NOT EDIT -->

---
id: "4.1.56"
title: "AWS Lambda Cold Start Monitoring"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.1.56 · AWS Lambda Cold Start Monitoring

## Description

Cold start frequency and duration impact user experience. High cold start rates or long init times cause request latency spikes and timeouts.

## Value

Cold start frequency and duration impact user experience. High cold start rates or long init times cause request latency spikes and timeouts.

## Implementation

Enable CloudWatch Logs for Lambda (platform logs include REPORT and INIT). Optionally ingest X-Ray traces for end-to-end cold start visibility. Parse REPORT/INIT_START lines to extract init duration and invocation type. Alert when cold start rate exceeds 10% or init duration > 1s for critical functions. Consider provisioned concurrency for latency-sensitive workloads.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: CloudWatch Logs (Lambda platform logs: REPORT, INIT), X-Ray traces.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable CloudWatch Logs for Lambda (platform logs include REPORT and INIT). Optionally ingest X-Ray traces for end-to-end cold start visibility. Parse REPORT/INIT_START lines to extract init duration and invocation type. Alert when cold start rate exceeds 10% or init duration > 1s for critical functions. Consider provisioned concurrency for latency-sensitive workloads.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatchlogs" ("REPORT RequestId" OR "INIT_START")
| eval function_name=case(isnotnull(log_group), replace(log_group, "/aws/lambda/", ""), 1=1, "unknown")
| rex "Init Duration:\s+(?<init_ms>\d+\.?\d*)\s*ms"
| rex "Duration:\s+(?<duration_ms>\d+\.?\d*)\s*ms"
| eval cold_start=if(match(_raw, "INIT_START"), 1, 0)
| stats count as invocations, sum(cold_start) as cold_starts, avg(init_ms) as avg_init_ms, avg(duration_ms) as avg_duration_ms by function_name, bin(_time, 1h)
| eval cold_start_pct=round(cold_starts/invocations*100, 1)
| where cold_start_pct > 10 OR avg_init_ms > 1000
| table _time function_name invocations cold_starts cold_start_pct avg_init_ms avg_duration_ms
| sort -cold_start_pct
```

Understanding this SPL

**AWS Lambda Cold Start Monitoring** — Cold start frequency and duration impact user experience. High cold start rates or long init times cause request latency spikes and timeouts.

Documented **Data sources**: CloudWatch Logs (Lambda platform logs: REPORT, INIT), X-Ray traces. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatchlogs. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatchlogs". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **function_name** — often to normalize units, derive a ratio, or prepare for thresholds.
• Extracts fields with `rex` (regular expression).
• Extracts fields with `rex` (regular expression).
• `eval` defines or adjusts **cold_start** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by function_name, bin(_time, 1h)** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **cold_start_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where cold_start_pct > 10 OR avg_init_ms > 1000` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **AWS Lambda Cold Start Monitoring**): table _time function_name invocations cold_starts cold_start_pct avg_init_ms avg_duration_ms
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (cold start % and init duration by function over time), Table (function, cold starts, avg init ms), Single value (cold start rate).

## SPL

```spl
index=aws sourcetype="aws:cloudwatchlogs" ("REPORT RequestId" OR "INIT_START")
| eval function_name=case(isnotnull(log_group), replace(log_group, "/aws/lambda/", ""), 1=1, "unknown")
| rex "Init Duration:\s+(?<init_ms>\d+\.?\d*)\s*ms"
| rex "Duration:\s+(?<duration_ms>\d+\.?\d*)\s*ms"
| eval cold_start=if(match(_raw, "INIT_START"), 1, 0)
| stats count as invocations, sum(cold_start) as cold_starts, avg(init_ms) as avg_init_ms, avg(duration_ms) as avg_duration_ms by function_name, bin(_time, 1h)
| eval cold_start_pct=round(cold_starts/invocations*100, 1)
| where cold_start_pct > 10 OR avg_init_ms > 1000
| table _time function_name invocations cold_starts cold_start_pct avg_init_ms avg_duration_ms
| sort -cold_start_pct
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  where match(All_Changes.app, "(?i)glue|lambda|logs")
  by All_Changes.user All_Changes.status span=1h
| sort -count
```

## Visualization

Line chart (cold start % and init duration by function over time), Table (function, cold starts, avg init ms), Single value (cold start rate).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
