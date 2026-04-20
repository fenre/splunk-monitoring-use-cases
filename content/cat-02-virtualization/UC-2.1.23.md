---
id: "2.1.23"
title: "VM Unexpected Power State Changes"
criticality: "critical"
splunkPillar: "Security"
---

# UC-2.1.23 · VM Unexpected Power State Changes

## Description

Unexpected VM shutdowns or resets indicate guest OS crashes, resource exhaustion, or unauthorized actions. Unlike planned maintenance, unplanned power state changes disrupt services without warning. Correlating with the initiating user distinguishes admin actions from automated or malicious changes.

## Value

Unexpected VM shutdowns or resets indicate guest OS crashes, resource exhaustion, or unauthorized actions. Unlike planned maintenance, unplanned power state changes disrupt services without warning. Correlating with the initiating user distinguishes admin actions from automated or malicious changes.

## Implementation

Collect vCenter events via Splunk_TA_vmware. Maintain a lookup of authorized service accounts and scheduled maintenance windows. Alert on any power-off or reset outside of maintenance windows or by non-authorized users. Cross-reference with guest OS event logs for crash evidence.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`.
• Ensure the following data sources are available: `sourcetype=vmware:events`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect vCenter events via Splunk_TA_vmware. Maintain a lookup of authorized service accounts and scheduled maintenance windows. Alert on any power-off or reset outside of maintenance windows or by non-authorized users. Cross-reference with guest OS event logs for crash evidence.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:events" (event_type="VmPoweredOffEvent" OR event_type="VmResettingEvent" OR event_type="VmGuestShutdownEvent" OR event_type="VmGuestRebootEvent")
| eval planned=if(match(user, "^(admin|svc_|scheduled)"), "Planned", "Unplanned")
| where planned="Unplanned"
| table _time, vm_name, host, event_type, user, message
| sort -_time
```

Understanding this SPL

**VM Unexpected Power State Changes** — Unexpected VM shutdowns or resets indicate guest OS crashes, resource exhaustion, or unauthorized actions. Unlike planned maintenance, unplanned power state changes disrupt services without warning. Correlating with the initiating user distinguishes admin actions from automated or malicious changes.

Documented **Data sources**: `sourcetype=vmware:events`. **App/TA** (typical add-on context): `Splunk_TA_vmware`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:events. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **planned** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where planned="Unplanned"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **VM Unexpected Power State Changes**): table _time, vm_name, host, event_type, user, message
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object_category, All_Changes.user | sort - count
```

Understanding this CIM / accelerated SPL

**VM Unexpected Power State Changes** — Unexpected VM shutdowns or resets indicate guest OS crashes, resource exhaustion, or unauthorized actions. Unlike planned maintenance, unplanned power state changes disrupt services without warning. Correlating with the initiating user distinguishes admin actions from automated or malicious changes.

Documented **Data sources**: `sourcetype=vmware:events`. **App/TA** (typical add-on context): `Splunk_TA_vmware`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (power events), Table (unplanned shutdowns), Bar chart (by VM and user).

## SPL

```spl
index=vmware sourcetype="vmware:events" (event_type="VmPoweredOffEvent" OR event_type="VmResettingEvent" OR event_type="VmGuestShutdownEvent" OR event_type="VmGuestRebootEvent")
| eval planned=if(match(user, "^(admin|svc_|scheduled)"), "Planned", "Unplanned")
| where planned="Unplanned"
| table _time, vm_name, host, event_type, user, message
| sort -_time
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object_category, All_Changes.user | sort - count
```

## Visualization

Timeline (power events), Table (unplanned shutdowns), Bar chart (by VM and user).

## References

- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
