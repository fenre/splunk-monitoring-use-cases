---
id: "5.4.11"
title: "Band Steering Effectiveness"
criticality: "low"
splunkPillar: "Observability"
---

# UC-5.4.11 · Band Steering Effectiveness

## Description

Band steering moves capable clients to 5 GHz, reducing congestion on 2.4 GHz. Measuring effectiveness validates RF policy.

## Value

Band steering moves capable clients to 5 GHz, reducing congestion on 2.4 GHz. Measuring effectiveness validates RF policy.

## Implementation

Collect client association events with channel info. Calculate the ratio of 5 GHz vs 2.4 GHz clients per SSID. Target >70% on 5 GHz for dual-band capable clients.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Cisco WLC syslog, Meraki API.
• Ensure the following data sources are available: `sourcetype=cisco:wlc`, `sourcetype=meraki:api`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect client association events with channel info. Calculate the ratio of 5 GHz vs 2.4 GHz clients per SSID. Target >70% on 5 GHz for dual-band capable clients.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="cisco:wlc" "associated"
| eval band=if(match(channel,"^(1|6|11)$"),"2.4GHz","5GHz")
| stats count by band, ssid
| eventstats sum(count) as total by ssid
| eval pct=round(count/total*100,1)
```

Understanding this SPL

**Band Steering Effectiveness** — Band steering moves capable clients to 5 GHz, reducing congestion on 2.4 GHz. Measuring effectiveness validates RF policy.

Documented **Data sources**: `sourcetype=cisco:wlc`, `sourcetype=meraki:api`. **App/TA** (typical add-on context): Cisco WLC syslog, Meraki API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: cisco:wlc. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="cisco:wlc". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **band** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by band, ssid** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eventstats` rolls up events into metrics; results are split **by ssid** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **pct** — often to normalize units, derive a ratio, or prepare for thresholds.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Pie chart (band distribution), Bar chart (by SSID), Timechart (trending).

## SPL

```spl
index=network sourcetype="cisco:wlc" "associated"
| eval band=if(match(channel,"^(1|6|11)$"),"2.4GHz","5GHz")
| stats count by band, ssid
| eventstats sum(count) as total by ssid
| eval pct=round(count/total*100,1)
```

## Visualization

Pie chart (band distribution), Bar chart (by SSID), Timechart (trending).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
