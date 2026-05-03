<!-- AUTO-GENERATED from UC-5.1.61.json — DO NOT EDIT -->

---
id: "5.1.61"
title: "Arista EOS Agent Health Monitoring (Arista)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.61 · Arista EOS Agent Health Monitoring (Arista)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We help you know early when something looks wrong with arista eos agent health monitoring so the team can act before it grows into a bigger outage.*

---

## Description

EOS features run as processes under ProcMgr; unexpected agent restarts often precede control-plane instability, STP or routing anomalies, or memory pressure. Tracking restart frequency by agent name ties platform symptoms to a specific subsystem instead of generic “switch is slow” tickets. Trending restarts after code upgrades also validates stability before promoting images fleet-wide.

## Value

Operations teams monitor Arista EOS agent health across all protocol agents, detecting agent crashes and restarts that indicate software bugs requiring TAC investigation and firmware upgrades.

## Implementation

Create a baseline of allowed occasional restarts per major version; alert when any host exceeds threshold per day or when critical agents (e.g., Stp, Bgp, Route) restart. Attach EOS version from inventory. Open problem ticket when restarts cluster after a specific feature toggle.

## Detailed Implementation

### Prerequisites
* Arista EOS agent health data from syslog or eAPI. Data in `index=arista` or `index=network` with `sourcetype=arista:eos`. Key syslog: `AGENT-5-*`, `%AGENT-6-INITIALIZED`, `%AGENT-3-CRASHED`. eAPI: `show agent`.
* Arista EOS agents: modular software architecture where each protocol/feature runs as an independent agent (Stp, Rib, Bgp, Ospf, Mlag, Acl, etc.). Agent crash or restart indicates software issue. Agent health is critical for switch functionality.

### Step 1 — - Configure data collection
```
# Arista EOS -- agent logging is enabled by default
logging host <splunk-ip>
logging trap informational
```
Verify:
```spl
index=arista earliest=-30d
| where match(_raw, "(?i)AGENT|agent.*crash|agent.*restart|agent.*init|agent.*term")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- EOS agent health monitoring:**
```spl
index=arista earliest=-30d
| where match(_raw, "(?i)AGENT|agent.*crash|agent.*restart|agent.*init|agent.*term|agent.*fail")
| eval device=coalesce(host, device_name)
| rex field=_raw "(?i)Agent\s+'?(?<agent_name>[A-Za-z]+)'?"
| eval agent=coalesce(agent_name, "unknown")
| eval agent_event=case(
    match(_raw, "(?i)crash|core|abort|segfault"), "CRASH",
    match(_raw, "(?i)restart|recover"), "RESTART",
    match(_raw, "(?i)init|start"), "INITIALIZED",
    match(_raw, "(?i)term|stop|exit"), "TERMINATED",
    1==1, "AGENT_EVENT")
| eval is_critical_agent=if(match(agent, "(?i)Stp|Rib|Bgp|Ospf|Mlag|Intf|Fib|Acl|Arp"), "YES", "NO")
| stats count as events count(eval(agent_event="CRASH")) as crashes count(eval(agent_event="RESTART")) as restarts values(agent) as affected_agents by device
| eval severity=case(
    crashes > 0, "CRITICAL -- agent crash: ".mvjoin(affected_agents, ", "),
    restarts > 3, "WARNING -- frequent agent restarts",
    1==1, "OK")
| where severity != "OK"
| sort severity
```

### Step 3 — - Validate
(a) CLI: `show agent` -- list all agents and their status.
(b) CLI: `show agent <name> logs` -- agent-specific log.
(c) CLI: `dir /var/core/` -- check for crash core files.

### Step 4 — - Operationalize
Dashboard ("Arista -- Agent Health"):
* Row 1 -- Single-value: "Agent crashes (30d)", "Agent restarts", "Devices affected".
* Row 2 -- Agent crash/restart timeline.

Alert: Critical (agent crash): collect core file, open Arista TAC case.

### Step 5 — - Troubleshooting

* **Agent crash** -- Collect core file: `dir /var/core/`. Open TAC case with core file and `show tech-support`. Consider upgrading EOS to a release with the bug fix.

* **Frequent agent restarts** -- May indicate memory leak or resource exhaustion. Monitor: `show processes top` for memory usage trends. Check EOS release notes for known issues.

* **Critical agent down** -- Stp, Rib, or Bgp agent failure affects forwarding. If not auto-recovered, try: `agent <name> restart`. Plan maintenance window for firmware upgrade.

## SPL

```spl
index=network sourcetype="arista:eos"
| search ProcMgr OR "ProcMgr-worker" OR "Agent.*restart" OR "restarted" OR "%AGENT-"
| rex field=_raw "(?i)(?<agent_name>[A-Za-z0-9_\-]+)\s+agent.*restart"
| stats count as restarts, values(agent_name) as agents by host
| where restarts > 0
| sort -restarts
```

## Visualization

Table of hosts with agent restart counts; bar chart by agent name; sparkline of restarts over time.

## Known False Positives

API rate limits, CVaaS maintenance, and collector restarts can look like an agent problem—check CloudVision and device reachability first.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
