<!-- AUTO-GENERATED from UC-2.6.43.json — DO NOT EDIT -->

---
id: "2.6.43"
title: "Citrix Site Database Connectivity from Controllers"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-2.6.43 · Citrix Site Database Connectivity from Controllers

## Description

The Citrix site database is the single source of truth for registrations, entitlements, and broker decisions. If Delivery Controllers cannot reach the site database, users experience brokering failures, registration storms, and eventual site-wide service degradation. Proactively detecting connection retries, timeout errors, and authentication failures to the data store is essential before session launch capacity collapses. Correlate controller Application log events with `citrix:broker:events` to distinguish transient network blips from persistent connectivity loss.

## Value

The Citrix site database is the single source of truth for registrations, entitlements, and broker decisions. If Delivery Controllers cannot reach the site database, users experience brokering failures, registration storms, and eventual site-wide service degradation. Proactively detecting connection retries, timeout errors, and authentication failures to the data store is essential before session launch capacity collapses. Correlate controller Application log events with `citrix:broker:events` to distinguish transient network blips from persistent connectivity loss.

## Implementation

Forward Windows Application logs from every Delivery Controller. Add field extractions or `rex` to normalize database connection error text, SQL connectivity codes, and timeout indicators. Ingest or schedule-query `index=xd` broker events to correlate. Alert when any controller reports repeated site database connection failures in a five-minute window, or when a single error pattern exceeds your baseline. Suppress during planned database maintenance using a time-bound lookup. Document escalation to the DBA and Citrix site recovery runbooks.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for Microsoft Windows; Template for Citrix XenDesktop 7 (`TA-XD7-Broker`) for `citrix:broker:events`.
• Ensure the following data sources are available: `index=windows` `sourcetype="WinEventLog:Application"` from Delivery Controllers; optional `index=xd` `sourcetype="citrix:broker:events"` for correlation.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy universal forwarders on all Delivery Controllers. Verify Citrix FMA, Broker, and configuration logging emit database connection errors to Application. Tune `props.conf` to retain multiline `Message` where needed. Enable optional `index=xd` broker feed for the same time window. Map `host` to a stable controller name for paging.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range, `rex`, and `Message` match list as your event text requires):

```spl
index=windows sourcetype="WinEventLog:Application" (source="*Citrix*" OR source="*Broker*" OR Message="*site database*" OR Message="*Site database*")
| search (Message="*connection*" OR Message="*timeout*" OR Message="*failed*" OR Message="*unavailable*") (Message="*database*" OR Message="*SQL*" OR Message="*data store*")
| bin _time span=5m
| stats count as evt_count, values(EventCode) as event_codes, values(Message) as sample_msgs by host, _time
| where evt_count > 0
| sort -_time
| table _time, host, event_codes, evt_count, sample_msgs
```

**Citrix Site Database Connectivity from Controllers** — The Citrix site database is the single source of truth for registrations, entitlements, and broker decisions. The SPL scopes controller Application logs, buckets time, and surfaces grouped failures per host. Join or append with `index=xd` broker searches if you need brokering-side confirmation.

Step 3 — Validate
Reproduce a controlled test (e.g. firewall deny to SQL) in a lab and confirm events appear. Compare counts with SQL Server error logs and load balancer health. Ensure alert triggers only on sustained or repeated errors if noise is high.

Step 4 — Operationalize
Route critical alerts to the Citrix and database on-call. Add a dashboard with five-minute error rate, top messages, and controller list. Update the runbook with RTO and verification steps (connectivity, disk, logins, failovers).

## SPL

```spl
index=windows sourcetype="WinEventLog:Application" (source="*Citrix*" OR source="*Broker*" OR Message="*site database*" OR Message="*Site database*")
| search (Message="*connection*" OR Message="*timeout*" OR Message="*failed*" OR Message="*unavailable*") (Message="*database*" OR Message="*SQL*" OR Message="*data store*")
| bin _time span=5m
| stats count as evt_count, values(EventCode) as event_codes, values(Message) as sample_msgs by host, _time
| where evt_count > 0
| sort -_time
| table _time, host, event_codes, evt_count, sample_msgs
```

## Visualization

Single value (open critical events), timechart of database-related errors by controller, table of recent error text with host, linked drilldown to broker event timeline.

## References

- [Citrix Databases — CVAD](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/databases.html)
- [uberAgent UXM (optional correlation on endpoints)](https://splunkbase.splunk.com/app/1448)
