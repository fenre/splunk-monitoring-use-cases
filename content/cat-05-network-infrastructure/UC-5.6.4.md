<!-- AUTO-GENERATED from UC-5.6.4.json — DO NOT EDIT -->

---
id: "5.6.4"
title: "DNS Tunneling Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.6.4 · DNS Tunneling Detection

## Description

DNS tunneling uses DNS queries to exfiltrate data or establish C2 channels, bypassing traditional security controls.

## Value

DNS tunneling uses DNS queries to exfiltrate data or establish C2 channels, bypassing traditional security controls.

## Implementation

Monitor for anomalously long DNS queries (>50 chars), high query volumes to single domains, and TXT record queries. Baseline normal DNS patterns.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: DNS TAs.
• Ensure the following data sources are available: DNS query logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor for anomalously long DNS queries (>50 chars), high query volumes to single domains, and TXT record queries. Baseline normal DNS patterns.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=dns
| eval query_len=len(query)
| stats avg(query_len) as avg_len, count as queries, dc(query) as unique_queries by src, domain
| where avg_len > 50 OR queries > 1000
| sort -avg_len
```

Understanding this SPL

**DNS Tunneling Detection** — DNS tunneling uses DNS queries to exfiltrate data or establish C2 channels, bypassing traditional security controls.

Documented **Data sources**: DNS query logs. **App/TA** (typical add-on context): DNS TAs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: dns.

**Pipeline walkthrough**

• Scopes the data: index=dns. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **query_len** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by src, domain** so each row reflects one combination of those dimensions.
• Filters the current rows with `where avg_len > 50 OR queries > 1000` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare query volume, response codes, or latency in Infoblox reporting, Microsoft DNS views, BIND logs, or Meraki Network > Monitor to the Splunk results for the same resolvers and time range.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (client, domain, query length, volume), Scatter plot, Bar chart.

## SPL

```spl
index=dns
| eval query_len=len(query)
| stats avg(query_len) as avg_len, count as queries, dc(query) as unique_queries by src, domain
| where avg_len > 50 OR queries > 1000
| sort -avg_len
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Resolution.DNS
  by DNS.src DNS.query span=5m
| where count>0
| sort -count
```

## Visualization

Table (client, domain, query length, volume), Scatter plot, Bar chart.

## References

- [CIM: Network_Resolution](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Resolution)
