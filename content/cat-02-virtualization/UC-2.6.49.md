<!-- AUTO-GENERATED from UC-2.6.49.json — DO NOT EDIT -->

---
id: "2.6.49"
title: "Stuck Sessions and Ghost Session Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.6.49 · Stuck Sessions and Ghost Session Detection

## Description

Sessions that sit disconnected beyond policy, that never complete logoff, or that remain in broker state when the session host is already gone, consume user licenses, load index, and file handles; they are common precursors to ghost or orphaned sessions. Ghost sessions that survive past the machine that hosted them complicate support and can block new connections for the same user. You want detection that works off authoritative session records and time-in-state, with thresholds aligned to your group policy and Citrix session reliability settings, plus a path to session host or broker session reset actions.

## Value

Sessions that sit disconnected beyond policy, that never complete logoff, or that remain in broker state when the session host is already gone, consume user licenses, load index, and file handles; they are common precursors to ghost or orphaned sessions. Ghost sessions that survive past the machine that hosted them complicate support and can block new connections for the same user. You want detection that works off authoritative session records and time-in-state, with thresholds aligned to your group policy and Citrix session reliability settings, plus a path to session host or broker session reset actions.

## Implementation

Align `idle_sec` and disconnect timers with GPO: disconnected session limit, logoff on disconnect, and session linger. Eight hours in the example SPL is a placeholder. Join broker and Monitor OData so you can see broker versus VDA truth; mismatch flags ghosts. For automation, use a runbook with Citrix `Get-BrokerSession` and reset cmdlets, not blind reboots. Alert on a machine with many long-lived disconnected states or a single user with repeated ghosts after migrations.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `TA-XD7-Broker`; optional uberAgent; optional Citrix Monitor OData for `Sessions`.
• Ensure the following data sources are available: consistent `session_id` or `SessionUid` between feeds if you will correlate; time sync on controllers and session hosts.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Document your official disconnect and logoff policies. Extract numeric idle and duration fields. If the broker only emits strings, add `strptime` or `dur2sec` in `props`. Test that reconnect events clear prior disconnect rows in your state model; if you only have logs, use `transaction` on session key (expensive — prefer OData current state for inventory-style checks).

Step 2 — Create the search and alert
Run the following SPL in Search (replace `28800` seconds and state list with your policy):

```spl
index=xd sourcetype="citrix:broker:events" event_type="SessionState"
| eval state=coalesce(session_state, "Unknown")
| eval idle_sec=coalesce(idle_time_sec, 0)
| where state="Disconnected" AND idle_sec>28800
| stats count by machine_name, user, session_id
| where count>=1
```

**Stuck Sessions and Ghost Session Detection** — Append a second search on OData if you use it: join or `lookup` on `SessionUid` to compare to live broker inventory.

Step 3 — Validate
In a test lab, leave a long disconnect, confirm the event stream. Purposely desynchronize broker and a test VDA (carefully) to confirm ghost session signals exist before automation.

Step 4 — Operationalize
Pair alerts with a Citrix support queue. Track mean time to reset. Feed counts into a reliability KPI for monthly reviews.

## SPL

```spl
index=xd sourcetype="citrix:broker:events" (event_type="SessionState" OR event_type="SessionDisconnect" OR event_type="SessionLogoff")
| eval state=coalesce(session_state, SessionState, status, "Unknown")
| eval sess=coalesce(session_key, session_id, Uid, "unknown")
| eval user=coalesce(user, UserName, "unknown")
| eval machine=coalesce(machine_name, VDA, host, "Unknown")
| where state IN ("Disconnected", "StuckOnBroker", "PendingLogoff", "PreparingSession", "PreparingApplication")
| eval idle_sec=coalesce(idle_time_sec, disconnect_duration_sec, 0)
| where idle_sec>28800
| bin _time span=1h
| stats count as bad_sessions, values(state) as states, max(idle_sec) as max_idle_sec, dc(user) as affected_users by machine, _time
| where bad_sessions>0
| table _time, machine, bad_sessions, affected_users, max_idle_sec, states
```

## Visualization

Table of long-lived sessions, heatmap of affected machines, sparkline of ghost count over time, optional link to a Director-equivalent view.

## References

- [Session reliability and reconnection (Citrix)](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/ica-session-reliability.html)
- [Troubleshoot user issues — session disconnect](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/troubleshoot-user-issues.html)
