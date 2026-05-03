<!-- AUTO-GENERATED from UC-5.3.16.json — DO NOT EDIT -->

---
id: "5.3.16"
title: "Citrix ADC High Availability Failover Monitoring (NetScaler)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.3.16 · Citrix ADC High Availability Failover Monitoring (NetScaler)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We list high-availability and failover style messages so a switch of roles during maintenance does not look like a mystery in post-review.*

---

## Description

Citrix ADC deployments typically use HA pairs where a secondary appliance takes over if the primary fails. Failover events (PRIMARY → SECONDARY swap) are disruptive — active connections may be dropped, and if configuration sync was incomplete, the new primary may have a stale configuration. Monitoring failover events, sync status, and node health ensures HA is functioning correctly and that failovers are investigated promptly.

## Value

Infrastructure teams detect Citrix ADC high availability failover events, split-brain conditions, and heartbeat failures to ensure HA protection is functioning and failovers are investigated.

## Implementation

The ADC logs HA state transitions via syslog when nodes change between PRIMARY, SECONDARY, CLAIMING, and FORCE CHANGE states. Also poll the NITRO API `hanode` resource for `hacurstatus`, `hacurstate`, `hasync`, `haprop`, and `hatotpktrx`. Monitor for: any failover event (state change to PRIMARY on a formerly SECONDARY node), sync failures (`hasync` not SUCCESS — configuration mismatch between nodes), system health states (COMPLETEFAIL, PARTIALFAIL, ROUTEMONITORFAIL), and STAYSECONDARY status (forced secondary, no automatic failover possible). Alert immediately on failover events. Regularly validate sync status — a desynchronized HA pair means the secondary will come up with stale configuration after failover.

## Detailed Implementation

### Prerequisites
* Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`, Splunkbase 2770). Citrix ADC HA syslog events in `index=netscaler` with `sourcetype=citrix:netscaler:syslog`. Key fields: `ha_state` (PRIMARY/SECONDARY), `ha_cur_state`, `peer_ip`, failover event messages (EVENT_STATECHANGE).
* Citrix ADC HA pair: two nodes in active-passive. The primary handles traffic; the secondary is standby. Failover triggers: (1) health check failure (heartbeat), (2) interface failure, (3) manual force failover, (4) resource exhaustion (routing monitor triggers).

### Step 1 — - Configure data collection
Verify HA events:
```spl
index=netscaler sourcetype="citrix:netscaler:syslog" ("HA" OR "failover" OR "statechange" OR "PRIMARY" OR "SECONDARY" OR "STAYSECONDARY") earliest=-7d
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- HA failover detection:**
```spl
index=netscaler sourcetype="citrix:netscaler:syslog" ("HA" OR "failover" OR "statechange" OR "PRIMARY" OR "SECONDARY") earliest=-24h
| eval ha_event=case(match(_raw, "(?i)primary.*to.*secondary"), "DEMOTED", match(_raw, "(?i)secondary.*to.*primary"), "PROMOTED", match(_raw, "(?i)staysecondary"), "STUCK_SECONDARY", match(_raw, "(?i)force.*failover"), "FORCED_FAILOVER", match(_raw, "(?i)heartbeat.*fail|peer.*down"), "HEARTBEAT_FAILURE", match(_raw, "(?i)split.?brain"), "SPLIT_BRAIN", 1==1, null())
| where isnotnull(ha_event)
| eval severity=case(ha_event="SPLIT_BRAIN", "CRITICAL -- both nodes think they are primary", ha_event="HEARTBEAT_FAILURE", "HIGH -- HA partner unreachable", ha_event IN ("PROMOTED", "DEMOTED"), "WARNING -- failover occurred", ha_event="STUCK_SECONDARY", "WARNING -- node not promoting", 1==1, "INFO")
| stats count as events latest(_time) as last_event values(host) as nodes by ha_event, severity
| sort severity
```

### Step 3 — - Validate
(a) On ADC CLI: `show ha node` -- compare HA state (PRIMARY/SECONDARY) with Splunk.
(b) Force a failover (with change window): `force ha failover` -- verify failover events appear.
(c) Verify both nodes are reporting to Splunk.

### Step 4 — - Operationalize
Dashboard ("Citrix ADC -- HA Status"):
* Row 1 -- Single-value: "Primary node", "Secondary node", "Last failover", "HA health".
* Row 2 -- HA event history table.

Alerting:
* Critical (split-brain detected): both nodes active -- immediate intervention.
* High (heartbeat failure): HA protection lost -- failover will not work.
* Warning (failover occurred): investigate cause -- was it planned?

### Step 5 — - Troubleshooting

* **Split-brain** -- Both nodes are primary. This is the most dangerous state. Immediate action: (1) identify which node should be primary, (2) force the other to secondary: `force ha failover -f`. Root cause: usually a network failure between the HA heartbeat interfaces.

* **Frequent failovers** -- Check: (1) HA heartbeat interface link status, (2) resource monitors (route monitors, link monitors), (3) intermittent interface failures.

* **STAYSECONDARY** -- The secondary node is configured to never become primary. Check: `show ha node` for "Stay Secondary" flag. This may be intentional (during maintenance) or a configuration error.

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

## Known False Positives

Rehearsals, power work, and card swaps can make high-availability logs chatty without user-facing loss.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
