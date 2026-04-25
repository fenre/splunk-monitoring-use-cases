<!-- AUTO-GENERATED from UC-2.1.21.json — DO NOT EDIT -->

---
id: "2.1.21"
title: "ESXi Host Unexpected Reboot Detection"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-2.1.21 · ESXi Host Unexpected Reboot Detection

## Description

Unexpected ESXi reboots indicate hardware failure (memory ECC errors, CPU machine checks), kernel panics (PSODs), or firmware bugs. Each reboot triggers HA failover of all VMs on that host, causing widespread service disruption. Early detection enables root cause analysis before the issue recurs.

## Value

Unexpected ESXi reboots indicate hardware failure (memory ECC errors, CPU machine checks), kernel panics (PSODs), or firmware bugs. Each reboot triggers HA failover of all VMs on that host, causing widespread service disruption. Early detection enables root cause analysis before the issue recurs.

## Implementation

Collect vCenter events via Splunk_TA_vmware. Also forward ESXi syslog directly to Splunk for boot-time messages. Alert immediately on HostConnectionLostEvent (ungraceful). Correlate with IPMI/iLO/iDRAC logs if available. Differentiate planned reboots (HostShutdownEvent with a user) from unplanned (HostConnectionLostEvent).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`.
• Ensure the following data sources are available: `sourcetype=vmware:events`, ESXi syslog.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect vCenter events via Splunk_TA_vmware. Also forward ESXi syslog directly to Splunk for boot-time messages. Alert immediately on HostConnectionLostEvent (ungraceful). Correlate with IPMI/iLO/iDRAC logs if available. Differentiate planned reboots (HostShutdownEvent with a user) from unplanned (HostConnectionLostEvent).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:events" (event_type="HostConnectionLostEvent" OR event_type="HostDisconnectedEvent" OR event_type="HostShutdownEvent")
| table _time, host, event_type, message, user
| sort -_time
```

Understanding this SPL

**ESXi Host Unexpected Reboot Detection** — Unexpected ESXi reboots indicate hardware failure (memory ECC errors, CPU machine checks), kernel panics (PSODs), or firmware bugs. Each reboot triggers HA failover of all VMs on that host, causing widespread service disruption. Early detection enables root cause analysis before the issue recurs.

Documented **Data sources**: `sourcetype=vmware:events`, ESXi syslog. **App/TA** (typical add-on context): `Splunk_TA_vmware`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:events. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **ESXi Host Unexpected Reboot Detection**): table _time, host, event_type, message, user
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (host events), Status grid (host connectivity), Alert panel (critical).

## SPL

```spl
index=vmware sourcetype="vmware:events" (event_type="HostConnectionLostEvent" OR event_type="HostDisconnectedEvent" OR event_type="HostShutdownEvent")
| table _time, host, event_type, message, user
| sort -_time
```

## Visualization

Timeline (host events), Status grid (host connectivity), Alert panel (critical).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
