<!-- AUTO-GENERATED from UC-1.2.73.json — DO NOT EDIT -->

---
id: "1.2.73"
title: "LDAP Query Performance (DC Health)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.2.73 · LDAP Query Performance (DC Health)

## Description

Slow LDAP queries on domain controllers degrade authentication, group policy processing, and application lookups across the entire domain.

## Value

When domain controllers bog down on LDAP, logons and policy updates slow for everyone. Trending NTDS counters early helps capacity planning and catches attacks that hammer the directory.

## Implementation

Configure Perfmon inputs on domain controllers for NTDS object: `LDAP Searches/sec`, `LDAP Successful Binds/sec`, `LDAP Client Sessions`, `LDAP Active Threads` (interval=60). Also enable "Expensive/Inefficient LDAP searches" logging via registry (15 Field Engineering diagnostics). Alert when LDAP search rate drops suddenly (DC issues) or when client sessions exceed baseline by 2x (possible LDAP enumeration attack).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=Perfmon:NTDS` (counters: LDAP Searches/sec, LDAP Successful Binds/sec, LDAP Search Time).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
On each domain controller, add a `perfmon` input in `inputs.conf` for the **NTDS** object with counters at minimum: `LDAP Searches/sec`, `LDAP Successful Binds/sec`, `LDAP Client Sessions` (and optionally `LDAP Active Threads`, `LDAP UDP operations/sec`). Set `interval=60`, `sourcetype=Perfmon:NTDS` (or your normalized name), and route to a perf-capacity index. Enable Windows "Expensive/Inefficient LDAP searches" diagnostic logging if you need query-level forensics. Alert when search rate falls versus baseline (service stress) or when `LDAP Client Sessions` doubles versus normal (possible enumeration) using the primary SPL above.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=perfmon sourcetype="Perfmon:NTDS" counter IN ("LDAP Searches/sec","LDAP Successful Binds/sec","LDAP Client Sessions")
| timechart span=5m avg(Value) as value by counter, host
```

Understanding this SPL

**LDAP Query Performance (DC Health)** — Slow LDAP queries on domain controllers degrade authentication, group policy processing, and application lookups across the entire domain.

Documented **Data sources**: `sourcetype=Perfmon:NTDS` (counters: LDAP Searches/sec, LDAP Successful Binds/sec, LDAP Search Time). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: perfmon; **sourcetype**: Perfmon:NTDS. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=perfmon, sourcetype="Perfmon:NTDS". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by counter, host** — ideal for trending and alerting on this use case.

Optional CIM / accelerated related view (no CIM field for `LDAP Searches/sec`; use DC CPU as a coarse correlate):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as cpu
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| where cpu > 85
```

Enable **data model acceleration** on `Performance` (CPU). For LDAP-specific thresholds, keep the `Perfmon:NTDS` search in Step 2 as the source of truth.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (LDAP operations/sec), Dual-axis (searches + bind rate), Table (DCs by load), Gauge (active sessions).

## SPL

```spl
index=perfmon sourcetype="Perfmon:NTDS" counter IN ("LDAP Searches/sec","LDAP Successful Binds/sec","LDAP Client Sessions")
| timechart span=5m avg(Value) as value by counter, host
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as cpu
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| where cpu > 85
```

## Visualization

Line chart (LDAP operations/sec), Dual-axis (searches + bind rate), Table (DCs by load), Gauge (active sessions).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
