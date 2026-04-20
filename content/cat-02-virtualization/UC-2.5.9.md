---
id: "2.5.9"
title: "IGEL Cloud Gateway Connection Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.5.9 · IGEL Cloud Gateway Connection Health

## Description

The IGEL Cloud Gateway (ICG) enables remote management of IGEL devices outside the corporate network — essential for work-from-home and branch office deployments. If ICG connectivity fails, remote devices cannot receive policy updates, firmware upgrades, or administrative commands, creating a management blind spot. Monitoring ICG health from both the UMS and ICG perspectives ensures continuous remote device manageability.

## Value

The IGEL Cloud Gateway (ICG) enables remote management of IGEL devices outside the corporate network — essential for work-from-home and branch office deployments. If ICG connectivity fails, remote devices cannot receive policy updates, firmware upgrades, or administrative commands, creating a management blind spot. Monitoring ICG health from both the UMS and ICG perspectives ensures continuous remote device manageability.

## Implementation

Deploy a Splunk Universal Forwarder on the ICG server to monitor `/opt/IGEL/icg/usg/logs/icg-security.log`. The ICG security log records authentication events (success/failure), user creation/deletion, and file uploads. Also monitor the UMS check-status endpoint for ICG-related warnings (cloud gateway disconnection). Alert on: sustained authentication failures from ICG (possible certificate mismatch), ICG going offline (no events for 15+ minutes), or UMS reporting ICG disconnection in its health status.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Universal Forwarder monitoring ICG security log, custom scripted input for UMS health.
• Ensure the following data sources are available: `index=endpoint` `sourcetype="igel:icg:security"` fields `event_type`, `user`, `result`, `source_ip`; `sourcetype="igel:ums:health"` for ICG connection warnings.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy a Splunk Universal Forwarder on the ICG server to monitor `/opt/IGEL/icg/usg/logs/icg-security.log`. The ICG security log records authentication events (success/failure), user creation/deletion, and file uploads. Also monitor the UMS check-status endpoint for ICG-related warnings (cloud gateway disconnection). Alert on: sustained authentication failures from ICG (possible certificate mismatch), ICG going offline (no events for 15+ minutes), or UMS reporting ICG disconnection in its health…

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=endpoint sourcetype="igel:icg:security"
| bin _time span=15m
| stats count as total_events,
  sum(eval(if(match(event_type, "(?i)auth.*fail"), 1, 0))) as failed_auth,
  sum(eval(if(match(event_type, "(?i)auth.*success"), 1, 0))) as success_auth,
  dc(source_ip) as unique_sources by _time
| eval fail_pct=if(total_events>0, round(failed_auth/total_events*100,1), 0)
| where failed_auth > 5 OR fail_pct > 20
| table _time, total_events, success_auth, failed_auth, fail_pct, unique_sources
```

Understanding this SPL

**IGEL Cloud Gateway Connection Health** — The IGEL Cloud Gateway (ICG) enables remote management of IGEL devices outside the corporate network — essential for work-from-home and branch office deployments. If ICG connectivity fails, remote devices cannot receive policy updates, firmware upgrades, or administrative commands, creating a management blind spot. Monitoring ICG health from both the UMS and ICG perspectives ensures continuous remote device manageability.

Documented **Data sources**: `index=endpoint` `sourcetype="igel:icg:security"` fields `event_type`, `user`, `result`, `source_ip`; `sourcetype="igel:ums:health"` for ICG connection warnings. **App/TA** (typical add-on context): Splunk Universal Forwarder monitoring ICG security log, custom scripted input for UMS health. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: endpoint; **sourcetype**: igel:icg:security. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=endpoint, sourcetype="igel:icg:security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **fail_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where failed_auth > 5 OR fail_pct > 20` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **IGEL Cloud Gateway Connection Health**): table _time, total_events, success_auth, failed_auth, fail_pct, unique_sources

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t dc(Authentication.src) as agg_value from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src span=15m | sort - agg_value
```

Understanding this CIM / accelerated SPL

**IGEL Cloud Gateway Connection Health** — The IGEL Cloud Gateway (ICG) enables remote management of IGEL devices outside the corporate network — essential for work-from-home and branch office deployments. If ICG connectivity fails, remote devices cannot receive policy updates, firmware upgrades, or administrative commands, creating a management blind spot. Monitoring ICG health from both the UMS and ICG perspectives ensures continuous remote device manageability.

Documented **Data sources**: `index=endpoint` `sourcetype="igel:icg:security"` fields `event_type`, `user`, `result`, `source_ip`; `sourcetype="igel:ums:health"` for ICG connection warnings. **App/TA** (typical add-on context): Splunk Universal Forwarder monitoring ICG security log, custom scripted input for UMS health. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timechart (ICG auth success vs failure), Single value (current ICG status), Table (failed auth sources).

## SPL

```spl
index=endpoint sourcetype="igel:icg:security"
| bin _time span=15m
| stats count as total_events,
  sum(eval(if(match(event_type, "(?i)auth.*fail"), 1, 0))) as failed_auth,
  sum(eval(if(match(event_type, "(?i)auth.*success"), 1, 0))) as success_auth,
  dc(source_ip) as unique_sources by _time
| eval fail_pct=if(total_events>0, round(failed_auth/total_events*100,1), 0)
| where failed_auth > 5 OR fail_pct > 20
| table _time, total_events, success_auth, failed_auth, fail_pct, unique_sources
```

## CIM SPL

```spl
| tstats summariesonly=t dc(Authentication.src) as agg_value from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src span=15m | sort - agg_value
```

## Visualization

Timechart (ICG auth success vs failure), Single value (current ICG status), Table (failed auth sources).

## References

- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
