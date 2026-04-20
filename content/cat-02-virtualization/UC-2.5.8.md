---
id: "2.5.8"
title: "IGEL Device Unscheduled Reboot Detection"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.5.8 · IGEL Device Unscheduled Reboot Detection

## Description

Unexpected reboots on thin clients disrupt active VDI sessions, causing users to lose unsaved work and requiring re-authentication. Detecting unscheduled reboots — those not preceded by an administrator-initiated reboot command or firmware update — helps identify hardware failures, power issues, or kernel panics across the fleet before they become widespread.

## Value

Unexpected reboots on thin clients disrupt active VDI sessions, causing users to lose unsaved work and requiring re-authentication. Detecting unscheduled reboots — those not preceded by an administrator-initiated reboot command or firmware update — helps identify hardware failures, power issues, or kernel panics across the fleet before they become widespread.

## Implementation

IGEL OS kernel boot messages appear in syslog when the device starts. Cross-reference boot events against UMS security audit logs for administrator-initiated reboot commands. Boots that occur without a matching reboot command within a 10-minute window are classified as unscheduled. Alert when a single device has more than 3 unscheduled reboots in 24 hours (possible hardware failure) or when more than 5 devices at the same site reboot unexpectedly within 30 minutes (possible power event).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk syslog input (TCP/TLS) receiving IGEL OS rsyslog.
• Ensure the following data sources are available: `index=endpoint` `sourcetype="igel:os:syslog"` fields `host`, `process`, `message`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
IGEL OS kernel boot messages appear in syslog when the device starts. Cross-reference boot events against UMS security audit logs for administrator-initiated reboot commands. Boots that occur without a matching reboot command within a 10-minute window are classified as unscheduled. Alert when a single device has more than 3 unscheduled reboots in 24 hours (possible hardware failure) or when more than 5 devices at the same site reboot unexpectedly within 30 minutes (possible power event).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=endpoint sourcetype="igel:os:syslog" process="kernel" ("Linux version" OR "Booting" OR "Command line:")
| stats count as boot_events, earliest(_time) as first_boot, latest(_time) as last_boot by host
| join type=left host [search index=endpoint sourcetype="igel:ums:security" event_type="*reboot*" OR event_type="*restart*" | stats latest(_time) as scheduled_reboot by target]
| eval unscheduled=if(isnull(scheduled_reboot) OR last_boot > scheduled_reboot + 600, "Yes", "No")
| where unscheduled="Yes"
| eval last_boot_fmt=strftime(last_boot, "%Y-%m-%d %H:%M:%S")
| table host, last_boot_fmt, boot_events
| sort -boot_events
```

Understanding this SPL

**IGEL Device Unscheduled Reboot Detection** — Unexpected reboots on thin clients disrupt active VDI sessions, causing users to lose unsaved work and requiring re-authentication. Detecting unscheduled reboots — those not preceded by an administrator-initiated reboot command or firmware update — helps identify hardware failures, power issues, or kernel panics across the fleet before they become widespread.

Documented **Data sources**: `index=endpoint` `sourcetype="igel:os:syslog"` fields `host`, `process`, `message`. **App/TA** (typical add-on context): Splunk syslog input (TCP/TLS) receiving IGEL OS rsyslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: endpoint; **sourcetype**: igel:os:syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=endpoint, sourcetype="igel:os:syslog". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Joins to a subsearch with `join` — set `max=` to match cardinality and avoid silent truncation.
• `eval` defines or adjusts **unscheduled** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where unscheduled="Yes"` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **last_boot_fmt** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **IGEL Device Unscheduled Reboot Detection**): table host, last_boot_fmt, boot_events
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (devices with unscheduled reboots), Timechart (reboot events over time), Single value (unscheduled reboot count last 24h).

## SPL

```spl
index=endpoint sourcetype="igel:os:syslog" process="kernel" ("Linux version" OR "Booting" OR "Command line:")
| stats count as boot_events, earliest(_time) as first_boot, latest(_time) as last_boot by host
| join type=left host [search index=endpoint sourcetype="igel:ums:security" event_type="*reboot*" OR event_type="*restart*" | stats latest(_time) as scheduled_reboot by target]
| eval unscheduled=if(isnull(scheduled_reboot) OR last_boot > scheduled_reboot + 600, "Yes", "No")
| where unscheduled="Yes"
| eval last_boot_fmt=strftime(last_boot, "%Y-%m-%d %H:%M:%S")
| table host, last_boot_fmt, boot_events
| sort -boot_events
```

## Visualization

Table (devices with unscheduled reboots), Timechart (reboot events over time), Single value (unscheduled reboot count last 24h).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
