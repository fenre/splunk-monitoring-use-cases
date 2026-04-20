---
id: "5.1.64"
title: "Aruba CX VSX Redundancy Monitoring (HPE Aruba)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.1.64 · Aruba CX VSX Redundancy Monitoring (HPE Aruba)

## Description

VSX pairs use an inter-switch link and keepalive; if both fail, split-brain can leave two active primaries forwarding independently, risking loops, duplicate MACs, and hard-to-diagnose application errors. Monitoring ISL, keepalive, and synchronization state is essential for data center and campus cores where VSX fronts servers or downstream stacks. Splunk lets you alert before both control and data paths degrade past recovery.

## Value

VSX pairs use an inter-switch link and keepalive; if both fail, split-brain can leave two active primaries forwarding independently, risking loops, duplicate MACs, and hard-to-diagnose application errors. Monitoring ISL, keepalive, and synchronization state is essential for data center and campus cores where VSX fronts servers or downstream stacks. Splunk lets you alert before both control and data paths degrade past recovery.

## Implementation

Prefer synchronized clocks on VSX peers. Critical alert on keepalive loss, ISL down, or explicit split-brain / dual-primary messages. For SNMP, forward traps to Splunk and map OID to human-readable VSX state in `transforms.conf`. Correlate both peers’ logs into one notable event using a lookup of VSX pairs.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: HPE Aruba CX syslog, SNMP.
• Ensure the following data sources are available: Aruba CX syslog; SNMP traps (VSX / link state) if forwarded to Splunk.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Prefer synchronized clocks on VSX peers. Critical alert on keepalive loss, ISL down, or explicit split-brain / dual-primary messages. For SNMP, forward traps to Splunk and map OID to human-readable VSX state in `transforms.conf`. Correlate both peers’ logs into one notable event using a lookup of VSX pairs.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network (sourcetype=syslog OR sourcetype=snmptrapd OR sourcetype="snmp:trap")
| search "VSX" OR "Inter-Switch" OR "ISL" OR "keepalive" OR "split" OR "dual-primary" OR "InSync" OR "OutOfSync"
| rex field=_raw "(?i)VSX\s*[:,-]\s*(?<vsx_detail>[^\n]+)"
| stats count as vsx_events, latest(vsx_detail) as last_detail, latest(_raw) as sample by host
| sort -vsx_events
```

Understanding this SPL

**Aruba CX VSX Redundancy Monitoring (HPE Aruba)** — VSX pairs use an inter-switch link and keepalive; if both fail, split-brain can leave two active primaries forwarding independently, risking loops, duplicate MACs, and hard-to-diagnose application errors. Monitoring ISL, keepalive, and synchronization state is essential for data center and campus cores where VSX fronts servers or downstream stacks. Splunk lets you alert before both control and data paths degrade past recovery.

Documented **Data sources**: Aruba CX syslog; SNMP traps (VSX / link state) if forwarded to Splunk. **App/TA** (typical add-on context): HPE Aruba CX syslog, SNMP. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: syslog, snmptrapd, snmp:trap. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype=syslog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Extracts fields with `rex` (regular expression).
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: VSX pair health dashboard; ISL and keepalive status indicators; timeline of sync state changes.

## SPL

```spl
index=network (sourcetype=syslog OR sourcetype=snmptrapd OR sourcetype="snmp:trap")
| search "VSX" OR "Inter-Switch" OR "ISL" OR "keepalive" OR "split" OR "dual-primary" OR "InSync" OR "OutOfSync"
| rex field=_raw "(?i)VSX\s*[:,-]\s*(?<vsx_detail>[^\n]+)"
| stats count as vsx_events, latest(vsx_detail) as last_detail, latest(_raw) as sample by host
| sort -vsx_events
```

## Visualization

VSX pair health dashboard; ISL and keepalive status indicators; timeline of sync state changes.

## References

- [Splunkbase app 7523](https://splunkbase.splunk.com/app/7523)
- [Splunkbase app 2846](https://splunkbase.splunk.com/app/2846)
- [Splunkbase app 2847](https://splunkbase.splunk.com/app/2847)
