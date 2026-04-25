<!-- AUTO-GENERATED from UC-5.12.4.json — DO NOT EDIT -->

---
id: "5.12.4"
title: "SIP Trunk Utilization"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.12.4 · SIP Trunk Utilization

## Description

Concurrent session counts or peg counts vs. licensed trunk capacity — prevents preemptive blocking at peak.

## Value

Concurrent session counts or peg counts vs. licensed trunk capacity — prevents preemptive blocking at peak.

## Implementation

Separate inbound vs. outbound if asymmetric licensing; forecast with `predict` for capacity planning.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: SBC SNMP, CDR-derived concurrency, Stream SIP.
• Ensure the following data sources are available: `sourcetype="snmp:sbc"`, `sourcetype="stream:sip"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Separate inbound vs. outbound if asymmetric licensing; forecast with `predict` for capacity planning.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=voip sourcetype="stream:sip" OR sourcetype="snmp:sbc"
| eval concurrent=if(isnotnull(active_calls), active_calls, curr_sess)
| timechart span=1m max(concurrent) as peak_sess by trunk_group
| lookup trunk_capacity trunk_group OUTPUT licensed_sess
| eval util_pct=round(100*peak_sess/licensed_sess,1)
| where util_pct>85
```

Understanding this SPL

**SIP Trunk Utilization** — Concurrent session counts or peg counts vs. licensed trunk capacity — prevents preemptive blocking at peak.

Documented **Data sources**: `sourcetype="snmp:sbc"`, `sourcetype="stream:sip"`. **App/TA** (typical add-on context): SBC SNMP, CDR-derived concurrency, Stream SIP. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: voip; **sourcetype**: stream:sip, snmp:sbc. Those sourcetypes align with what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=voip, sourcetype="stream:sip". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **concurrent** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=1m** buckets with a separate series **by trunk_group** — ideal for trending and alerting on this use case.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• `eval` defines or adjusts **util_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where util_pct>85` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
For the same period, compare concurrent session counts from CDR/Stream to the SBC or carrier trunk-group utilization screen; align rounding (erlangs vs sessions) and one-way vs bidirectional trunks.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Area chart (concurrency), Gauge (utilization %), Table (trunk groups at risk).

## SPL

```spl
index=voip sourcetype="stream:sip" OR sourcetype="snmp:sbc"
| eval concurrent=if(isnotnull(active_calls), active_calls, curr_sess)
| timechart span=1m max(concurrent) as peak_sess by trunk_group
| lookup trunk_capacity trunk_group OUTPUT licensed_sess
| eval util_pct=round(100*peak_sess/licensed_sess,1)
| where util_pct>85
```

## Visualization

Area chart (concurrency), Gauge (utilization %), Table (trunk groups at risk).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
