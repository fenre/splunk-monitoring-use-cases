---
id: "5.9.17"
title: "DNS Trace Delegation Chain Monitoring"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.9.17 · DNS Trace Delegation Chain Monitoring

## Description

DNS Trace tests follow the full delegation chain from root to authoritative server. Monitoring availability and duration across the chain identifies issues at specific levels of the DNS hierarchy.

## Value

DNS Trace tests follow the full delegation chain from root to authoritative server. Monitoring availability and duration across the chain identifies issues at specific levels of the DNS hierarchy.

## Implementation

Create DNS Trace tests in ThousandEyes for critical domains. Unlike DNS Server tests that query a specific resolver, DNS Trace tests follow the entire delegation chain from root servers. The same `dns.lookup.availability` and `dns.lookup.duration` metrics are reported.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (DNS Trace tests).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create DNS Trace tests in ThousandEyes for critical domains. Unlike DNS Server tests that query a specific resolver, DNS Trace tests follow the entire delegation chain from root servers. The same `dns.lookup.availability` and `dns.lookup.duration` metrics are reported.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.type="dns-trace"
| stats avg(dns.lookup.availability) as avg_availability avg(dns.lookup.duration) as avg_duration_s by dns.question.name, thousandeyes.source.agent.name
| eval avg_duration_ms=round(avg_duration_s*1000,1)
| where avg_availability < 100 OR avg_duration_ms > 500
| sort avg_availability, -avg_duration_ms
```

Understanding this SPL

**DNS Trace Delegation Chain Monitoring** — DNS Trace tests follow the full delegation chain from root to authoritative server. Monitoring availability and duration across the chain identifies issues at specific levels of the DNS hierarchy.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (DNS Trace tests). **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `stats` rolls up events into metrics; results are split **by dns.question.name, thousandeyes.source.agent.name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **avg_duration_ms** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where avg_availability < 100 OR avg_duration_ms > 500` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (duration over time), Table (domain, agent, availability, duration), Alert on failures.

## SPL

```spl
`stream_index` thousandeyes.test.type="dns-trace"
| stats avg(dns.lookup.availability) as avg_availability avg(dns.lookup.duration) as avg_duration_s by dns.question.name, thousandeyes.source.agent.name
| eval avg_duration_ms=round(avg_duration_s*1000,1)
| where avg_availability < 100 OR avg_duration_ms > 500
| sort avg_availability, -avg_duration_ms
```

## Visualization

Line chart (duration over time), Table (domain, agent, availability, duration), Alert on failures.

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
