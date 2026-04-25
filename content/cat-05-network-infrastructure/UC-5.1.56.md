<!-- AUTO-GENERATED from UC-5.1.56.json — DO NOT EDIT -->

---
id: "5.1.56"
title: "Junos Chassis Alarm Monitoring (Juniper)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.1.56 · Junos Chassis Alarm Monitoring (Juniper)

## Description

Junos raises chassis alarms for power supply loss, fan failure, FPC or PIC offline, and temperature exceedances—conditions that often need on-site hardware work before service is fully restored. Ignoring these events lets a single failed component escalate into switch-wide thermal shutdown or loss of redundancy. A clear Splunk view of major and minor chassis alarms speeds dispatch to facilities and vendor support and shortens mean time to repair for edge and campus fabrics.

## Value

Junos raises chassis alarms for power supply loss, fan failure, FPC or PIC offline, and temperature exceedances—conditions that often need on-site hardware work before service is fully restored. Ignoring these events lets a single failed component escalate into switch-wide thermal shutdown or loss of redundancy. A clear Splunk view of major and minor chassis alarms speeds dispatch to facilities and vendor support and shortens mean time to repair for edge and campus fabrics.

## Implementation

Forward Junos structured syslog to Splunk; install `Splunk_TA_juniper` for field normalization. Tune `search` terms to your facility naming (CHASSISD, craftd). Alert on first major alarm and on minor alarms that repeat on the same FRU within 24h. Enrich with CMDB site and rack for dispatch.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_juniper`, syslog.
• Ensure the following data sources are available: `sourcetype=juniper:junos:structured`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward Junos structured syslog to Splunk; install `Splunk_TA_juniper` for field normalization. Tune `search` terms to your facility naming (CHASSISD, craftd). Alert on first major alarm and on minor alarms that repeat on the same FRU within 24h. Enrich with CMDB site and rack for dispatch.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="juniper:junos:structured"
| search CHASSISD OR "*chassis*" OR ALARM OR "*alarm*"
| search "*Major*" OR "*Minor*" OR severity=major OR severity=minor OR "class major" OR "class minor"
| rex field=_raw max_match=0 "(?i)fru\s*type:\s*(?<fru_type>[^,\n]+)"
| stats count as alarm_events, values(_raw) as sample_messages by host, fru_type
| where alarm_events > 0
| sort -alarm_events
```

Understanding this SPL

**Junos Chassis Alarm Monitoring (Juniper)** — Junos raises chassis alarms for power supply loss, fan failure, FPC or PIC offline, and temperature exceedances—conditions that often need on-site hardware work before service is fully restored. Ignoring these events lets a single failed component escalate into switch-wide thermal shutdown or loss of redundancy. A clear Splunk view of major and minor chassis alarms speeds dispatch to facilities and vendor support and shortens mean time to repair for edge and campus fabrics.

Documented **Data sources**: `sourcetype=juniper:junos:structured`. **App/TA** (typical add-on context): `Splunk_TA_juniper`, syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: juniper:junos:structured. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="juniper:junos:structured". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Applies an explicit `search` filter to narrow the current result set.
• Extracts fields with `rex` (regular expression).
• `stats` rolls up events into metrics; results are split **by host, fru_type** so each row reflects one combination of those dimensions.
• Filters the current rows with `where alarm_events > 0` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
SSH to the device and run `show chassis alarms`, `show chassis routing-engine`, or `show virtual-chassis` as appropriate, and check that the same FRU, member, or RE state appears in syslog timestamps around your Splunk hit.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Chassis alarm table by host and FRU; timeline of major vs minor; single-value panel for open major alarms.

## SPL

```spl
index=network sourcetype="juniper:junos:structured"
| search CHASSISD OR "*chassis*" OR ALARM OR "*alarm*"
| search "*Major*" OR "*Minor*" OR severity=major OR severity=minor OR "class major" OR "class minor"
| rex field=_raw max_match=0 "(?i)fru\s*type:\s*(?<fru_type>[^,\n]+)"
| stats count as alarm_events, values(_raw) as sample_messages by host, fru_type
| where alarm_events > 0
| sort -alarm_events
```

## Visualization

Chassis alarm table by host and FRU; timeline of major vs minor; single-value panel for open major alarms.

## References

- [CIM: Alerts](https://docs.splunk.com/Documentation/CIM/latest/User/Alerts)
