<!-- AUTO-GENERATED from UC-5.10.5.json — DO NOT EDIT -->

---
id: "5.10.5"
title: "SIP Registration Storm Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.10.5 · SIP Registration Storm Detection

## Description

Detects sudden spikes in SIP REGISTER messages that can overwhelm IMS/SBC infrastructure — caused by mass device reboots, network flaps, or DDoS attacks. Early detection prevents cascading core failures.

## Value

Detects sudden spikes in SIP REGISTER messages that can overwhelm IMS/SBC infrastructure — caused by mass device reboots, network flaps, or DDoS attacks. Early detection prevents cascading core failures.

## Implementation

Configure Splunk App for Stream to capture SIP REGISTER traffic on the IMS/SBC interfaces. Use a 5-minute time bucket for aggregation. Calculate a rolling baseline using `eventstats` and flag any bucket where REGISTER volume exceeds 3 standard deviations above the mean. The `dc(src)` field helps distinguish between a mass re-registration event (many unique sources) vs. a single device stuck in a registration loop (few unique sources, high count). Alert the NOC immediately as registration storms can cascade into full core outages within minutes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk App for Stream` (Splunkbase #1809).
• Ensure the following data sources are available: `sourcetype=stream:sip`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Splunk App for Stream to capture SIP REGISTER traffic on the IMS/SBC interfaces. Use a 5-minute time bucket for aggregation. Calculate a rolling baseline using `eventstats` and flag any bucket where REGISTER volume exceeds 3 standard deviations above the mean. The `dc(src)` field helps distinguish between a mass re-registration event (many unique sources) vs. a single device stuck in a registration loop (few unique sources, high count). Alert the NOC immediately as registration storms …

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
sourcetype="stream:sip" method="REGISTER"
| bin _time span=5m
| stats count as register_count, dc(src) as unique_sources by _time
| eventstats avg(register_count) as baseline, stdev(register_count) as stdev_reg
| eval threshold=baseline+(3*stdev_reg)
| where register_count>threshold
| eval spike_factor=round(register_count/baseline, 1)
```

Understanding this SPL

**SIP Registration Storm Detection** — Detects sudden spikes in SIP REGISTER messages that can overwhelm IMS/SBC infrastructure — caused by mass device reboots, network flaps, or DDoS attacks. Early detection prevents cascading core failures.

Documented **Data sources**: `sourcetype=stream:sip`. **App/TA** (typical add-on context): `Splunk App for Stream` (Splunkbase #1809). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **sourcetype**: stream:sip. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: sourcetype="stream:sip". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by _time** so each row reflects one combination of those dimensions.
• `eventstats` aggregates the pipeline (counts, distinct values, sums, percentiles, etc.) into fewer rows.
• `eval` defines or adjusts **threshold** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where register_count>threshold` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **spike_factor** — often to normalize units, derive a ratio, or prepare for thresholds.
Step 3 — Validate
Compare Splunk counts in the same time window to your packet capture or Stream job scope (VLAN, SPAN, or tap). On the core element (PCRF, SBC, or PGW) console or EMS, open the matching subscriber or trunk counters and confirm codes such as Diameter `result_code` or SIP `reply_code` line up. After any network or mirror change, re-check that the Stream capture still includes the trunks you care about.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (REGISTER count over time with dynamic baseline threshold line), Single value (current spike factor vs. baseline), Table (time bucket, register_count, unique_sources, baseline, threshold — highlighting rows above threshold), Area chart (unique sources over time to correlate with storms).

## SPL

```spl
sourcetype="stream:sip" method="REGISTER"
| bin _time span=5m
| stats count as register_count, dc(src) as unique_sources by _time
| eventstats avg(register_count) as baseline, stdev(register_count) as stdev_reg
| eval threshold=baseline+(3*stdev_reg)
| where register_count>threshold
| eval spike_factor=round(register_count/baseline, 1)
```

## Visualization

Line chart (REGISTER count over time with dynamic baseline threshold line), Single value (current spike factor vs. baseline), Table (time bucket, register_count, unique_sources, baseline, threshold — highlighting rows above threshold), Area chart (unique sources over time to correlate with storms).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
