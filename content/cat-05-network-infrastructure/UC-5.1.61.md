---
id: "5.1.61"
title: "Arista EOS Agent Health Monitoring (Arista)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.61 · Arista EOS Agent Health Monitoring (Arista)

## Description

EOS features run as processes under ProcMgr; unexpected agent restarts often precede control-plane instability, STP or routing anomalies, or memory pressure. Tracking restart frequency by agent name ties platform symptoms to a specific subsystem instead of generic “switch is slow” tickets. Trending restarts after code upgrades also validates stability before promoting images fleet-wide.

## Value

EOS features run as processes under ProcMgr; unexpected agent restarts often precede control-plane instability, STP or routing anomalies, or memory pressure. Tracking restart frequency by agent name ties platform symptoms to a specific subsystem instead of generic “switch is slow” tickets. Trending restarts after code upgrades also validates stability before promoting images fleet-wide.

## Implementation

Create a baseline of allowed occasional restarts per major version; alert when any host exceeds threshold per day or when critical agents (e.g., Stp, Bgp, Route) restart. Attach EOS version from inventory. Open problem ticket when restarts cluster after a specific feature toggle.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `arista:eos` via SC4S, syslog.
• Ensure the following data sources are available: `sourcetype=arista:eos`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a baseline of allowed occasional restarts per major version; alert when any host exceeds threshold per day or when critical agents (e.g., Stp, Bgp, Route) restart. Attach EOS version from inventory. Open problem ticket when restarts cluster after a specific feature toggle.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="arista:eos"
| search ProcMgr OR "ProcMgr-worker" OR "Agent.*restart" OR "restarted" OR "%AGENT-"
| rex field=_raw "(?i)(?<agent_name>[A-Za-z0-9_\-]+)\s+agent.*restart"
| stats count as restarts, values(agent_name) as agents by host
| where restarts > 0
| sort -restarts
```

Understanding this SPL

**Arista EOS Agent Health Monitoring (Arista)** — EOS features run as processes under ProcMgr; unexpected agent restarts often precede control-plane instability, STP or routing anomalies, or memory pressure. Tracking restart frequency by agent name ties platform symptoms to a specific subsystem instead of generic “switch is slow” tickets. Trending restarts after code upgrades also validates stability before promoting images fleet-wide.

Documented **Data sources**: `sourcetype=arista:eos`. **App/TA** (typical add-on context): `arista:eos` via SC4S, syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: arista:eos. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="arista:eos". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Extracts fields with `rex` (regular expression).
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where restarts > 0` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of hosts with agent restart counts; bar chart by agent name; sparkline of restarts over time.

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

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
