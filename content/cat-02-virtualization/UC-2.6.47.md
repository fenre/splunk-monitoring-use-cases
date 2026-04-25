<!-- AUTO-GENERATED from UC-2.6.47.json — DO NOT EDIT -->

---
id: "2.6.47"
title: "Workspace App Client Version Distribution"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.6.47 · Workspace App Client Version Distribution

## Description

Citrix Workspace app versions and platforms drift quickly — users defer upgrades, some branches are blocked by legacy tools, and mobile platforms patch on different cadences. A wide long tail of old clients increases your support cost, security exposure, and feature inconsistency. Reporting client version share by platform (Windows, Mac, Linux, iOS, Android) supports compliance with internal standards, tells you which upgrade campaigns worked, and highlights obsolete builds that should be blocked at the gateway. This is not a one-time audit; you want scheduled visibility after every gateway or StoreFront change.

## Value

Citrix Workspace app versions and platforms drift quickly — users defer upgrades, some branches are blocked by legacy tools, and mobile platforms patch on different cadences. A wide long tail of old clients increases your support cost, security exposure, and feature inconsistency. Reporting client version share by platform (Windows, Mac, Linux, iOS, Android) supports compliance with internal standards, tells you which upgrade campaigns worked, and highlights obsolete builds that should be blocked at the gateway. This is not a one-time audit; you want scheduled visibility after every gateway or StoreFront change.

## Implementation

Ensure client version fields are present on at least one reliable event (often session start from broker or a Monitor OData `Sessions` backfill). Build a `lookup` of approved `client_version` per platform. Schedule a weekly or daily report, not an alert, unless a version is explicitly banned — then alert when `pct` for that version is nonzero. For executive views, show stacked percentage bars by platform. Feed the data into your software-asset and endpoint-management teams for package targeting.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Template for Citrix XenDesktop 7 (`TA-XD7-Broker`); optional Citrix Monitor OData for richer session details.
• Ensure the following data sources are available: broker events with client metadata; or OData `Sessions` with client version and device details.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Verify field names with `| fieldsummary` in a 24-hour window. If only opaque build numbers arrive, add a `lookup` to friendly names. Deduplicate multiple events per logon to avoid double counting with `| dedup` on session and day where appropriate for reporting, but not for per-connection analytics.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report; adjust `event_type` list):

```spl
index=xd sourcetype="citrix:broker:events" (event_type="SessionConnection" OR event_type="ConnectionLogon")
| eval cv=coalesce(client_version, ClientVersion, "unknown")
| eval platform=coalesce(client_platform, client_os, "unknown")
| where cv!="unknown"
| stats count as sessions, dc(user) as users by cv, platform
| eventstats sum(sessions) as total_sessions
| eval pct=round(100 * sessions / total_sessions, 2)
| sort - sessions
| table cv, platform, users, sessions, pct
```

**Workspace App Client Version Distribution** — Add `| inputlookup approved_workspace_clients` and `| where isnull(approved)` to flag rows that breach policy, if you maintain such a list.

Step 3 — Validate
Check totals against a Citrix Director session export for a test day. Differences often come from unauthenticated or prelogon events — exclude those with a filter on event type if needed.

Step 4 — Operationalize
Publish the report to a portal, attach it to change windows for client upgrades, and re-run after any VPN or gateway change that alters the client path.

## SPL

```spl
index=xd sourcetype="citrix:broker:events" (event_type="SessionConnection" OR event_type="ConnectionLogon" OR event_type="SessionInfo")
| eval cv=coalesce(client_version, ClientVersion, workspace_version, "unknown")
| eval platform=coalesce(client_platform, os_type, client_os, "unknown")
| where cv!="unknown"
| stats count as sessions, dc(user) as users, dc(host) as hosts by cv, platform
| eventstats sum(sessions) as total_sessions
| eval pct=round(100 * sessions / total_sessions, 2)
| sort - sessions
| table cv, platform, users, sessions, pct
```

## Visualization

Pie or treemap of versions, stacked bar by platform, table of versions with percent of sessions, optional single value for count of unapproved clients via lookup match.

## References

- [Citrix Workspace app lifecycle matrix](https://docs.citrix.com/en-us/citrix-workspace-app-for-windows/whats-new.html)
- [Session data from Monitor (context)](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/monitor-service.html)
