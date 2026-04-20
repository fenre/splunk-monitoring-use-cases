---
id: "5.12.6"
title: "Signaling Storm Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.12.6 · Signaling Storm Detection

## Description

Bursts of SIP OPTIONS, REGISTER, or diameter requests can indicate reflection DDoS or misconfigured endpoints — complements UC-5.10.5 with cross-layer view.

## Value

Bursts of SIP OPTIONS, REGISTER, or diameter requests can indicate reflection DDoS or misconfigured endpoints — complements UC-5.10.5 with cross-layer view.

## Implementation

Whitelist health-check sources; coordinate with peer ops when storm targets upstream interconnect.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk App for Stream, STP/Diameter capture.
• Ensure the following data sources are available: `sourcetype="stream:sip"`, `sourcetype="diameter:cap"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Whitelist health-check sources; coordinate with peer ops when storm targets upstream interconnect.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=signaling (sourcetype="stream:sip" OR sourcetype="diameter:cap")
| bin _time span=1m
| stats count by method, cmd_code, _time
| eventstats avg(count) as mu, stdev(count) as s by method
| where count > mu+5*s
| sort -count
```

Understanding this SPL

**Signaling Storm Detection** — Bursts of SIP OPTIONS, REGISTER, or diameter requests can indicate reflection DDoS or misconfigured endpoints — complements UC-5.10.5 with cross-layer view.

Documented **Data sources**: `sourcetype="stream:sip"`, `sourcetype="diameter:cap"`. **App/TA** (typical add-on context): Splunk App for Stream, STP/Diameter capture. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: signaling; **sourcetype**: stream:sip, diameter:cap. Those sourcetypes align with what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=signaling, sourcetype="stream:sip". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by method, cmd_code, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eventstats` rolls up events into metrics; results are split **by method** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > mu+5*s` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (spike detection), Table (method × source ASN), Single value (peak RPS).

## SPL

```spl
index=signaling (sourcetype="stream:sip" OR sourcetype="diameter:cap")
| bin _time span=1m
| stats count by method, cmd_code, _time
| eventstats avg(count) as mu, stdev(count) as s by method
| where count > mu+5*s
| sort -count
```

## Visualization

Timeline (spike detection), Table (method × source ASN), Single value (peak RPS).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
