<!-- AUTO-GENERATED from UC-5.8.3.json — DO NOT EDIT -->

---
id: "5.8.3"
title: "SNMP Trap Consolidation"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.8.3 · SNMP Trap Consolidation

## Description

Centralizing SNMP traps from all sources enables cross-tool correlation and reduces monitoring tool sprawl.

## Value

Centralizing SNMP traps from all sources enables cross-tool correlation and reduces monitoring tool sprawl.

## Implementation

Configure Splunk SNMP trap receiver (UDP 162). Map trap OIDs to human-readable names via lookup. Correlate with syslog events from the same device.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for SNMP (trap receiver).
• Ensure the following data sources are available: SNMP traps.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Splunk SNMP trap receiver (UDP 162). Map trap OIDs to human-readable names via lookup. Correlate with syslog events from the same device.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="snmp:trap"
| stats count by trap_oid, host, severity | sort -count
```

Understanding this SPL

**SNMP Trap Consolidation** — Centralizing SNMP traps from all sources enables cross-tool correlation and reduces monitoring tool sprawl.

Documented **Data sources**: SNMP traps. **App/TA** (typical add-on context): Splunk Add-on for SNMP (trap receiver). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: snmp:trap. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="snmp:trap". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by trap_oid, host, severity** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
On Infoblox Grid Manager (or reporting export), run the same query window for the event type; confirm log forwarding or API batch jobs are not throttling, and that Splunk’s time zone matches the grid.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (device, trap, severity), Bar chart, Timeline.

## SPL

```spl
index=network sourcetype="snmp:trap"
| stats count by trap_oid, host, severity | sort -count
```

## Visualization

Table (device, trap, severity), Bar chart, Timeline.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
