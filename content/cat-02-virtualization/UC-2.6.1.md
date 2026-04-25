<!-- AUTO-GENERATED from UC-2.6.1.json — DO NOT EDIT -->

---
id: "2.6.1"
title: "Citrix Session Logon Duration Breakdown"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-2.6.1 · Citrix Session Logon Duration Breakdown

## Description

Slow Citrix logon times are the most common user complaint in CVAD environments. Logon duration is composed of multiple sequential phases — brokering, VM start, HDX connection, authentication, profile load, GPO processing, and script execution. Identifying which phase contributes to slow logons enables targeted remediation rather than broad troubleshooting. A 60-second logon target is typical; exceeding it degrades user satisfaction and productivity.

## Value

Slow Citrix logon times are the most common user complaint in CVAD environments. Logon duration is composed of multiple sequential phases — brokering, VM start, HDX connection, authentication, profile load, GPO processing, and script execution. Identifying which phase contributes to slow logons enables targeted remediation rather than broad troubleshooting. A 60-second logon target is typical; exceeding it degrades user satisfaction and productivity.

## Implementation

**Preferred:** Deploy uberAgent UXM on VDAs — the Logon Duration dashboard provides automatic phase breakdown (userinit, shell, GPO, profile, scripts) with no OData polling required, and captures per-user detail. **Alternative:** Collect session logon events from the Citrix Broker Service event log on Delivery Controllers using the `TA-XD7-Broker` add-on, or poll the Monitor Service OData API endpoint `Sessions` for `LogOnDuration` breakdown. Alert when p95 logon exceeds 60 seconds for any delivery group. Trend logon duration over weeks to detect gradual regression after GPO or profile changes. Segment by delivery group to isolate problem areas. Common root causes by phase: brokering (controller load), VM start (hypervisor contention), profile load (large profiles or slow file shares), GPO (excessive policies).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: uberAgent UXM (Splunkbase 1448) — recommended; or Template for Citrix XenDesktop 7 (`TA-XD7-Broker`), Citrix Monitor Service OData API.
• Ensure the following data sources are available: uberAgent: `sourcetype="uberAgent:Logon:LogonDetail"` (phase-level breakdown including GPO, profile, shell, scripts); or `index=xd` `sourcetype="citrix:broker:events"` fields `logon_duration_ms`, `brokering_duration_ms`, `vm_start_duration_ms`, `hdx_connection_ms`, `authentication_ms`, `profile_load_ms`, `gpo_ms`, `logon_scripts_ms`, `user`, `delivery_group`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
**Preferred:** Deploy uberAgent UXM on VDAs — the Logon Duration dashboard provides automatic phase breakdown (userinit, shell, GPO, profile, scripts) with no OData polling required, and captures per-user detail. **Alternative:** Collect session logon events from the Citrix Broker Service event log on Delivery Controllers using the `TA-XD7-Broker` add-on, or poll the Monitor Service OData API endpoint `Sessions` for `LogOnDuration` breakdown. Alert when p95 logon exceeds 60 seconds for any deliv…

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=xd sourcetype="citrix:broker:events" event_type="SessionLogon"
| eval total_logon_sec=logon_duration_ms/1000
| bin _time span=1h
| stats avg(total_logon_sec) as avg_logon, perc95(total_logon_sec) as p95_logon,
  avg(brokering_duration_ms) as avg_broker, avg(vm_start_duration_ms) as avg_vmstart,
  avg(hdx_connection_ms) as avg_hdx, avg(profile_load_ms) as avg_profile,
  avg(gpo_ms) as avg_gpo, count as logon_count by delivery_group, _time
| where p95_logon > 60
| table _time, delivery_group, logon_count, avg_logon, p95_logon, avg_broker, avg_vmstart, avg_hdx, avg_profile, avg_gpo
```

Understanding this SPL

**Citrix Session Logon Duration Breakdown** — Slow Citrix logon times are the most common user complaint in CVAD environments. Logon duration is composed of multiple sequential phases — brokering, VM start, HDX connection, authentication, profile load, GPO processing, and script execution. Identifying which phase contributes to slow logons enables targeted remediation rather than broad troubleshooting. A 60-second logon target is typical; exceeding it degrades user satisfaction and productivity.

Documented **Data sources**: uberAgent: `sourcetype="uberAgent:Logon:LogonDetail"` (phase-level breakdown including GPO, profile, shell, scripts); or `index=xd` `sourcetype="citrix:broker:events"` fields `logon_duration_ms`, `brokering_duration_ms`, `vm_start_duration_ms`, `hdx_connection_ms`, `authentication_ms`, `profile_load_ms`, `gpo_ms`, `logon_scripts_ms`, `user`, `delivery_group`. **App/TA** (typical add-on context): uberAgent UXM (Splunkbase 1448) — recommended; or Template for Citrix XenDesktop 7 (`TA-XD7-Broker`), Citrix Monitor Service OData API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: xd; **sourcetype**: citrix:broker:events. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=xd, sourcetype="citrix:broker:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **total_logon_sec** — often to normalize units, derive a ratio, or prepare for thresholds.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by delivery_group, _time** so each row reflects one combination of those dimensions.
• Filters the current rows with `where p95_logon > 60` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Citrix Session Logon Duration Breakdown**): table _time, delivery_group, logon_count, avg_logon, p95_logon, avg_broker, avg_vmstart, avg_hdx, avg_profile, avg_gpo

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Stacked bar chart (logon phases), Line chart (logon duration trending), Table (slowest delivery groups).

## SPL

```spl
index=xd sourcetype="citrix:broker:events" event_type="SessionLogon"
| eval total_logon_sec=logon_duration_ms/1000
| bin _time span=1h
| stats avg(total_logon_sec) as avg_logon, perc95(total_logon_sec) as p95_logon,
  avg(brokering_duration_ms) as avg_broker, avg(vm_start_duration_ms) as avg_vmstart,
  avg(hdx_connection_ms) as avg_hdx, avg(profile_load_ms) as avg_profile,
  avg(gpo_ms) as avg_gpo, count as logon_count by delivery_group, _time
| where p95_logon > 60
| table _time, delivery_group, logon_count, avg_logon, p95_logon, avg_broker, avg_vmstart, avg_hdx, avg_profile, avg_gpo
```

## Visualization

Stacked bar chart (logon phases), Line chart (logon duration trending), Table (slowest delivery groups).

## References

- [uberAgent UXM](https://splunkbase.splunk.com/app/1448)
