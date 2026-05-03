<!-- AUTO-GENERATED from UC-5.9.22.json — DO NOT EDIT -->

---
id: "5.9.22"
title: "Local Agent Issue Monitoring"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.9.22 · Local Agent Issue Monitoring

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We check that all our network monitoring sensors are actually working, because a broken sensor means a blind spot — we won't get any warnings when the network in that area has problems.*

---

## Description

Monitors the health of ThousandEyes Enterprise Agents themselves — detecting when agents lose connectivity, experience software issues, or encounter local network problems at their deployment site. This is a critical operational health check: if an agent is down, ALL tests assigned to it stop producing data, creating blind spots in your monitoring coverage.

## Value

A downed ThousandEyes agent is an invisible failure: no errors appear because no tests run. If you only monitor test metrics (UC-5.9.1–17), a dead agent produces no data — which looks like "nothing happening" rather than "monitoring broken." Local Agent Issue events are the only mechanism to detect this blind spot. Without monitoring agent health, you could have a critical branch office agent down for days while the NOC team assumes the network path is fine because no alerts are firing. This UC ensures you know the moment an agent goes offline, so you can fix it before the next network incident occurs — an incident you would otherwise miss entirely.

## Implementation

Uses the same Event input as UC-5.9.18. Local Agent Issue events are one of six event types fetched by the Event input. Filter by `type="Local Agent Issue"` to focus on agent health.

## Detailed Implementation

### Prerequisites
- All prerequisites from UC-5.9.18 apply — Event input configured, `event_index` macro set.
- **Enterprise Agents deployed.** This UC only applies to Enterprise Agents (customer-managed), not Cloud Agents (ThousandEyes-managed). Cloud Agent issues are handled by ThousandEyes support.

### Step 1 — Configure data collection
Same as UC-5.9.18. Local Agent Issue events are fetched alongside all other event types.

Verify:
```spl
index=thousandeyes_events type="Local Agent Issue" earliest=-30d
| stats count by severity, state
```

### Step 2 — Create the search and alert
```spl
`event_index` type="Local Agent Issue"
| stats count earliest(_time) as first_seen latest(_time) as last_seen by severity, state, thousandeyes.test.name
| eval duration_min = round((last_seen - first_seen) / 60, 0)
| sort -count
```

**Active agent issue alert:**
```spl
`event_index` type="Local Agent Issue" state="active"
| dedup thousandeyes.test.name
| table _time, severity, thousandeyes.test.name, thousandeyes.permalink
```

**Data gap detection** (complementary approach — detects agents that stopped sending data without a Local Agent Issue event):
```spl
`stream_index` earliest=-4h latest=-2h
| stats dc(thousandeyes.source.agent.name) as agents_2h_ago
| append [
  search `stream_index` earliest=-2h
  | stats dc(thousandeyes.source.agent.name) as agents_now
]
| stats values(agents_2h_ago) as before values(agents_now) as after
```
If `agents_now < agents_2h_ago`, an agent stopped reporting.

**Scheduling:** cron `*/10 * * * *`, time range `-30m to now`.

### Step 3 — Validate
(a) Check that the Event input is collecting data: `index=thousandeyes_events | stats count by type` — all event types should be present.
(b) To force an agent issue, temporarily block the Enterprise Agent's outbound connectivity to the ThousandEyes platform (ports 443 TCP) for 5 minutes, then restore. A Local Agent Issue event should appear.
(c) Cross-reference with the ThousandEyes UI: **Cloud & Enterprise Agents → Agent Status**.

### Step 4 — Operationalize
**Runbook** (owner: infrastructure / agent management team):
1. Local Agent Issue event detected. Identify the affected agent from the event details.
2. Attempt to reach the agent: SSH/console to the agent VM or check the container orchestrator (Docker/K8s).
3. Common fixes:
   - Agent VM is rebooting → wait for auto-recovery.
   - Agent VM is down → restart VM.
   - Agent container exited → `docker restart te-agent` or equivalent.
   - Local network issue → check switch port, VLAN assignment, firewall rules (agent needs outbound 443 to `*.thousandeyes.com`).
   - Agent software crash → collect logs from `/var/log/te-agent/` and file a ThousandEyes support ticket.
4. After recovery, verify tests resume producing data: `index=thousandeyes_metrics thousandeyes.source.agent.name="<agent>" earliest=-30m | stats count`.

### Step 5 — Troubleshooting
- **No Local Agent Issue events despite known agent outages** — The agent issue detection relies on the ThousandEyes platform noticing the agent's absence. If the Event API input itself is broken, no events of any type will appear. Check UC-5.9.18 troubleshooting.

- **Stale `active` events** — If a Local Agent Issue event stays `active` indefinitely even though the agent recovered, there may be a delay in the event state transitioning to `cleared`. Check the ThousandEyes UI for the actual agent status.

## SPL

```spl
`event_index` type="Local Agent Issue"
| stats count earliest(_time) as first_seen latest(_time) as last_seen by severity, state, thousandeyes.test.name
| eval duration_min = round((last_seen - first_seen) / 60, 0)
| sort -count
```

## Visualization

(1) Single value: agents with active issues (red ≥ 1). (2) Table: agent name, issue severity, state, duration. (3) Map: if agent location data is available, plot agents with issues geographically.

## Known False Positives

**Planned agent maintenance or reboots.** Restarting a VM or container hosting an Enterprise Agent triggers a Local Agent Issue event. Correlate with your change management system to suppress alerts during planned maintenance.

**Brief network blips at the agent site.** A 30-second connectivity interruption (e.g., a switch failover, Wi-Fi AP handoff) can trigger an agent issue event that resolves itself. Check if the event duration is < 5 minutes and the state transitions to `cleared`.

**Agent software updates.** The ThousandEyes agent auto-updates can cause brief connectivity interruptions. These events typically last 2–5 minutes.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes Enterprise Agent installation and troubleshooting](https://docs.thousandeyes.com/product-documentation/global-vantage-points/enterprise-agents)
