<!-- AUTO-GENERATED from UC-2.6.48.json — DO NOT EDIT -->

---
id: "2.6.48"
title: "Published Application Inventory Drift"
criticality: "medium"
splunkPillar: "Security"
---

# UC-2.6.48 · Published Application Inventory Drift

## Description

The published application catalog and delivery group assignments define what users can launch and from where. Unplanned additions — for example, an overly broad group entitlement — expand attack surface. Silent removals can break a department. Drift is often caught only after help desk tickets. Collecting and comparing app inventory over time, including who made the last change, supports change management, recertification, and quick forensic review if suspicious publishing appears. The goal is the same as infrastructure drift detection, but for desktop and app entitlements in Citrix rather than for cloud IaaS tags alone.

## Value

The published application catalog and delivery group assignments define what users can launch and from where. Unplanned additions — for example, an overly broad group entitlement — expand attack surface. Silent removals can break a department. Drift is often caught only after help desk tickets. Collecting and comparing app inventory over time, including who made the last change, supports change management, recertification, and quick forensic review if suspicious publishing appears. The goal is the same as infrastructure drift detection, but for desktop and app entitlements in Citrix rather than for cloud IaaS tags alone.

## Implementation

If native broker `event_type` values are not present, use daily OData `Applications` and `Outputlookup` a baseline table, then `diff` the next run with a scripted or Splunk custom command. For real-time, parse admin audit entries that include the admin SID or UPN. Alert when an application appears or disappears without a linked change record in your ITSM, or when `Actor` is not a known automation account. For security, pay special care to new publish actions to all-authenticated users or to broad Active Directory groups.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `TA-XD7-Broker` and optional Citrix admin audit feeds; optional OData inventory script.
• Ensure the following data sources are available: `citrix:broker:events` with admin and inventory semantics; or periodic OData snapshots in `citrix:monitor:odata`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Decide on event-driven, snapshot-diff, or both. For OData, use a secured account and write each poll with `_time` set to poll completion. Store golden copies in a KV store or CSV in Splunk. Map admin identities consistently (UPN). Strip passwords or secrets if any appear in `Message`.

Step 2 — Create the search and alert
Run the following SPL in Search (tune `match` to your logging):

```spl
index=xd sourcetype="citrix:broker:events" (event_type="PublishedAppChange" OR event_type="AppGroupChange" OR event_type="AdminAction")
| eval app=coalesce(app_name, ApplicationName, "Unknown")
| eval actor=coalesce(admin_user, Actor, user, "unknown")
| table _time, app, actor, delivery_group, change_type, Message
```

**Published Application Inventory Drift** — Layer `| search NOT [ inputlookup change_approved_tickets | fields ticket_hash ]` if you can correlate ITSM. For baselines, replace the live search with a diff search comparing `| inputlookup` yesterday versus today on `app_id`.

Step 3 — Validate
Execute a test publish in a lab and assert an event. Compare counts to the Citrix management console. Address duplicate events if both OData and broker emit the same logical change.

Step 4 — Operationalize
Send weekly diffs to application owners, route unexpected entries to the security team, and attach evidence to recertification.

## SPL

```spl
index=xd sourcetype="citrix:broker:events"
| where event_type IN ("PublishedAppChange", "AppGroupChange", "AdminAction") OR match(_raw, "(?i)(publish|unpublish|application|delivery\s*group|entitlement)")
| eval app=coalesce(app_name, ApplicationName, published_name, "Unknown")
| eval change=coalesce(change_type, action, operation, event_type, "change")
| eval actor=coalesce(admin_user, Actor, user, "unknown")
| bin _time span=1d
| stats count as changes, values(change) as change_types, values(delivery_group) as dgs by _time, app, actor
| where changes>0
| sort - _time
| table _time, app, actor, change_types, dgs, changes
```

## Visualization

Changelog table with old versus new, timeline of app count by delivery group, single value for new apps in last 24 hours with drilldown to detail.

## References

- [Publish applications in CVAD](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/publish.html)
- [Delegating administration and role-based access](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/delegated-administration.html)
