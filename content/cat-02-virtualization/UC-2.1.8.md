<!-- AUTO-GENERATED from UC-2.1.8.json — DO NOT EDIT -->

---
id: "2.1.8"
title: "DRS Imbalance Detection"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.1.8 · DRS Imbalance Detection

## Description

DRS should keep clusters balanced. Frequent or failed DRS recommendations indicate resource constraints, affinity rule conflicts, or misconfiguration.

## Value

DRS should keep clusters balanced. Frequent or failed DRS recommendations indicate resource constraints, affinity rule conflicts, or misconfiguration.

## Implementation

Monitor DRS migration frequency. High migration counts suggest oscillation. Also check for unapplied DRS recommendations (DRS set to manual mode). Correlate with CPU/memory utilization per host.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`.
• Ensure the following data sources are available: `sourcetype=vmware:events`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor DRS migration frequency. High migration counts suggest oscillation. Also check for unapplied DRS recommendations (DRS set to manual mode). Correlate with CPU/memory utilization per host.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:events" event_type="DrsVmMigratedEvent"
| bin _time span=1h
| stats count by _time, cluster
| where count > 20
```

Understanding this SPL

**DRS Imbalance Detection** — DRS should keep clusters balanced. Frequent or failed DRS recommendations indicate resource constraints, affinity rule conflicts, or misconfiguration.

Documented **Data sources**: `sourcetype=vmware:events`. **App/TA** (typical add-on context): `Splunk_TA_vmware`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:events. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by _time, cluster** so each row reflects one combination of those dimensions.
• Filters the current rows with `where count > 20` — typically the threshold or rule expression for this monitoring goal.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (migrations per hour), Table of DRS events, Cluster balance comparison chart.

## SPL

```spl
index=vmware sourcetype="vmware:events" event_type="DrsVmMigratedEvent"
| bin _time span=1h
| stats count by _time, cluster
| where count > 20
```

## Visualization

Line chart (migrations per hour), Table of DRS events, Cluster balance comparison chart.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
