<!-- AUTO-GENERATED from UC-5.2.13.json — DO NOT EDIT -->

---
id: "5.2.13"
title: "Session Table Exhaustion"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.2.13 · Session Table Exhaustion

## Description

When session tables fill, new connections are dropped. This causes service outages that are difficult to diagnose without firewall telemetry.

## Value

When session tables fill, new connections are dropped. This causes service outages that are difficult to diagnose without firewall telemetry.

## Implementation

Monitor session counts via SNMP or firewall system logs. Know your platform's session limit. Alert at 80% utilization. Investigate top session consumers by source/destination.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX), SNMP.
• Ensure the following data sources are available: `sourcetype=pan:system`, `sourcetype=fgt_event`, SNMP.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor session counts via SNMP or firewall system logs. Know your platform's session limit. Alert at 80% utilization. Investigate top session consumers by source/destination.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="pan:system" "session table"
| append [search index=network sourcetype="pan:traffic" | stats dc(session_id) as active_sessions by dvc | eval max_sessions=coalesce(max_sessions,500000)]
| stats latest(active_sessions) as sessions, latest(max_sessions) as max by dvc
| eval utilization=round(sessions/max*100,1) | where utilization > 80
```

Understanding this SPL

**Session Table Exhaustion** — When session tables fill, new connections are dropped. This causes service outages that are difficult to diagnose without firewall telemetry.

Documented **Data sources**: `sourcetype=pan:system`, `sourcetype=fgt_event`, SNMP. **App/TA** (typical add-on context): `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX), SNMP. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: pan:system. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="pan:system". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Appends rows from a subsearch with `append`.
• `stats` rolls up events into metrics; results are split **by dvc** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **utilization** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where utilization > 80` — typically the threshold or rule expression for this monitoring goal.

Step 3 — Validate
Sample the same time range in your firewall management console, Panorama, FortiManager, or Check Point SmartConsole and confirm that counts, usernames, and object names line up with Splunk.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (per firewall), Line chart (session count trending), Table (top consumers).

## SPL

```spl
index=network sourcetype="pan:system" "session table"
| append [search index=network sourcetype="pan:traffic" | stats dc(session_id) as active_sessions by dvc | eval max_sessions=coalesce(max_sessions,500000)]
| stats latest(active_sessions) as sessions, latest(max_sessions) as max by dvc
| eval utilization=round(sessions/max*100,1) | where utilization > 80
```

## Visualization

Gauge (per firewall), Line chart (session count trending), Table (top consumers).

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
