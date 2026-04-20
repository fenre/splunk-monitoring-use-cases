---
id: "5.1.58"
title: "Junos Routing Engine Failover Monitoring (Juniper)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.1.58 · Junos Routing Engine Failover Monitoring (Juniper)

## Description

Platforms with dual routing engines rely on GRES and related state transfer; an unplanned mastership change usually means primary RE failure, kernel panic, or loss of control-plane stability. Repeated failovers on the same chassis point to degrading hardware or software defects before a hard outage. Tracking these events in Splunk gives operations a single place to justify RMA, software upgrade, or emergency maintenance.

## Value

Platforms with dual routing engines rely on GRES and related state transfer; an unplanned mastership change usually means primary RE failure, kernel panic, or loss of control-plane stability. Repeated failovers on the same chassis point to degrading hardware or software defects before a hard outage. Tracking these events in Splunk gives operations a single place to justify RMA, software upgrade, or emergency maintenance.

## Implementation

Classify planned vs unplanned using maintenance windows or SNMP/CLI context if ingested. Critical alert on any mastership change outside a change window; warning if more than one event per chassis per 7 days. Attach device role (PE, core, aggregation) for prioritization.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_juniper`, syslog.
• Ensure the following data sources are available: `sourcetype=juniper:junos:structured`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Classify planned vs unplanned using maintenance windows or SNMP/CLI context if ingested. Critical alert on any mastership change outside a change window; warning if more than one event per chassis per 7 days. Attach device role (PE, core, aggregation) for prioritization.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="juniper:junos:structured"
| search SERD_MASTERSHIP OR RE_SWITCHOVER OR "mastership" OR "Routing Engine.*switch" OR "Become master"
| rex field=_raw "(?i)from\s+(?<old_role>\w+)\s+to\s+(?<new_role>\w+)"
| bin span=24h _time
| stats count as failover_events, values(_raw) as samples by host, _time
| where failover_events > 0
| sort -failover_events
```

Understanding this SPL

**Junos Routing Engine Failover Monitoring (Juniper)** — Platforms with dual routing engines rely on GRES and related state transfer; an unplanned mastership change usually means primary RE failure, kernel panic, or loss of control-plane stability. Repeated failovers on the same chassis point to degrading hardware or software defects before a hard outage. Tracking these events in Splunk gives operations a single place to justify RMA, software upgrade, or emergency maintenance.

Documented **Data sources**: `sourcetype=juniper:junos:structured`. **App/TA** (typical add-on context): `Splunk_TA_juniper`, syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: juniper:junos:structured. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="juniper:junos:structured". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Extracts fields with `rex` (regular expression).
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by host, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where failover_events > 0` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Failover timeline per chassis; count of failovers per device last 30 days; list of recent raw messages for triage.

## SPL

```spl
index=network sourcetype="juniper:junos:structured"
| search SERD_MASTERSHIP OR RE_SWITCHOVER OR "mastership" OR "Routing Engine.*switch" OR "Become master"
| rex field=_raw "(?i)from\s+(?<old_role>\w+)\s+to\s+(?<new_role>\w+)"
| bin span=24h _time
| stats count as failover_events, values(_raw) as samples by host, _time
| where failover_events > 0
| sort -failover_events
```

## Visualization

Failover timeline per chassis; count of failovers per device last 30 days; list of recent raw messages for triage.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
