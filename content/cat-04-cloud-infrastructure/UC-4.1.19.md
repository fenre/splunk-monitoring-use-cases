<!-- AUTO-GENERATED from UC-4.1.19.json — DO NOT EDIT -->

---
id: "4.1.19"
title: "WAF Blocked Request Analysis"
criticality: "medium"
splunkPillar: "Security"
---

# UC-4.1.19 · WAF Blocked Request Analysis

## Description

WAF blocks reveal attack patterns targeting your applications. Analysis helps tune rules and understand the threat landscape.

## Value

WAF blocks reveal attack patterns targeting your applications. Analysis helps tune rules and understand the threat landscape.

## Implementation

Enable WAF logging to S3 or Kinesis Firehose. Ingest via Splunk_TA_aws. Analyze blocked requests by rule, source IP, URI, and user agent to identify attack patterns and false positives.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: `sourcetype=aws:waf` (WAF logs via S3 or Kinesis).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable WAF logging to S3 or Kinesis Firehose. Ingest via Splunk_TA_aws. Analyze blocked requests by rule, source IP, URI, and user agent to identify attack patterns and false positives.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:waf" action="BLOCK"
| stats count by terminatingRuleId, httpRequest.clientIp, httpRequest.uri
| sort 20 -count
```

Understanding this SPL

**WAF Blocked Request Analysis** — WAF blocks reveal attack patterns targeting your applications. Analysis helps tune rules and understand the threat landscape.

Documented **Data sources**: `sourcetype=aws:waf` (WAF logs via S3 or Kinesis). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:waf. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:waf". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by terminatingRuleId, httpRequest.clientIp, httpRequest.uri** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (rule, source, URI, count), Bar chart by rule, Map (source IPs), Timeline.

## SPL

```spl
index=aws sourcetype="aws:waf" action="BLOCK"
| stats count by terminatingRuleId, httpRequest.clientIp, httpRequest.uri
| sort 20 -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Web.proxy
  where (Web.status >= 400 OR like(Web.status, "5%") OR like(Web.status, "403"))
  by Web.src Web.url Web.status span=1h
| sort -count
```

## Visualization

Table (rule, source, URI, count), Bar chart by rule, Map (source IPs), Timeline.

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
