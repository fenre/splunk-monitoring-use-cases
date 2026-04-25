<!-- AUTO-GENERATED from UC-2.6.40.json — DO NOT EDIT -->

---
id: "2.6.40"
title: "Citrix App Layering Health and Layer Attach Status"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.6.40 · Citrix App Layering Health and Layer Attach Status

## Description

Citrix App Layering delivers OS and application layers to MCS, PVS, and elastic deployments. The elastic appliance, packaging connector, and on-VDA mount stack must all stay healthy; a failed package cache, attach timeout, or ELM/connector outage blocks user desktops at boot or sign-in. Windows Application logs on the ELM and connector roles plus VDA layer messages paint an end-to-end path from packaging through attach.

## Value

Citrix App Layering delivers OS and application layers to MCS, PVS, and elastic deployments. The elastic appliance, packaging connector, and on-VDA mount stack must all stay healthy; a failed package cache, attach timeout, or ELM/connector outage blocks user desktops at boot or sign-in. Windows Application logs on the ELM and connector roles plus VDA layer messages paint an end-to-end path from packaging through attach.

## Implementation

Classify hosts by `elm|connector|vda` using a host lookup. When ELM is Linux-only, push syslog or a JSON HEC path instead of `WinEventLog`. Track cache disk usage for packaging machines via a separate capacity UC. Deduplicate noisy retry loops with `streamstats` or by trimming `count`>100/min bursts.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for Microsoft Windows, HEC or scripted API collector for the App Layering management service as needed, optional PVS/TA inputs.
• Ensure the following data sources are available: `sourcetype="WinEventLog:Application"` on ELM/connector, `sourcetype="citrix:vda:events"`, optional `sourcetype="citrix:pvs:events"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
List every role that participates in image creation and run-time mount. Ingest with consistent time zones. If you run elastic layering with cloud connectors, add cloud connector logs. Tag `component` in `transforms.conf` at index time to simplify searching.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; expand host regex to your naming standard):

```spl
index=windows OR index=xd (sourcetype="WinEventLog:Application" OR sourcetype="citrix:vda:events" OR sourcetype="citrix:pvs:events") match(_raw, "(?i)App\s*Layer|layering|unifl|svmgr|ELM|layer (attach|mount|roll|package|not found|fail|cache)")
| eval component=if(match(host, "(?i)elm|layering|manager"), "elm", if(match(_raw, "(?i)PVS|vDisk"), "pvs", "vda"))
| where match(_raw, "(?i)fail|error|timeout|unavail|mismatch|cache.*(miss|full|corrupt)|not mounted")
| bin _time span=15m
| stats count, values(Message) as msg_sample, dc(host) as hosts, dc(user) as users by _time, component, host
| sort - count
```

Step 3 — Validate
Reboot a VDA in test and confirm no unexpected errors; inject a known bad layer removed from ELM. Confirm PVS co-paths if you stack technologies.

Step 4 — Operationalize
Run parallel with the imaging pipeline UC; route ELM hard failures to the image build team, attach failures to the VDA on-call.

## SPL

```spl
index=windows OR index=xd (sourcetype="WinEventLog:Application" OR sourcetype="citrix:vda:events" OR sourcetype="citrix:pvs:events") match(_raw, "(?i)App\s*Layer|layering|unifl|svmgr|ELM|layer (attach|mount|roll|package|not found|fail|cache)")
| eval component=if(match(host, "(?i)elm|layering|manager"), "elm", if(match(_raw, "(?i)PVS|vDisk"), "pvs", "vda"))
| where match(_raw, "(?i)fail|error|timeout|unavail|mismatch|cache.*(miss|full|corrupt)|not mounted")
| bin _time span=15m
| stats count, values(Message) as msg_sample, dc(host) as hosts, dc(user) as users by _time, component, host
| sort - count
```

## Visualization

Swimlane (ELM vs VDA issues), Table (message samples), Single value (open critical errors in 24h).

## References

- [Citrix App Layering - Monitor and troubleshoot](https://docs.citrix.com/en-us/citrix-app-layering/4/monitor/monitor.html)
