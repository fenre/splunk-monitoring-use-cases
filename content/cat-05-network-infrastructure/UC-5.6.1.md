---
id: "5.6.1"
title: "DNS Query Volume Trending"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.6.1 · DNS Query Volume Trending

## Description

DNS query volume trending supports capacity planning and reveals traffic pattern changes.

## Value

DNS query volume trending supports capacity planning and reveals traffic pattern changes.

## Implementation

Forward DNS query logs. For Windows DNS: enable analytical logging. For Infoblox: configure syslog output. Track queries per second over time.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk_TA_infoblox, Splunk_TA_windows (DNS logs), Pi-hole syslog.
• Ensure the following data sources are available: `sourcetype=infoblox:dns`, `sourcetype=MSAD:NT6:DNS`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward DNS query logs. For Windows DNS: enable analytical logging. For Infoblox: configure syslog output. Track queries per second over time.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=dns sourcetype="infoblox:dns" OR sourcetype="MSAD:NT6:DNS"
| timechart span=5m count as qps
```

Understanding this SPL

**DNS Query Volume Trending** — DNS query volume trending supports capacity planning and reveals traffic pattern changes.

Documented **Data sources**: `sourcetype=infoblox:dns`, `sourcetype=MSAD:NT6:DNS`. **App/TA** (typical add-on context): Splunk_TA_infoblox, Splunk_TA_windows (DNS logs), Pi-hole syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: dns; **sourcetype**: infoblox:dns, MSAD:NT6:DNS. Those sourcetypes align with what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=dns, sourcetype="infoblox:dns". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets — ideal for trending and alerting on this use case.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Network_Resolution.DNS
  by DNS.src DNS.query DNS.record_type span=5m
| sort -count
```

Understanding this CIM / accelerated SPL

**DNS Query Volume Trending** — DNS query volume trending supports capacity planning and reveals traffic pattern changes.

Documented **Data sources**: `sourcetype=infoblox:dns`, `sourcetype=MSAD:NT6:DNS`. **App/TA** (typical add-on context): Splunk_TA_infoblox, Splunk_TA_windows (DNS logs), Pi-hole syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Network_Resolution.DNS` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (QPS over time), Single value (current QPS), Table.

## SPL

```spl
index=dns sourcetype="infoblox:dns" OR sourcetype="MSAD:NT6:DNS"
| timechart span=5m count as qps
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Resolution.DNS
  by DNS.src DNS.query DNS.record_type span=5m
| sort -count
```

## Visualization

Line chart (QPS over time), Single value (current QPS), Table.

## References

- [CIM: Network_Resolution](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Resolution)
