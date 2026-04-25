<!-- AUTO-GENERATED from UC-2.6.4.json — DO NOT EDIT -->

---
id: "2.6.4"
title: "VDA Machine Registration Health"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-2.6.4 · VDA Machine Registration Health

## Description

Virtual Delivery Agents must register with a Delivery Controller to receive user sessions. Unregistered VDAs are effectively offline — they cannot serve users and reduce available capacity. Mass deregistration events indicate controller failures, network issues, or VDA crashes. Monitoring the ratio of registered to total machines ensures session hosting capacity meets demand.

## Value

Virtual Delivery Agents must register with a Delivery Controller to receive user sessions. Unregistered VDAs are effectively offline — they cannot serve users and reduce available capacity. Mass deregistration events indicate controller failures, network issues, or VDA crashes. Monitoring the ratio of registered to total machines ensures session hosting capacity meets demand.

## Implementation

Poll machine status from the Broker Service or Monitor Service OData API `Machines` endpoint. Track `RegistrationState` (Registered, Unregistered, Initializing) and `FaultState` (None, FailedToStart, StuckOnBoot, Unregistered, MaxCapacity). Alert when registration percentage drops below 95% for any delivery group. Alert immediately when more than 5 machines deregister within 5 minutes (mass deregistration = infrastructure problem). Correlate with controller health and hypervisor connectivity.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Template for Citrix XenDesktop 7 (`TA-XD7-Broker`), Citrix Monitor Service OData API.
• Ensure the following data sources are available: `index=xd` `sourcetype="citrix:broker:events"` fields `machine_name`, `registration_state`, `delivery_group`, `catalog_name`, `fault_state`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll machine status from the Broker Service or Monitor Service OData API `Machines` endpoint. Track `RegistrationState` (Registered, Unregistered, Initializing) and `FaultState` (None, FailedToStart, StuckOnBoot, Unregistered, MaxCapacity). Alert when registration percentage drops below 95% for any delivery group. Alert immediately when more than 5 machines deregister within 5 minutes (mass deregistration = infrastructure problem). Correlate with controller health and hypervisor connectivity.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=xd sourcetype="citrix:broker:events" event_type="MachineStatus"
| stats latest(registration_state) as reg_state, latest(fault_state) as fault by machine_name, delivery_group
| stats count as total,
  sum(eval(if(reg_state="Registered", 1, 0))) as registered,
  sum(eval(if(reg_state="Unregistered", 1, 0))) as unregistered,
  sum(eval(if(fault!="None" AND fault!="", 1, 0))) as faulted by delivery_group
| eval reg_pct=round(registered/total*100,1)
| where reg_pct < 95 OR faulted > 0
| table delivery_group, total, registered, unregistered, faulted, reg_pct
```

Understanding this SPL

**VDA Machine Registration Health** — Virtual Delivery Agents must register with a Delivery Controller to receive user sessions. Unregistered VDAs are effectively offline — they cannot serve users and reduce available capacity. Mass deregistration events indicate controller failures, network issues, or VDA crashes. Monitoring the ratio of registered to total machines ensures session hosting capacity meets demand.

Documented **Data sources**: `index=xd` `sourcetype="citrix:broker:events"` fields `machine_name`, `registration_state`, `delivery_group`, `catalog_name`, `fault_state`. **App/TA** (typical add-on context): Template for Citrix XenDesktop 7 (`TA-XD7-Broker`), Citrix Monitor Service OData API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: xd; **sourcetype**: citrix:broker:events. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=xd, sourcetype="citrix:broker:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by machine_name, delivery_group** so each row reflects one combination of those dimensions.
• `stats` rolls up events into metrics; results are split **by delivery_group** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **reg_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where reg_pct < 95 OR faulted > 0` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **VDA Machine Registration Health**): table delivery_group, total, registered, unregistered, faulted, reg_pct

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Single value (registration % with color), Bar chart (registered vs unregistered by delivery group), Table (unregistered machines with fault state).

## SPL

```spl
index=xd sourcetype="citrix:broker:events" event_type="MachineStatus"
| stats latest(registration_state) as reg_state, latest(fault_state) as fault by machine_name, delivery_group
| stats count as total,
  sum(eval(if(reg_state="Registered", 1, 0))) as registered,
  sum(eval(if(reg_state="Unregistered", 1, 0))) as unregistered,
  sum(eval(if(fault!="None" AND fault!="", 1, 0))) as faulted by delivery_group
| eval reg_pct=round(registered/total*100,1)
| where reg_pct < 95 OR faulted > 0
| table delivery_group, total, registered, unregistered, faulted, reg_pct
```

## Visualization

Single value (registration % with color), Bar chart (registered vs unregistered by delivery group), Table (unregistered machines with fault state).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
