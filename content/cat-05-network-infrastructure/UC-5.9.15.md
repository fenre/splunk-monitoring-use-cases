---
id: "5.9.15"
title: "DNSSEC Validity Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.15 · DNSSEC Validity Monitoring

## Description

DNSSEC validation failures cause hard resolution failures for DNSSEC-enforcing resolvers. Monitoring validity ensures the DNSSEC chain of trust remains intact.

## Value

DNSSEC validation failures cause hard resolution failures for DNSSEC-enforcing resolvers. Monitoring validity ensures the DNSSEC chain of trust remains intact.

## Implementation

Create DNSSEC tests in ThousandEyes for domains where you manage DNSSEC signing. The OTel metric `dns.lookup.validity` reports 100% when the DNSSEC chain validates successfully and 0% on failure. The Splunk App Network dashboard includes a "DNS Validity (%)" line chart.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (DNSSEC tests).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create DNSSEC tests in ThousandEyes for domains where you manage DNSSEC signing. The OTel metric `dns.lookup.validity` reports 100% when the DNSSEC chain validates successfully and 0% on failure. The Splunk App Network dashboard includes a "DNS Validity (%)" line chart.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.type="dns-dnssec"
| stats avg(dns.lookup.validity) as avg_validity by dns.question.name
| where avg_validity < 100
| sort avg_validity
```

Understanding this SPL

**DNSSEC Validity Monitoring** — DNSSEC validation failures cause hard resolution failures for DNSSEC-enforcing resolvers. Monitoring validity ensures the DNSSEC chain of trust remains intact.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (DNSSEC tests). **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `stats` rolls up events into metrics; results are split **by dns.question.name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where avg_validity < 100` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (validity % over time), Single value (current validity), Table.

## SPL

```spl
`stream_index` thousandeyes.test.type="dns-dnssec"
| stats avg(dns.lookup.validity) as avg_validity by dns.question.name
| where avg_validity < 100
| sort avg_validity
```

## Visualization

Line chart (validity % over time), Single value (current validity), Table.

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
