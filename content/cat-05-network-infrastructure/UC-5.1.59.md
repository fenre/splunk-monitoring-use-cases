<!-- AUTO-GENERATED from UC-5.1.59.json — DO NOT EDIT -->

---
id: "5.1.59"
title: "Junos Virtual Chassis Health (Juniper)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.59 · Junos Virtual Chassis Health (Juniper)

## Description

Virtual Chassis merges multiple switches into one control plane; a member disconnect or role churn can blackhole VLANs or split forwarding across members. VCCP and member state messages are the earliest signal of stack cable, power, or software issues. Centralized monitoring reduces time to detect partial stack failures that users report as intermittent “random” connectivity loss.

## Value

Virtual Chassis merges multiple switches into one control plane; a member disconnect or role churn can blackhole VLANs or split forwarding across members. VCCP and member state messages are the earliest signal of stack cable, power, or software issues. Centralized monitoring reduces time to detect partial stack failures that users report as intermittent “random” connectivity loss.

## Implementation

Baseline normal VCCP chatter; alert on member disconnect, not-primary transitions, or split-brain indicators per Juniper KB wording in your release. Correlate with interface errors on VCP ports. Map `host` to stack ID in a lookup for faster operator response.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_juniper`, syslog.
• Ensure the following data sources are available: `sourcetype=juniper:junos:structured`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Baseline normal VCCP chatter; alert on member disconnect, not-primary transitions, or split-brain indicators per Juniper KB wording in your release. Correlate with interface errors on VCP ports. Map `host` to stack ID in a lookup for faster operator response.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="juniper:junos:structured"
| search VCCPD OR "Virtual Chassis" OR "vcp-" OR "member.*state" OR "VC member"
| rex field=_raw "(?i)member\s+(?<member_id>\d+)"
| stats count as vc_events, dc(member_id) as members_seen, latest(_raw) as last_event by host
| sort -vc_events
```

Understanding this SPL

**Junos Virtual Chassis Health (Juniper)** — Virtual Chassis merges multiple switches into one control plane; a member disconnect or role churn can blackhole VLANs or split forwarding across members. VCCP and member state messages are the earliest signal of stack cable, power, or software issues. Centralized monitoring reduces time to detect partial stack failures that users report as intermittent “random” connectivity loss.

Documented **Data sources**: `sourcetype=juniper:junos:structured`. **App/TA** (typical add-on context): `Splunk_TA_juniper`, syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: juniper:junos:structured. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="juniper:junos:structured". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Extracts fields with `rex` (regular expression).
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
SSH to the device and run `show chassis alarms`, `show chassis routing-engine`, or `show virtual-chassis` as appropriate, and check that the same FRU, member, or RE state appears in syslog timestamps around your Splunk hit.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: VC member status matrix; event timeline for stack role changes; table of stacks with elevated event rate.

## SPL

```spl
index=network sourcetype="juniper:junos:structured"
| search VCCPD OR "Virtual Chassis" OR "vcp-" OR "member.*state" OR "VC member"
| rex field=_raw "(?i)member\s+(?<member_id>\d+)"
| stats count as vc_events, dc(member_id) as members_seen, latest(_raw) as last_event by host
| sort -vc_events
```

## Visualization

VC member status matrix; event timeline for stack role changes; table of stacks with elevated event rate.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
