<!-- AUTO-GENERATED from UC-1.2.15.json — DO NOT EDIT -->

---
id: "1.2.15"
title: "DNS Server Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.2.15 · DNS Server Health

## Description

DNS is foundational infrastructure — when DNS is slow or failing, everything fails. Monitoring query rates and failures ensures resolution reliability.

## Value

When name resolution wobbles, “everything is broken” follows—this is an early look at DNS health before apps fail in hard-to-trace ways.

## Implementation

Enable DNS analytical logging via Event Viewer (disabled by default for performance). Alternatively use DNS debug logging to a file and forward it. Monitor query volume, SERVFAIL rate, and zone transfer events.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`, Microsoft DNS Analytical logs.
• Ensure the following data sources are available: `sourcetype=WinEventLog:DNS Server`, DNS debug/analytical logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable DNS analytical logging via Event Viewer (disabled by default for performance). Alternatively use DNS debug logging to a file and forward it. Monitor query volume, SERVFAIL rate, and zone transfer events.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=dns sourcetype="MSAD:NT6:DNS"
| timechart span=5m count as query_count by QTYPE
```

Understanding this SPL

**DNS Server Health** — DNS is foundational infrastructure — when DNS is slow or failing, everything fails. Monitoring query rates and failures ensures resolution reliability.

Documented **Data sources**: `sourcetype=WinEventLog:DNS Server`, DNS debug/analytical logs. **App/TA** (typical add-on context): `Splunk_TA_windows`, Microsoft DNS Analytical logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: dns; **sourcetype**: MSAD:NT6:DNS. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=dns, sourcetype="MSAD:NT6:DNS". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by QTYPE** — ideal for trending and alerting on this use case.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Network_Resolution
  by host span=5m
| where count>0
```

Understanding this CIM / accelerated SPL

CIM tstats is an approximate mirror when Windows TA field extractions and CIM tags are complete. Enable the matching data model acceleration or tstats may return no rows.



Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (query rate), Pie chart (query types), Single value (SERVFAIL count).

## SPL

```spl
index=dns sourcetype="MSAD:NT6:DNS"
| timechart span=5m count as query_count by QTYPE
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Resolution
  by host span=5m
| where count>0
```

## Visualization

Line chart (query rate), Pie chart (query types), Single value (SERVFAIL count).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
