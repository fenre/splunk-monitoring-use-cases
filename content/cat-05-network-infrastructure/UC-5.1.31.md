---
id: "5.1.31"
title: "QoS Policy Drops per Class"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.31 · QoS Policy Drops per Class

## Description

Traffic dropped per QoS class/queue on routers/switches.

## Value

Traffic dropped per QoS class/queue on routers/switches.

## Implementation

Poll CISCO-CLASS-BASED-QOS-MIB (cbQosCMDropPkt, cbQosCMPrePolicyPkt) per policy/class. Map OID to policy name via lookup. Alert when drop rate exceeds 5% for critical classes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: SNMP modular input (CISCO-CLASS-BASED-QOS-MIB), `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog.
• Ensure the following data sources are available: cbQosCMDropPkt, cbQosCMPrePolicyPkt.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll CISCO-CLASS-BASED-QOS-MIB (cbQosCMDropPkt, cbQosCMPrePolicyPkt) per policy/class. Map OID to policy name via lookup. Alert when drop rate exceeds 5% for critical classes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype=snmp:qos
| streamstats current=f last(cbQosCMDropPkt) as prev_drop, last(cbQosCMPrePolicyPkt) as prev_pre by host, cbQosConfigIndex, cbQosObjectsIndex
| eval drop_delta=cbQosCMDropPkt-coalesce(prev_drop,0), pre_delta=cbQosCMPrePolicyPkt-coalesce(prev_pre,0)
| eval drop_rate=round(drop_delta/(pre_delta+0.001)*100,2)
| where drop_delta > 0
| stats sum(drop_delta) as total_drops, sum(pre_delta) as total_pre by host, policy_class
| eval drop_pct=round(total_drops/(total_pre+0.001)*100,2)
| sort -total_drops
```

Understanding this SPL

**QoS Policy Drops per Class** — Traffic dropped per QoS class/queue on routers/switches.

Documented **Data sources**: cbQosCMDropPkt, cbQosCMPrePolicyPkt. **App/TA** (typical add-on context): SNMP modular input (CISCO-CLASS-BASED-QOS-MIB), `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: snmp:qos. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype=snmp:qos. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `streamstats` rolls up events into metrics; results are split **by host, cbQosConfigIndex, cbQosObjectsIndex** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **drop_delta** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **drop_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where drop_delta > 0` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by host, policy_class** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **drop_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (host, class, drops, rate), Bar chart, Line chart (drops over time).

## SPL

```spl
index=network sourcetype=snmp:qos
| streamstats current=f last(cbQosCMDropPkt) as prev_drop, last(cbQosCMPrePolicyPkt) as prev_pre by host, cbQosConfigIndex, cbQosObjectsIndex
| eval drop_delta=cbQosCMDropPkt-coalesce(prev_drop,0), pre_delta=cbQosCMPrePolicyPkt-coalesce(prev_pre,0)
| eval drop_rate=round(drop_delta/(pre_delta+0.001)*100,2)
| where drop_delta > 0
| stats sum(drop_delta) as total_drops, sum(pre_delta) as total_pre by host, policy_class
| eval drop_pct=round(total_drops/(total_pre+0.001)*100,2)
| sort -total_drops
```

## Visualization

Table (host, class, drops, rate), Bar chart, Line chart (drops over time).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
