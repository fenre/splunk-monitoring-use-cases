---
id: "5.1.60"
title: "Arista MLAG Health and Consistency (Arista)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.1.60 · Arista MLAG Health and Consistency (Arista)

## Description

MLAG pairs depend on matching configuration and a healthy peer link; inconsistency or peer loss can lead to blackholed VLANs or asymmetric forwarding while both switches appear “up.” Catching `config-sanity` failures and peer state changes early prevents subtle application outages that load balancers and servers cannot retry away from. Splunk correlation across both peers speeds root cause when only one side logs the fault.

## Value

MLAG pairs depend on matching configuration and a healthy peer link; inconsistency or peer loss can lead to blackholed VLANs or asymmetric forwarding while both switches appear “up.” Catching `config-sanity` failures and peer state changes early prevents subtle application outages that load balancers and servers cannot retry away from. Splunk correlation across both peers speeds root cause when only one side logs the fault.

## Implementation

Ingest syslog from both MLAG peers with synchronized clocks. Alert on peer-link down, partial connectivity, or config-sanity failure strings present in your EOS version. Use a lookup pairing `mlag_domain` or neighbor hostname to open one incident for the pair. Validate against `show mlag` snapshots if you periodically scrape CLI into Splunk.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `arista:eos` via SC4S, syslog.
• Ensure the following data sources are available: `sourcetype=arista:eos`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest syslog from both MLAG peers with synchronized clocks. Alert on peer-link down, partial connectivity, or config-sanity failure strings present in your EOS version. Use a lookup pairing `mlag_domain` or neighbor hostname to open one incident for the pair. Validate against `show mlag` snapshots if you periodically scrape CLI into Splunk.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="arista:eos"
| search Mlag OR MLAG OR mlag OR "Mlag:" OR "Dual attached" OR "peer-link" OR "inactive"
| rex field=_raw "(?i)Mlag:\s*(?<mlag_msg>[^\n]+)"
| stats count as mlag_events, latest(mlag_msg) as last_summary, values(_raw) as samples by host
| sort -mlag_events
```

Understanding this SPL

**Arista MLAG Health and Consistency (Arista)** — MLAG pairs depend on matching configuration and a healthy peer link; inconsistency or peer loss can lead to blackholed VLANs or asymmetric forwarding while both switches appear “up.” Catching `config-sanity` failures and peer state changes early prevents subtle application outages that load balancers and servers cannot retry away from. Splunk correlation across both peers speeds root cause when only one side logs the fault.

Documented **Data sources**: `sourcetype=arista:eos`. **App/TA** (typical add-on context): `arista:eos` via SC4S, syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: arista:eos. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="arista:eos". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Extracts fields with `rex` (regular expression).
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: MLAG peer pair dashboard; red/amber status per domain; timeline of state transitions.

## SPL

```spl
index=network sourcetype="arista:eos"
| search Mlag OR MLAG OR mlag OR "Mlag:" OR "Dual attached" OR "peer-link" OR "inactive"
| rex field=_raw "(?i)Mlag:\s*(?<mlag_msg>[^\n]+)"
| stats count as mlag_events, latest(mlag_msg) as last_summary, values(_raw) as samples by host
| sort -mlag_events
```

## Visualization

MLAG peer pair dashboard; red/amber status per domain; timeline of state transitions.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
