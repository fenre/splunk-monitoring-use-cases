<!-- AUTO-GENERATED from UC-2.5.10.json — DO NOT EDIT -->

---
id: "2.5.10"
title: "IGEL Device Configuration Drift Detection"
criticality: "medium"
splunkPillar: "Security"
---

# UC-2.5.10 · IGEL Device Configuration Drift Detection

## Description

IGEL UMS manages device configurations through profiles and priority profiles assigned to devices or directories. Unauthorized or unintended configuration changes — profile reassignments, priority profile overrides, or direct device settings modifications — can break VDI session configurations, disable security controls, or create inconsistent user experiences. Detecting configuration drift from the approved baseline ensures fleet standardization.

## Value

IGEL UMS manages device configurations through profiles and priority profiles assigned to devices or directories. Unauthorized or unintended configuration changes — profile reassignments, priority profile overrides, or direct device settings modifications — can break VDI session configurations, disable security controls, or create inconsistent user experiences. Detecting configuration drift from the approved baseline ensures fleet standardization.

## Implementation

The UMS security audit log records all profile assignments, priority profile updates, and device configuration modifications with the acting administrator's username. Monitor for: bulk profile reassignments (more than 10 devices in 5 minutes — could be intentional rollout or accidental), off-hours configuration changes, changes by unauthorized users, and removal of security-related profiles (e.g., syslog forwarding, USB lockdown). Maintain a lookup of approved change windows and authorized administrators. Alert on changes outside approved windows or by non-authorized users.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Universal Forwarder monitoring UMS security log files.
• Ensure the following data sources are available: `index=endpoint` `sourcetype="igel:ums:security"` fields `source_tag`, `event_type`, `user`, `target`, `detail`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
The UMS security audit log records all profile assignments, priority profile updates, and device configuration modifications with the acting administrator's username. Monitor for: bulk profile reassignments (more than 10 devices in 5 minutes — could be intentional rollout or accidental), off-hours configuration changes, changes by unauthorized users, and removal of security-related profiles (e.g., syslog forwarding, USB lockdown). Maintain a lookup of approved change windows and authorized admin…

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=endpoint sourcetype="igel:ums:security" source_tag="UMS-Webapp" OR source_tag="UMS-Server"
  (event_type="*profile*" OR event_type="*assignment*" OR event_type="*settings*" OR event_type="*configuration*")
| eval change_type=case(
    match(event_type, "(?i)priority.*profile"), "Priority Profile Change",
    match(event_type, "(?i)profile"), "Profile Change",
    match(event_type, "(?i)assign"), "Assignment Change",
    1=1, "Settings Change"
  )
| stats count as changes, dc(target) as affected_devices, values(user) as changed_by by change_type, _time
| where changes > 0
| sort -_time
| table _time, change_type, changes, affected_devices, changed_by
```

Understanding this SPL

**IGEL Device Configuration Drift Detection** — IGEL UMS manages device configurations through profiles and priority profiles assigned to devices or directories. Unauthorized or unintended configuration changes — profile reassignments, priority profile overrides, or direct device settings modifications — can break VDI session configurations, disable security controls, or create inconsistent user experiences. Detecting configuration drift from the approved baseline ensures fleet standardization.

Documented **Data sources**: `index=endpoint` `sourcetype="igel:ums:security"` fields `source_tag`, `event_type`, `user`, `target`, `detail`. **App/TA** (typical add-on context): Splunk Universal Forwarder monitoring UMS security log files. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: endpoint; **sourcetype**: igel:ums:security. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=endpoint, sourcetype="igel:ums:security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **change_type** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by change_type, _time** so each row reflects one combination of those dimensions.
• Filters the current rows with `where changes > 0` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **IGEL Device Configuration Drift Detection**): table _time, change_type, changes, affected_devices, changed_by

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object_category, All_Changes.user | sort - count
```

Understanding this CIM / accelerated SPL

**IGEL Device Configuration Drift Detection** — IGEL UMS manages device configurations through profiles and priority profiles assigned to devices or directories. Unauthorized or unintended configuration changes — profile reassignments, priority profile overrides, or direct device settings modifications — can break VDI session configurations, disable security controls, or create inconsistent user experiences. Detecting configuration drift from the approved baseline ensures fleet standardization.

Documented **Data sources**: `index=endpoint` `sourcetype="igel:ums:security"` fields `source_tag`, `event_type`, `user`, `target`, `detail`. **App/TA** (typical add-on context): Splunk Universal Forwarder monitoring UMS security log files. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (configuration changes), Bar chart (changes by type), Table (recent changes with user and target details).

## SPL

```spl
index=endpoint sourcetype="igel:ums:security" source_tag="UMS-Webapp" OR source_tag="UMS-Server"
  (event_type="*profile*" OR event_type="*assignment*" OR event_type="*settings*" OR event_type="*configuration*")
| eval change_type=case(
    match(event_type, "(?i)priority.*profile"), "Priority Profile Change",
    match(event_type, "(?i)profile"), "Profile Change",
    match(event_type, "(?i)assign"), "Assignment Change",
    1=1, "Settings Change"
  )
| stats count as changes, dc(target) as affected_devices, values(user) as changed_by by change_type, _time
| where changes > 0
| sort -_time
| table _time, change_type, changes, affected_devices, changed_by
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object_category, All_Changes.user | sort - count
```

## Visualization

Timeline (configuration changes), Bar chart (changes by type), Table (recent changes with user and target details).

## References

- [uberAgent indexer app](https://splunkbase.splunk.com/app/2998)
- [Splunkbase app 1448](https://splunkbase.splunk.com/app/1448)
- [Splunk Add-on for Microsoft Windows](https://splunkbase.splunk.com/app/742)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
