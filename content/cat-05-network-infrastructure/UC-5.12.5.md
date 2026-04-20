---
id: "5.12.5"
title: "VoIP MOS Score Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.12.5 · VoIP MOS Score Monitoring

## Description

Mean Opinion Score (or derived R-factor) from RTCP XR or vendor QoE reports — user-perceived VoLTE/VoIP quality.

## Value

Mean Opinion Score (or derived R-factor) from RTCP XR or vendor QoE reports — user-perceived VoLTE/VoIP quality.

## Implementation

ITU-T G.107 E-model targets; correlate with jitter/loss from same leg_id; segment by radio access (VoLTE) vs. Wi-Fi.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: SBC QoE records, Poly/Vendor QoS feeds.
• Ensure the following data sources are available: `sourcetype="qos:rtcp"`, `sourcetype="cdr:voip"` with `mos` field.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
ITU-T G.107 E-model targets; correlate with jitter/loss from same leg_id; segment by radio access (VoLTE) vs. Wi-Fi.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=voip (sourcetype="qos:rtcp" OR sourcetype="cdr:voip")
| where isnotnull(mos)
| timechart span=5m avg(mos) as avg_mos perc5(mos) as worst_mos by codec
| where avg_mos < 3.8 OR worst_mos < 3.0
```

Understanding this SPL

**VoIP MOS Score Monitoring** — Mean Opinion Score (or derived R-factor) from RTCP XR or vendor QoE reports — user-perceived VoLTE/VoIP quality.

Documented **Data sources**: `sourcetype="qos:rtcp"`, `sourcetype="cdr:voip"` with `mos` field. **App/TA** (typical add-on context): SBC QoE records, Poly/Vendor QoS feeds. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: voip; **sourcetype**: qos:rtcp, cdr:voip. Those sourcetypes align with what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=voip, sourcetype="qos:rtcp". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where isnotnull(mos)` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by codec** — ideal for trending and alerting on this use case.
• Filters the current rows with `where avg_mos < 3.8 OR worst_mos < 3.0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (MOS trend), Scatter (loss vs. MOS), Table (worst calls).

## SPL

```spl
index=voip (sourcetype="qos:rtcp" OR sourcetype="cdr:voip")
| where isnotnull(mos)
| timechart span=5m avg(mos) as avg_mos perc5(mos) as worst_mos by codec
| where avg_mos < 3.8 OR worst_mos < 3.0
```

## Visualization

Line chart (MOS trend), Scatter (loss vs. MOS), Table (worst calls).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
