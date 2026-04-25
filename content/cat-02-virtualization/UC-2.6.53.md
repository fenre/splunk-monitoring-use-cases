<!-- AUTO-GENERATED from UC-2.6.53.json — DO NOT EDIT -->

---
id: "2.6.53"
title: "Citrix Delivery Group Desktop Assignment Changes"
criticality: "medium"
splunkPillar: "Security"
---

# UC-2.6.53 · Citrix Delivery Group Desktop Assignment Changes

## Description

Desktop and machine assignments determine who can reach which host pool, including support jump boxes and high-risk clinical or trading desktops. A mistaken assignment can grant a broad security group direct access to a gold image, or remove access during an incident. You should log add/remove actions on assignments with the acting admin, delivery group, user or group principal, and machine where applicable. Day-to-day automation may drive many rows — the control is the unexpected actor, off-hours change, or assignment outside an approved list of groups, not the volume alone.

## Value

Desktop and machine assignments determine who can reach which host pool, including support jump boxes and high-risk clinical or trading desktops. A mistaken assignment can grant a broad security group direct access to a gold image, or remove access during an incident. You should log add/remove actions on assignments with the acting admin, delivery group, user or group principal, and machine where applicable. Day-to-day automation may drive many rows — the control is the unexpected actor, off-hours change, or assignment outside an approved list of groups, not the volume alone.

## Implementation

Map broker admin events into `citrix:broker:events` with stable field names. Create a `lookup` of approved automation service accounts. Alert when `actor` is not in the list and the hour is outside change windows, or when a new Active Directory group is added to a sensitive delivery group. If your broker is quiet, supplement with hourly OData `Machines` output diffed in a saved search. Feed results to the identity and access team for recertification evidence.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `TA-XD7-Broker` with admin audit events enabled; optional Citrix Monitor OData for inventory diff.
• Ensure the following data sources are available: broker or Studio audit trail events with actor and subject; time sync across controllers.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
If Event IDs or `event_type` values differ by version, normalize with `eval` and a case statement. Truncate PII in `user` if your privacy policy requires hashing — keep a reversible vault outside Splunk for investigations.

Step 2 — Create the search and alert
Tighten the `match` on `_raw` after you know your exact `Message` format. A minimal start:

```spl
index=xd sourcetype="citrix:broker:events" event_type="AdminAction" matchstr="*assignment*"
| table _time, admin_user, user, delivery_group, Message
```

**Citrix Delivery Group Desktop Assignment Changes** — Add `| join` to your `lookup approved_admins` when ready.

Step 3 — Validate
Run a test assignment in non-production, confirm a row, and backfill one week of history. Compare to Citrix Director or Studio logs.

Step 4 — Operationalize
Route unexpected rows to a security distribution list, attach to quarterly recertification, and do not page on automation noise once baselined.

## SPL

```spl
index=xd sourcetype="citrix:broker:events"
| where event_type IN ("DesktopAssignmentChange", "MachineAssignment", "EntitlementChange") OR match(_raw, "(?i)(assignment|entitlement|desktop.?.?user|user.?.?machine)")
| eval user_key=coalesce(user, UPN, sam_account, "unknown")
| eval dg=coalesce(delivery_group, desktop_group, "Unknown")
| eval machine=coalesce(machine_name, machine, "Unassigned")
| eval change=coalesce(change_type, action, event_type, "change")
| eval actor=coalesce(admin_user, Admin, "unknown")
| bin _time span=1h
| stats count as changes, values(change) as change_types, values(user_key) as users_touched, values(machine) as machines by dg, _time, actor
| where changes>0
| sort - _time
| table _time, actor, dg, change_types, users_touched, machines, changes
```

## Visualization

Timeline of changes by admin, table of the last 50 events with before/after if your feed includes it, single value of changes in last 24 h compared to 30-day average.

## References

- [Assign machines to users in CVAD](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/delivery-groups-machines.html)
- [Manage machine catalogs and delivery groups](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/manage-cds.html)
