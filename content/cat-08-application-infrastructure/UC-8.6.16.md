<!-- AUTO-GENERATED from UC-8.6.16.json — DO NOT EDIT -->

---
id: "8.6.16"
title: "NTP Stratum Drift"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.6.16 · NTP Stratum Drift

## Description

Stratum jumps or large offset indicate bad upstream clock or local drift — affects Kerberos, TLS, and distributed logs.

## Value

Stratum jumps or large offset indicate bad upstream clock or local drift — affects Kerberos, TLS, and distributed logs.

## Implementation

Poll `chronyc tracking` or `ntpq -pn` every 5m. Alert when stratum >4 or |offset| >100ms sustained. Correlate with VM time sync settings.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`, `ntpq`/`chronyc` scripted input.
• Ensure the following data sources are available: `ntp:peer` `stratum`, `offset_ms`, `jitter_ms`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `chronyc tracking` or `ntpq -pn` every 5m. Alert when stratum >4 or |offset| >100ms sustained. Correlate with VM time sync settings.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype="ntp:peer"
| where stratum > 4 OR abs(offset_ms) > 100
| timechart span=5m max(stratum) as stratum, max(abs(offset_ms)) as abs_offset by host
```

Understanding this SPL

**NTP Stratum Drift** — Stratum jumps or large offset indicate bad upstream clock or local drift — affects Kerberos, TLS, and distributed logs.

Documented **Data sources**: `ntp:peer` `stratum`, `offset_ms`, `jitter_ms`. **App/TA** (typical add-on context): `Splunk_TA_nix`, `ntpq`/`chronyc` scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: ntp:peer. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype="ntp:peer". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where stratum > 4 OR abs(offset_ms) > 100` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.


Step 3 — Validate
Compare with the application or platform source of truth (logs, UI, or metrics) for the same time range, and with known change or maintenance windows.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (offset and stratum), Table (hosts with bad clock), Single value (max |offset|).

## SPL

```spl
index=os sourcetype="ntp:peer"
| where stratum > 4 OR abs(offset_ms) > 100
| timechart span=5m max(stratum) as stratum, max(abs(offset_ms)) as abs_offset by host
```

## Visualization

Line chart (offset and stratum), Table (hosts with bad clock), Single value (max |offset|).

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
