<!-- AUTO-GENERATED from UC-5.9.16.json — DO NOT EDIT -->

---
id: "5.9.16"
title: "DNS Provider Comparison"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.9.16 · DNS Provider Comparison

## Description

Comparing resolution times across DNS providers (internal recursive resolvers, external providers like Cloudflare, Google, ISP resolvers) helps optimize DNS configuration for lowest latency.

## Value

Comparing resolution times across DNS providers (internal recursive resolvers, external providers like Cloudflare, Google, ISP resolvers) helps optimize DNS configuration for lowest latency.

## Implementation

Create DNS Server tests in ThousandEyes for the same domain against multiple DNS server addresses. Each test targets a different resolver. Compare `dns.lookup.duration` and `dns.lookup.availability` across server addresses.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (DNS tests).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create DNS Server tests in ThousandEyes for the same domain against multiple DNS server addresses. Each test targets a different resolver. Compare `dns.lookup.duration` and `dns.lookup.availability` across server addresses.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.type="dns-server"
| stats avg(dns.lookup.duration) as avg_duration_s avg(dns.lookup.availability) as avg_availability by server.address, dns.question.name
| eval avg_duration_ms=round(avg_duration_s*1000,1)
| sort dns.question.name, avg_duration_ms
```

Understanding this SPL

**DNS Provider Comparison** — Comparing resolution times across DNS providers (internal recursive resolvers, external providers like Cloudflare, Google, ISP resolvers) helps optimize DNS configuration for lowest latency.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (DNS tests). **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `stats` rolls up events into metrics; results are split **by server.address, dns.question.name** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **avg_duration_ms** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare the same tests and time window in the Cisco ThousandEyes App for Splunk dashboard or the test view at app.thousandeyes.com so Splunk’s metrics and states match the vendor. If they disagree, check streaming or HEC inputs, macros, and API or token health before retuning.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Column chart (resolution time by provider), Table (provider, domain, duration, availability), Comparison dashboard.

## SPL

```spl
`stream_index` thousandeyes.test.type="dns-server"
| stats avg(dns.lookup.duration) as avg_duration_s avg(dns.lookup.availability) as avg_availability by server.address, dns.question.name
| eval avg_duration_ms=round(avg_duration_s*1000,1)
| sort dns.question.name, avg_duration_ms
```

## Visualization

Column chart (resolution time by provider), Table (provider, domain, duration, availability), Comparison dashboard.

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
