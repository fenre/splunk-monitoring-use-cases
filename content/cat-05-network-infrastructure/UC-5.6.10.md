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
• `stats` rolls up events into metrics; results are split **by query_domain, query_type** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Network_Resolution.DNS
  where DNS.reply_code_id=3
  by DNS.src DNS.query span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**DNSSEC Validation Failures** — DNSSEC failures can indicate DNS spoofing attempts or misconfigured zones. Monitoring prevents users from being directed to malicious sites.

Documented **Data sources**: `sourcetype=infoblox:dns`, `sourcetype=named`. **App/TA** (typical add-on context): Splunk_TA_infoblox, BIND logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Network_Resolution.DNS` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

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
  where DNS.reply_code_id=3
  by DNS.src DNS.query span=1h
| sort -count
```

## Visualization

Table (domain, failure count), Timechart (failure rate), Bar chart.

## References

- [CIM: Network_Resolution](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Resolution)
