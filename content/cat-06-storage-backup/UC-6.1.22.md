---
id: "6.1.22"
title: "Fibre Channel Port Error Rate (Array)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.22 · Fibre Channel Port Error Rate (Array)

## Description

Array-side FC port CRCs, signal loss, and link failures differ from switch-only views. Port error rate trending isolates HBA/cable issues at the storage attachment point.

## Value

Array-side FC port CRCs, signal loss, and link failures differ from switch-only views. Port error rate trending isolates HBA/cable issues at the storage attachment point.

## Implementation

Poll FC port counters per array port every 15m. Baseline error rate; alert on non-zero sustained errors or step changes after maintenance.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Vendor TA, SNMP FC port MIB.
• Ensure the following data sources are available: Array FC port statistics (CRC, enc_in, enc_out, link_fail).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll FC port counters per array port every 15m. Baseline error rate; alert on non-zero sustained errors or step changes after maintenance.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=storage sourcetype="storage:fc_port"
| eval err_rate=crc_errors + link_failures + signal_loss
| timechart span=15m sum(err_rate) as errors by array_name, port_id
| where errors > 0
```

Understanding this SPL

**Fibre Channel Port Error Rate (Array)** — Array-side FC port CRCs, signal loss, and link failures differ from switch-only views. Port error rate trending isolates HBA/cable issues at the storage attachment point.

Documented **Data sources**: Array FC port statistics (CRC, enc_in, enc_out, link_fail). **App/TA** (typical add-on context): Vendor TA, SNMP FC port MIB. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: storage; **sourcetype**: storage:fc_port. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=storage, sourcetype="storage:fc_port". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **err_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=15m** buckets with a separate series **by array_name, port_id** — ideal for trending and alerting on this use case.
• Filters the current rows with `where errors > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (errors by port), Line chart (error rate trend), Table (ports with errors).

## SPL

```spl
index=storage sourcetype="storage:fc_port"
| eval err_rate=crc_errors + link_failures + signal_loss
| timechart span=15m sum(err_rate) as errors by array_name, port_id
| where errors > 0
```

## Visualization

Bar chart (errors by port), Line chart (error rate trend), Table (ports with errors).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
