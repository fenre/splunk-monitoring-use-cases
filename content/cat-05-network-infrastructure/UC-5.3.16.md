---
id: "5.3.16"
title: "Citrix ADC High Availability Failover Monitoring (NetScaler)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.3.16 · Citrix ADC High Availability Failover Monitoring (NetScaler)

## Description

Citrix ADC deployments typically use HA pairs where a secondary appliance takes over if the primary fails. Failover events (PRIMARY → SECONDARY swap) are disruptive — active connections may be dropped, and if configuration sync was incomplete, the new primary may have a stale configuration. Monitoring failover events, sync status, and node health ensures HA is functioning correctly and that failovers are investigated promptly.

## Value

Citrix ADC deployments typically use HA pairs where a secondary appliance takes over if the primary fails. Failover events (PRIMARY → SECONDARY swap) are disruptive — active connections may be dropped, and if configuration sync was incomplete, the new primary may have a stale configuration. Monitoring failover events, sync status, and node health ensures HA is functioning correctly and that failovers are investigated promptly.

## Implementation

The ADC logs HA state transitions via syslog when nodes change between PRIMARY, SECONDARY, CLAIMING, and FORCE CHANGE states. Also poll the NITRO API `hanode` resource for `hacurstatus`, `hacurstate`, `hasync`, `haprop`, and `hatotpktrx`. Monitor for: any failover event (state change to PRIMARY on a formerly SECONDARY node), sync failures (`hasync` not SUCCESS — configuration mismatch between nodes), system health states (COMPLETEFAIL, PARTIALFAIL, ROUTEMONITORFAIL), and STAYSECONDARY status (forced secondary, no automatic failover possible). Alert immediately on failover events. Regularly validate sync status — a desynchronized HA pair means the secondary will come up with stale configuration after failover.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`).
• Ensure the following data sources are available: `index=network` `sourcetype="citrix:netscaler:syslog"` fields `ha_state`, `ha_node`, `sync_status`, `failover_reason`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
The ADC logs HA state transitions via syslog when nodes change between PRIMARY, SECONDARY, CLAIMING, and FORCE CHANGE states. Also poll the NITRO API `hanode` resource for `hacurstatus`, `hacurstate`, `hasync`, `haprop`, and `hatotpktrx`. Monitor for: any failover event (state change to PRIMARY on a formerly SECONDARY node), sync failures (`hasync` not SUCCESS — configuration mismatch between nodes), system health states (COMPLETEFAIL, PARTIALFAIL, ROUTEMONITORFAIL), and STAYSECONDARY status (fo…

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="citrix:netscaler:syslog" ("HA state" OR "failover" OR "STAYSECONDARY" OR "CLAIMING" OR "FORCE CHANGE")
| rex "HA state of node (?<node_id>\d+) changed from (?<from_state>\w+) to (?<to_state>\w+)"
| where isnotnull(from_state)
| eval is_failover=if(to_state="PRIMARY" AND from_state="SECONDARY", "Yes", "No")
| sort -_time
| table _time, host, node_id, from_state, to_state, is_failover
```

Understanding this SPL

**Citrix ADC High Availability Failover Monitoring (NetScaler)** — Citrix ADC deployments typically use HA pairs where a secondary appliance takes over if the primary fails. Failover events (PRIMARY → SECONDARY swap) are disruptive — active connections may be dropped, and if configuration sync was incomplete, the new primary may have a stale configuration. Monitoring failover events, sync status, and node health ensures HA is functioning correctly and that failovers are investigated promptly.

Documented **Data sources**: `index=network` `sourcetype="citrix:netscaler:syslog"` fields `ha_state`, `ha_node`, `sync_status`, `failover_reason`. **App/TA** (typical add-on context): Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: citrix:netscaler:syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="citrix:netscaler:syslog". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• Filters the current rows with `where isnotnull(from_state)` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **is_failover** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **Citrix ADC High Availability Failover Monitoring (NetScaler)**): table _time, host, node_id, from_state, to_state, is_failover


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (failover events), Status grid (node x state), Table (sync status per HA pair).

## SPL

```spl
index=network sourcetype="citrix:netscaler:syslog" ("HA state" OR "failover" OR "STAYSECONDARY" OR "CLAIMING" OR "FORCE CHANGE")
| rex "HA state of node (?<node_id>\d+) changed from (?<from_state>\w+) to (?<to_state>\w+)"
| where isnotnull(from_state)
| eval is_failover=if(to_state="PRIMARY" AND from_state="SECONDARY", "Yes", "No")
| sort -_time
| table _time, host, node_id, from_state, to_state, is_failover
```

## Visualization

Timeline (failover events), Status grid (node x state), Table (sync status per HA pair).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
