<!-- AUTO-GENERATED from UC-5.6.12.json — DO NOT EDIT -->

---
id: "5.6.12"
title: "DNS Query Type Distribution"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.6.12 · DNS Query Type Distribution

## Description

Unusual query type distribution (spikes in TXT, MX, or ANY) can indicate DNS tunneling, reconnaissance, or abuse.

## Value

Unusual query type distribution (spikes in TXT, MX, or ANY) can indicate DNS tunneling, reconnaissance, or abuse.

## Implementation

Capture DNS query types via Splunk Stream or DNS server logs. Baseline normal distribution (typically >80% A/AAAA). Alert on abnormal increases in TXT, NULL, or ANY queries.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk_TA_infoblox, Splunk Stream.
• Ensure the following data sources are available: `sourcetype=infoblox:dns`, `sourcetype=stream:dns`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Capture DNS query types via Splunk Stream or DNS server logs. Baseline normal distribution (typically >80% A/AAAA). Alert on abnormal increases in TXT, NULL, or ANY queries.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="stream:dns"
| stats count by query_type
| eventstats sum(count) as total
| eval pct=round(count/total*100,2) | sort -count
| head 20
```

Understanding this SPL

**DNS Query Type Distribution** — Unusual query type distribution (spikes in TXT, MX, or ANY) can indicate DNS tunneling, reconnaissance, or abuse.

Documented **Data sources**: `sourcetype=infoblox:dns`, `sourcetype=stream:dns`. **App/TA** (typical add-on context): Splunk_TA_infoblox, Splunk Stream. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: stream:dns. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="stream:dns". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by query_type** so each row reflects one combination of those dimensions.
• `eventstats` aggregates the pipeline (counts, distinct values, sums, percentiles, etc.) into fewer rows.
• `eval` defines or adjusts **pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Limits the number of rows with `head`.


Step 3 — Validate
Compare query volume, response codes, or latency in Infoblox reporting, Microsoft DNS views, BIND logs, or Meraki Network > Monitor to the Splunk results for the same resolvers and time range.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Pie chart (query type distribution), Timechart (by type), Table.

## SPL

```spl
index=network sourcetype="stream:dns"
| stats count by query_type
| eventstats sum(count) as total
| eval pct=round(count/total*100,2) | sort -count
| head 20
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

Pie chart (query type distribution), Timechart (by type), Table.

## References

- [CIM: Network_Resolution](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Resolution)
