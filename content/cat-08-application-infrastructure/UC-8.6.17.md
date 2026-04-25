<!-- AUTO-GENERATED from UC-8.6.17.json — DO NOT EDIT -->

---
id: "8.6.17"
title: "DNS Recursive Query Volume"
criticality: "medium"
splunkPillar: "Security"
---

# UC-8.6.17 · DNS Recursive Query Volume

## Description

Sudden spike in recursive queries on internal resolvers may indicate DDoS, malware, or misconfigured application loops.

## Value

Sudden spike in recursive queries on internal resolvers may indicate DDoS, malware, or misconfigured application loops.

## Implementation

Baseline QPS per client subnet. Alert on 10× baseline or absolute flood. Top `qname` for tunneling investigation.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: BIND `named` logs, Infoblox DNS, CoreDNS logs.
• Ensure the following data sources are available: `dns:query` recursive flag, `client` IP, `qname`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Baseline QPS per client subnet. Alert on 10× baseline or absolute flood. Top `qname` for tunneling investigation.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=dns sourcetype="bind:query" OR sourcetype="dns:query"
| where recursive=1
| bucket _time span=1m
| stats count as qps by client_ip, _time
| eventstats avg(qps) as avg_q by client_ip
| where qps > avg_q*10 AND qps > 1000
```

Understanding this SPL

**DNS Recursive Query Volume** — Sudden spike in recursive queries on internal resolvers may indicate DDoS, malware, or misconfigured application loops.

Documented **Data sources**: `dns:query` recursive flag, `client` IP, `qname`. **App/TA** (typical add-on context): BIND `named` logs, Infoblox DNS, CoreDNS logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: dns; **sourcetype**: bind:query, dns:query. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=dns, sourcetype="bind:query". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where recursive=1` — typically the threshold or rule expression for this monitoring goal.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by client_ip, _time** so each row reflects one combination of those dimensions.
• `eventstats` rolls up events into metrics; results are split **by client_ip** so each row reflects one combination of those dimensions.
• Filters the current rows with `where qps > avg_q*10 AND qps > 1000` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Compare with the application or platform source of truth (logs, UI, or metrics) for the same time range, and with known change or maintenance windows.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (recursive QPS), Table (top clients), Bar chart (query types).

## SPL

```spl
index=dns sourcetype="bind:query" OR sourcetype="dns:query"
| where recursive=1
| bucket _time span=1m
| stats count as qps by client_ip, _time
| eventstats avg(qps) as avg_q by client_ip
| where qps > avg_q*10 AND qps > 1000
```

## Visualization

Line chart (recursive QPS), Table (top clients), Bar chart (query types).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
