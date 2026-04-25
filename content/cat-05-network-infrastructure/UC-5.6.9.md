<!-- AUTO-GENERATED from UC-5.6.9.json — DO NOT EDIT -->

---
id: "5.6.9"
title: "DNS Cache Hit Ratio"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.6.9 · DNS Cache Hit Ratio

## Description

Low cache hit ratios indicate either a surge of new queries, cache poisoning attempts, or misconfigured TTLs — all increasing latency and upstream load.

## Value

Low cache hit ratios indicate either a surge of new queries, cache poisoning attempts, or misconfigured TTLs — all increasing latency and upstream load.

## Implementation

Enable query logging on DNS resolvers. Track cache hit vs. miss ratio. Alert when hit ratio drops below 70%. Investigate top domains causing misses.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk_TA_infoblox, BIND/Unbound logs.
• Ensure the following data sources are available: `sourcetype=infoblox:dns`, `sourcetype=named`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable query logging on DNS resolvers. Track cache hit vs. miss ratio. Alert when hit ratio drops below 70%. Investigate top domains causing misses.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="infoblox:dns"
| eval cache_hit=if(match(message,"cache hit"),1,0), total=1
| timechart span=1h sum(cache_hit) as hits, sum(total) as total
| eval hit_ratio=round(hits/total*100,1) | where hit_ratio < 70
```

Understanding this SPL

**DNS Cache Hit Ratio** — Low cache hit ratios indicate either a surge of new queries, cache poisoning attempts, or misconfigured TTLs — all increasing latency and upstream load.

Documented **Data sources**: `sourcetype=infoblox:dns`, `sourcetype=named`. **App/TA** (typical add-on context): Splunk_TA_infoblox, BIND/Unbound logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: infoblox:dns. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="infoblox:dns". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **cache_hit** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=1h** buckets — ideal for trending and alerting on this use case.
• `eval` defines or adjusts **hit_ratio** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where hit_ratio < 70` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare query volume, response codes, or latency in Infoblox reporting, Microsoft DNS views, BIND logs, or Meraki Network > Monitor to the Splunk results for the same resolvers and time range.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (hit ratio over time), Single value (current ratio), Table (top miss domains).

## SPL

```spl
index=network sourcetype="infoblox:dns"
| eval cache_hit=if(match(message,"cache hit"),1,0), total=1
| timechart span=1h sum(cache_hit) as hits, sum(total) as total
| eval hit_ratio=round(hits/total*100,1) | where hit_ratio < 70
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

Line chart (hit ratio over time), Single value (current ratio), Table (top miss domains).

## References

- [CIM: Network_Resolution](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Resolution)
