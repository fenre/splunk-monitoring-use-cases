<!-- AUTO-GENERATED from UC-5.6.10.json — DO NOT EDIT -->

---
id: "5.6.10"
title: "DNSSEC Validation Failures"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.6.10 · DNSSEC Validation Failures

## Description

DNSSEC failures can indicate DNS spoofing attempts or misconfigured zones. Monitoring prevents users from being directed to malicious sites.

## Value

DNSSEC failures can indicate DNS spoofing attempts or misconfigured zones. Monitoring prevents users from being directed to malicious sites.

## Implementation

Enable DNSSEC validation logging. Monitor for validation failures by domain. Cross-reference with known domain registrations. Alert on spikes in DNSSEC failures.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk_TA_infoblox, BIND logs.
• Ensure the following data sources are available: `sourcetype=infoblox:dns`, `sourcetype=named`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable DNSSEC validation logging. Monitor for validation failures by domain. Cross-reference with known domain registrations. Alert on spikes in DNSSEC failures.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="named" "DNSSEC" ("validation failure" OR "SERVFAIL" OR "no valid signature")
| rex "(?<query_domain>[a-zA-Z0-9.-]+\.)/(?<query_type>\w+)"
| stats count by query_domain, query_type | sort -count
```

Understanding this SPL

**DNSSEC Validation Failures** — DNSSEC failures can indicate DNS spoofing attempts or misconfigured zones. Monitoring prevents users from being directed to malicious sites.

Documented **Data sources**: `sourcetype=infoblox:dns`, `sourcetype=named`. **App/TA** (typical add-on context): Splunk_TA_infoblox, BIND logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: named. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="named". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• `stats` rolls up events into metrics; results are split **by query_domain, query_type** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare query volume, response codes, or latency in Infoblox reporting, Microsoft DNS views, BIND logs, or Meraki Network > Monitor to the Splunk results for the same resolvers and time range.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (domain, failure count), Timechart (failure rate), Bar chart.

## SPL

```spl
index=network sourcetype="named" "DNSSEC" ("validation failure" OR "SERVFAIL" OR "no valid signature")
| rex "(?<query_domain>[a-zA-Z0-9.-]+\.)/(?<query_type>\w+)"
| stats count by query_domain, query_type | sort -count
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

Table (domain, failure count), Timechart (failure rate), Bar chart.

## References

- [CIM: Network_Resolution](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Resolution)
