<!-- AUTO-GENERATED from UC-2.1.19.json — DO NOT EDIT -->

---
id: "2.1.19"
title: "Distributed vSwitch Port Health and Errors"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.1.19 · Distributed vSwitch Port Health and Errors

## Description

VDS port errors indicate VLAN misconfiguration, MTU mismatches, uplink failures, or teaming policy problems. VDS health check results (available since vSphere 5.1) detect common misconfigurations that cause intermittent connectivity issues that are extremely hard to troubleshoot from the guest OS.

## Value

VDS port errors indicate VLAN misconfiguration, MTU mismatches, uplink failures, or teaming policy problems. VDS health check results (available since vSphere 5.1) detect common misconfigurations that cause intermittent connectivity issues that are extremely hard to troubleshoot from the guest OS.

## Implementation

Enable VDS health checks in vCenter (VLAN/MTU check, Teaming/Failover check). Collect vCenter events via Splunk_TA_vmware. Alert on VmnicDisconnectedEvent (physical uplink loss), DvsPortBlockedEvent, and any health check failure. Create a network topology dashboard showing VDS → uplink → VLAN mapping.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`.
• Ensure the following data sources are available: `sourcetype=vmware:events`, VDS health check results, vCenter network events.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable VDS health checks in vCenter (VLAN/MTU check, Teaming/Failover check). Collect vCenter events via Splunk_TA_vmware. Alert on VmnicDisconnectedEvent (physical uplink loss), DvsPortBlockedEvent, and any health check failure. Create a network topology dashboard showing VDS → uplink → VLAN mapping.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:events" (event_type="*Dvs*" OR event_type="*dvPort*" OR event_type="*VmnicDisconnectedEvent*")
| stats count by event_type, host, dvs_name
| sort -count
| table event_type, host, dvs_name, count
```

Understanding this SPL

**Distributed vSwitch Port Health and Errors** — VDS port errors indicate VLAN misconfiguration, MTU mismatches, uplink failures, or teaming policy problems. VDS health check results (available since vSphere 5.1) detect common misconfigurations that cause intermittent connectivity issues that are extremely hard to troubleshoot from the guest OS.

Documented **Data sources**: `sourcetype=vmware:events`, VDS health check results, vCenter network events. **App/TA** (typical add-on context): `Splunk_TA_vmware`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:events. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by event_type, host, dvs_name** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **Distributed vSwitch Port Health and Errors**): table event_type, host, dvs_name, count

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (VDS health per host), Events table, Network topology diagram.

## SPL

```spl
index=vmware sourcetype="vmware:events" (event_type="*Dvs*" OR event_type="*dvPort*" OR event_type="*VmnicDisconnectedEvent*")
| stats count by event_type, host, dvs_name
| sort -count
| table event_type, host, dvs_name, count
```

## Visualization

Status grid (VDS health per host), Events table, Network topology diagram.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
