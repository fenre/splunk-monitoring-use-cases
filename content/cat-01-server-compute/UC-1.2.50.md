<!-- AUTO-GENERATED from UC-1.2.50.json — DO NOT EDIT -->

---
id: "1.2.50"
title: "DNS Debug Query Logging"
criticality: "medium"
splunkPillar: "Security"
---

# UC-1.2.50 · DNS Debug Query Logging

## Description

DNS query logging reveals C2 communication via DNS tunneling, DGA domains, and unauthorized DNS resolution. Essential for security visibility.

## Value

DNS is still the control plane of many stealthy C2s—if you only watch HTTP, you will miss a class of problems.

## Implementation

Enable DNS Analytical logging on Windows DNS servers or DNS debug logging to file (dnscmd /config /logfilepath). Forward via Splunk_TA_windows or Splunk Add-on for Microsoft DNS. Long TXT queries (>50 chars) and high-frequency CNAME lookups indicate DNS tunneling. Queries to recently registered domains or high-entropy names suggest DGA malware. Baseline normal query patterns, then alert on anomalies.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-DNS-Server/Analytical` or DNS debug log file.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable DNS Analytical logging on Windows DNS servers or DNS debug logging to file (dnscmd /config /logfilepath). Forward via Splunk_TA_windows or Splunk Add-on for Microsoft DNS. Long TXT queries (>50 chars) and high-frequency CNAME lookups indicate DNS tunneling. Queries to recently registered domains or high-entropy names suggest DGA malware. Baseline normal query patterns, then alert on anomalies.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=dns sourcetype="MSAD:NT6:DNS" query_type IN (TXT, NULL, CNAME)
| stats count avg(query_length) as avg_len by query, client_ip
| where avg_len > 50 OR count > 100
| sort -avg_len
```

Understanding this SPL

**DNS Debug Query Logging** — DNS query logging reveals C2 communication via DNS tunneling, DGA domains, and unauthorized DNS resolution. Essential for security visibility.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-DNS-Server/Analytical` or DNS debug log file. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: dns; **sourcetype**: MSAD:NT6:DNS. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=dns, sourcetype="MSAD:NT6:DNS". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by query, client_ip** so each row reflects one combination of those dimensions.
• Filters the current rows with `where avg_len > 50 OR count > 100` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Network_Resolution
  by host span=1h
| where count>0
```

Understanding this CIM / accelerated SPL

CIM tstats is an approximate mirror when Windows TA field extractions and CIM tags are complete. Enable the matching data model acceleration or tstats may return no rows.



Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (suspicious queries), Bar chart (query types), Timechart (query volume), Top domains.

## SPL

```spl
index=dns sourcetype="MSAD:NT6:DNS" query_type IN (TXT, NULL, CNAME)
| stats count avg(query_length) as avg_len by query, client_ip
| where avg_len > 50 OR count > 100
| sort -avg_len
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Resolution
  by host span=1h
| where count>0
```

## Visualization

Table (suspicious queries), Bar chart (query types), Timechart (query volume), Top domains.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
