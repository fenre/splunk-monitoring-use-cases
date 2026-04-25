<!-- AUTO-GENERATED from UC-5.6.2.json — DO NOT EDIT -->

---
id: "5.6.2"
title: "NXDOMAIN Spike Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.6.2 · NXDOMAIN Spike Detection

## Description

NXDOMAIN spikes indicate DGA malware (generating random domain lookups), misconfiguration, or DNS infrastructure issues.

## Value

NXDOMAIN spikes indicate DGA malware (generating random domain lookups), misconfiguration, or DNS infrastructure issues.

## Implementation

Monitor DNS response codes. Baseline NXDOMAIN rates. Alert when exceeding 3 standard deviations. Investigate the querying clients and domain patterns.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: DNS TAs.
• Ensure the following data sources are available: DNS query logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor DNS response codes. Baseline NXDOMAIN rates. Alert when exceeding 3 standard deviations. Investigate the querying clients and domain patterns.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=dns reply_code="NXDOMAIN" OR rcode="3"
| timechart span=5m count as nxdomain_count
| eventstats avg(nxdomain_count) as avg_nx, stdev(nxdomain_count) as std_nx
| where nxdomain_count > (avg_nx + 3*std_nx)
```

Understanding this SPL

**NXDOMAIN Spike Detection** — NXDOMAIN spikes indicate DGA malware (generating random domain lookups), misconfiguration, or DNS infrastructure issues.

Documented **Data sources**: DNS query logs. **App/TA** (typical add-on context): DNS TAs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: dns.

**Pipeline walkthrough**

• Scopes the data: index=dns. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets — ideal for trending and alerting on this use case.
• `eventstats` aggregates the pipeline (counts, distinct values, sums, percentiles, etc.) into fewer rows.
• Filters the current rows with `where nxdomain_count > (avg_nx + 3*std_nx)` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare query volume, response codes, or latency in Infoblox reporting, Microsoft DNS views, BIND logs, or Meraki Network > Monitor to the Splunk results for the same resolvers and time range.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart with threshold, Table (top NXDOMAIN clients), Bar chart (top queried NX domains).

## SPL

```spl
index=dns reply_code="NXDOMAIN" OR rcode="3"
| timechart span=5m count as nxdomain_count
| eventstats avg(nxdomain_count) as avg_nx, stdev(nxdomain_count) as std_nx
| where nxdomain_count > (avg_nx + 3*std_nx)
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Resolution.DNS
  by DNS.query DNS.reply_code span=5m
| where count>0
| sort -count
```

## Visualization

Line chart with threshold, Table (top NXDOMAIN clients), Bar chart (top queried NX domains).

## References

- [CIM: Network_Resolution](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Resolution)
