---
id: "5.6.3"
title: "SERVFAIL Rate Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.6.3 · SERVFAIL Rate Monitoring

## Description

SERVFAIL increases indicate upstream DNS failures, DNSSEC validation issues, or resolver problems.

## Value

SERVFAIL increases indicate upstream DNS failures, DNSSEC validation issues, or resolver problems.

## Implementation

Track SERVFAIL response codes. Alert on increases. Investigate which domains are failing and which resolvers are affected.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: DNS TAs.
• Ensure the following data sources are available: DNS query logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Track SERVFAIL response codes. Alert on increases. Investigate which domains are failing and which resolvers are affected.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=dns reply_code="SERVFAIL" OR rcode="2"
| timechart span=5m count as servfail | where servfail > 10
```

Understanding this SPL

**SERVFAIL Rate Monitoring** — SERVFAIL increases indicate upstream DNS failures, DNSSEC validation issues, or resolver problems.

Documented **Data sources**: DNS query logs. **App/TA** (typical add-on context): DNS TAs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: dns.

**Pipeline walkthrough**

• Scopes the data: index=dns. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets — ideal for trending and alerting on this use case.
• Filters the current rows with `where servfail > 10` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart, Table (failing domains), Single value.

## SPL

```spl
index=dns reply_code="SERVFAIL" OR rcode="2"
| timechart span=5m count as servfail | where servfail > 10
```

## Visualization

Line chart, Table (failing domains), Single value.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
